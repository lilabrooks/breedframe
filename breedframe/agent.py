import json
import time

from .config import ACTION_BUDGET, CASE_SECONDS, CONTROLLER_TIMEOUT, MAX_PHOTOS
from .contracts import ARGUMENTS
from .images import inspect_image
from .evidence import build_report, compare, request_reasons, successful

VIEW_TEXT = {
    "well_lit_full_body": "Add a well-lit full-body photo of the same dog, with the face visible.",
    "sharp_face_and_body": "Add a sharp photo of the same dog with the face and body in focus.",
    "closer_full_body": "Move closer and include the same dog's full body and face in the frame.",
}
REASON_TEXT = {
    "low_resolution": "The image has too few pixels for a useful breed comparison.",
    "exposure": "The measured brightness suggests lost image detail.",
    "low_detail": "The pixel-detail measurement is low; a sharper view may help.",
    "ambiguous_scores": "The leading classifier scores are close or weak.",
    "insufficient_evidence": "The available measurements do not establish a reliable visual match.",
    "conflicting_views": "The recorded views disagree on the leading class.",
}


def ranking_change(case):
    return compare(case)["summary"]


class Agent:
    def __init__(self, store, controller, classifier, budget=ACTION_BUDGET, seconds=CASE_SECONDS):
        self.store, self.controller, self.classifier = store, controller, classifier
        self.budget, self.seconds = budget, seconds

    def execute(self, case, name, raw_args):
        if name not in ARGUMENTS:
            raise ValueError("Unknown tool")
        args = ARGUMENTS[name].model_validate(raw_args)
        current = case["photos"][-1]["id"]
        if name in {"inspect_image", "classify_breed", "classify_region"}:
            if args.photo_id != current:
                raise ValueError("Investigate the current photo; earlier observations remain available.")
            if any(e["photo_id"] == current for e in successful(case, name)):
                raise ValueError("Duplicate action would return identical evidence.")
            if name == "classify_region":
                path = self.store.region_path(case, current, args.region_id)
                quality = inspect_image(path)
                return dict(
                    **self.classifier.classify(path),
                    region_id=args.region_id,
                    quality_flags=quality["quality_flags"],
                    region_inspection=quality,
                )
            path = self.store.photo_path(case, current)
            return inspect_image(path) if name == "inspect_image" else self.classifier.classify(path)
        inspections = [e for e in successful(case, "inspect_image") if e["photo_id"] == current]
        if not inspections:
            raise ValueError("Inspect the current photo before requesting or finishing.")
        if case["photos"][-1].get("regions") and not any(
            e.get("tool") == "classify_region" and e["photo_id"] == current for e in case["events"]
        ):
            raise ValueError("Investigate the user-selected region before requesting or finishing.")
        if name == "request_another_photo":
            if len(case["photos"]) >= MAX_PHOTOS:
                raise ValueError(
                    "Photo limit reached. Finish with available evidence, possibly inconclusive."
                )
            if args.reason not in request_reasons(case):
                raise ValueError("That request reason is not supported, or another photo is unavailable.")
            request = dict(
                **args.model_dump(),
                evidence_ids=[e["id"] for e in successful(case)],
                message=VIEW_TEXT[args.view],
                why=REASON_TEXT[args.reason],
            )
            case["request"], case["status"] = request, "awaiting_photo"
            return request
        report = build_report(case, **args.model_dump())
        case["report"], case["status"] = report, "complete"
        case["request"] = None
        return report

    def run(self, case, cancelled=lambda: False):
        if case["status"] != "ready":
            raise ValueError("Case must have a new photo ready for investigation.")
        current = case["photos"][-1]["id"]
        case["status"] = "running"
        if getattr(self.controller, "model", None):
            case["controller"] = self.controller.model
        case.pop("stop_reason", None)
        started = time.monotonic()
        spent = sum(r["seconds"] for r in case["runs"] if r["photo_id"] == current)
        repeated = set()
        failures = 0
        self.store.save(case)
        try:
            while case["status"] == "running" and case["attempts"][current] < self.budget:
                if cancelled():
                    raise RuntimeError("Cancelled by user; completed observations retained.")
                remaining_time = self.seconds - spent - (time.monotonic() - started)
                if remaining_time <= 0:
                    raise TimeoutError("Assessment deadline reached.")
                case["attempts"][current] += 1
                self.store.save(case)
                choose_start = time.monotonic()
                try:
                    name, args, metrics = self.controller.choose(
                        case,
                        self.budget - case["attempts"][current] + 1,
                        min(CONTROLLER_TIMEOUT, remaining_time),
                    )
                except Exception as exc:
                    case["events"].append(
                        dict(
                            id=len(case["events"]) + 1,
                            kind="controller_error",
                            photo_id=current,
                            status="error",
                            output={"error": str(exc)[:500]},
                            seconds=round(time.monotonic() - choose_start, 3),
                        )
                    )
                    self.store.save(case)
                    failures += 1
                    if failures >= 2 or isinstance(exc, TimeoutError):
                        raise RuntimeError("Controller failed; usable observations retained.") from exc
                    continue
                if cancelled():
                    raise RuntimeError(
                        "Cancelled by user before tool execution; completed observations retained."
                    )
                event = dict(
                    id=len(case["events"]) + 1,
                    kind="tool",
                    tool=name,
                    input=args,
                    photo_id=current,
                    status="running",
                    output={},
                    controller_seconds=round(time.monotonic() - choose_start, 3),
                    controller=metrics,
                )
                case["events"].append(event)
                self.store.save(case)
                tool_start = time.monotonic()
                previous_timeout = self.classifier.timeout
                try:
                    key = json.dumps([name, args], sort_keys=True)
                    if key in repeated:
                        raise ValueError("Repeated unproductive action blocked.")
                    repeated.add(key)
                    remaining_time = self.seconds - spent - (time.monotonic() - started)
                    if remaining_time <= 0:
                        raise TimeoutError("Assessment deadline reached before tool execution.")
                    if name in {"classify_breed", "classify_region"}:
                        self.classifier.timeout = min(self.classifier.timeout, remaining_time)
                    event["output"] = self.execute(case, name, args)
                    event["status"] = "ok"
                except Exception as exc:
                    event["status"] = "error"
                    event["output"] = {"error": f"{type(exc).__name__}: {exc}"[:600]}
                self.classifier.timeout = previous_timeout
                event["seconds"] = round(time.monotonic() - tool_start, 3)
                if cancelled():
                    case["report"] = None
                    case["request"] = None
                    raise RuntimeError("Cancelled by user; completed observations retained.")
                self.store.save(case)
            if case["status"] == "running":
                case["status"] = "incomplete"
                case["stop_reason"] = "Action budget exhausted; usable observations retained."
        except Exception as exc:
            case["status"] = "incomplete"
            case["stop_reason"] = str(exc)[:500]
        finally:
            case["runs"].append(
                dict(
                    photo_id=current,
                    seconds=round(time.monotonic() - started, 3),
                    attempts=case["attempts"][current],
                    status=case["status"],
                )
            )
            self.store.save(case)
        return case
