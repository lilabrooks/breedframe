"""Preselected paired cases; direct, rules and model policies. Never select on predictions."""

import argparse
import copy
import hashlib
import json
import platform
import time
from pathlib import Path
from statistics import mean

from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.config import ROOT, CONTROLLER, OLLAMA_URL
from breedframe.controller import Controller
from breedframe.evidence import compare
from breedframe.policies import RulesController
from breedframe.store import Store
from breedframe.model_identity import verify_controller
import httpx

MANIFEST = ROOT / "docs/evidence/photo-set-v2/manifest.json"
METHODS = ("direct", "rules", "agent")


def source_hashes():
    paths = [*sorted((ROOT / "breedframe").glob("*.py")), Path(__file__).resolve(), MANIFEST]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def summarize(rows):
    summary = {}
    for method in METHODS:
        pairs = [(row, row[method]) for row in rows if method in row]
        labeled = [(r, m) for r, m in pairs if r["breed_accuracy_eligible"]]
        reports = [(r, m) for r, m in labeled if m.get("candidates")]
        correct = sum(m["candidates"][0]["label"] == r["label"] for r, m in reports)
        summary[method] = dict(
            cases=len(pairs),
            labeled_denominator=len(labeled),
            correct_reports=correct,
            labeled_reports=len(reports),
            incorrect_labeled_reports=len(reports) - correct,
            abstentions=sum(not m.get("candidates") for _, m in pairs),
            incomplete=sum(m["status"] != "complete" for _, m in pairs),
            mean_seconds=round(mean(m["seconds"] for _, m in pairs), 3) if pairs else None,
            requests=sum(m.get("requests", 0) for _, m in pairs),
            supplied_followups=sum(m.get("supplied_followups", 0) for _, m in pairs),
            initial_photos_classified=sum(m.get("initial_photo_classified", False) for _, m in pairs),
            followup_photos_classified=sum(m.get("followup_photos_classified", 0) for _, m in pairs),
            cases_requesting_followup=sum(m.get("requests", 0) > 0 for _, m in pairs),
            unavailable_requests=sum(m.get("unavailable_requests", 0) for _, m in pairs),
            tool_errors=sum(m.get("tool_errors", 0) for _, m in pairs),
            failed_operations=sum(m["status"] == "failed" for _, m in pairs),
            controller_errors=sum(m.get("controller_errors", 0) for _, m in pairs),
            non_dog_reports=sum(not r["live_dog_present"] and bool(m.get("candidates")) for r, m in pairs),
            unsupported_breed_reports=sum(
                r["kind"] == "same_dog_pair"
                and not r["breed_accuracy_eligible"]
                and bool(m.get("candidates"))
                for r, m in pairs
            ),
            multi_dog_reports_without_selection=sum(
                r["kind"] == "multiple_dogs" and bool(m.get("candidates")) for r, m in pairs
            ),
            disagreements=sum(m.get("relation") == "disagreement" for _, m in pairs),
            labeled_first_to_final_improvements=sum(
                not m.get("initial_correct", False)
                and bool(m.get("candidates"))
                and m["candidates"][0]["label"] == r["label"]
                for r, m in labeled
            ),
            labeled_first_to_final_regressions=sum(
                m.get("initial_correct", False)
                and (not m.get("candidates") or m["candidates"][0]["label"] != r["label"])
                for r, m in labeled
            ),
        )
    return summary


def run_method(fixture, images, method, mode, classifier, store):
    started = time.monotonic()
    ids = fixture["photo_ids"]
    case = store.create((ROOT / images[ids[0]]["path"]).read_bytes())
    case["mode"] = method
    direct_results, initial_candidates = [], []
    supplied = unavailable = 0
    policy = Agent(store, RulesController() if method == "rules" else Controller(), classifier)
    for index, image_id in enumerate(ids):
        if index:
            if mode == "policy" and (method == "direct" or case["status"] != "awaiting_photo"):
                break
            if case["status"] == "incomplete":
                break  # A failure is retained; a forced second photo does not rescue a broken method.
            store.add_photo(case, (ROOT / images[image_id]["path"]).read_bytes())
            supplied += 1
        if method == "direct":
            try:
                output = classifier.classify(store.photo_path(case, case["photos"][-1]["id"]))
            except Exception as exc:
                case["status"] = "incomplete"
                case["stop_reason"] = f"{type(exc).__name__}: {exc}"
                break
            direct_results.append(dict(photo_id=case["photos"][-1]["id"], output=output))
            case["status"] = "complete"
            case["direct_results"] = copy.deepcopy(direct_results)
            store.save(case)
            if index == 0:
                initial_candidates = output["candidates"]
        else:
            policy.run(case)
            if index == 0:
                initial_candidates = copy.deepcopy((case.get("report") or {}).get("candidates", []))
    cutoff_status = case["status"]
    if method != "direct" and case["status"] == "awaiting_photo":
        unavailable = 1
        store.finish_partial(case)  # Explicit simulated user action, not an agent conclusion.
    store.save(case)
    comparison = compare(case)
    if method == "direct":
        candidates = (
            direct_results[-1]["output"]["candidates"]
            if direct_results and case["status"] == "complete"
            else []
        )
    else:
        candidates = (case.get("report") or {}).get("candidates", [])
    classified = {
        e["photo_id"] for e in case["events"] if e.get("tool") == "classify_breed" and e["status"] == "ok"
    }
    if method == "direct":
        classified = {r["photo_id"] for r in direct_results}
    return dict(
        status=case["status"],
        cutoff_status=cutoff_status,
        case_id=case["id"],
        seconds=round(time.monotonic() - started, 3),
        candidates=candidates,
        initial_candidates=initial_candidates,
        initial_correct=bool(initial_candidates)
        and initial_candidates[0]["label"] == fixture["classifier_label"],
        requests=sum(
            e.get("tool") == "request_another_photo" and e["status"] == "ok" for e in case["events"]
        ),
        supplied_followups=supplied,
        initial_photo_classified="photo-1" in classified,
        followup_photos_classified=len(classified - {"photo-1"}),
        unavailable_requests=unavailable,
        tool_errors=sum(e["kind"] == "tool" and e["status"] == "error" for e in case["events"]),
        controller_errors=sum(e["kind"] == "controller_error" for e in case["events"]),
        attempts=sum(case["attempts"].values()),
        relation=comparison["relation"],
        report=case.get("report"),
        direct_results=direct_results,
        events=case["events"],
        stop_reason=case.get("stop_reason"),
    )


def evaluate(split, mode, output):
    identity = verify_controller()
    with httpx.Client(trust_env=False, timeout=5) as client:
        runtime = client.get(OLLAMA_URL + "/api/version").json()
    manifest = json.loads(MANIFEST.read_text())
    images = {r["id"]: r for r in manifest["images"]}
    fixtures = [
        c
        for c in manifest["cases"]
        if c["split"] == split and (mode == "policy" or c["kind"] == "same_dog_pair")
    ]
    for fixture in fixtures:
        for image_id in fixture["photo_ids"]:
            row = images[image_id]
            if hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"Photo changed: {image_id}")
    frozen = source_hashes()
    result = dict(
        protocol_version=2,
        controller=CONTROLLER,
        controller_identity=identity,
        runtime=runtime,
        split=split,
        mode=mode,
        source_hashes=frozen,
        platform=platform.platform(),
        started_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        protocol="One run per method and fixed case; rotating method order. Label and source metadata never enter the controller. Policy mode supplies follow-ups only on request. Forced-pair mode supplies both photos even after completion, except after a system failure. A request beyond supplied photographs is closed by a simulated user partial-report action. All errors and abstentions remain in denominators. Warm model timing; cold warmup reported separately. No memory sampler.",
        rows=[],
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as target:
        json.dump(result, target, indent=2)
    classifier = Classifier()
    store = Store(ROOT / "data/paired-evaluation" / output.stem)
    try:
        warm_start = time.monotonic()
        classifier.classify(ROOT / "data/demo/beagle.jpg")
        warm_case = store.create((ROOT / "data/demo/beagle.jpg").read_bytes())
        Controller().choose(warm_case, 6)
        result["warmup_seconds"] = round(time.monotonic() - warm_start, 3)
        for index, fixture in enumerate(fixtures):
            row = {
                key: fixture[key]
                for key in ("id", "kind", "breed_accuracy_eligible", "live_dog_present", "leakage_group")
            }
            row["label"] = fixture["classifier_label"]
            result["rows"].append(row)
            order = METHODS[index % 3 :] + METHODS[: index % 3]
            row["method_order"] = order
            for method in order:
                method_started = time.monotonic()
                try:
                    row[method] = run_method(fixture, images, method, mode, classifier, store)
                except Exception as exc:
                    row[method] = dict(
                        status="failed",
                        candidates=[],
                        seconds=round(time.monotonic() - method_started, 3),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                result["summary"] = summarize(result["rows"])
                output.write_text(json.dumps(result, indent=2) + "\n")
                print(
                    f"{fixture['id']} / {method}: {row[method]['status']}, {row[method]['seconds']}s",
                    flush=True,
                )
        result["source_hashes_unchanged"] = source_hashes() == frozen
        result["complete"] = result["source_hashes_unchanged"]
        if not result["complete"]:
            raise RuntimeError(
                "Policy sources changed during evaluation; results are not a frozen comparison."
            )
    finally:
        classifier.close()
        output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["development", "reserved_evaluation"], required=True)
    parser.add_argument("--mode", choices=["policy", "forced_pair"], default="policy")
    parser.add_argument(
        "--output", type=Path, required=True, help="New evidence file; existing files are never overwritten."
    )
    args = parser.parse_args()
    evaluate(args.split, args.mode, args.output.resolve())
