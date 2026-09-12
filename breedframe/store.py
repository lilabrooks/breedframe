import json
import os
import re
import uuid
import math
import shutil
from pathlib import Path

from PIL import Image

from .config import DATA, MAX_PHOTOS, ACTION_BUDGET
from .contracts import RegionSelection
from .evidence import build_report
from .images import normalize_image


class Store:
    def __init__(self, root=DATA):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def directory(self, case_id):
        if not re.fullmatch(r"[0-9a-f]{32}", case_id):
            raise ValueError("Invalid case ID")
        return self.root / case_id

    def save(self, case):
        directory = self.directory(case["id"])
        directory.mkdir(exist_ok=True, mode=0o700)
        target = directory / "case.json"
        temp = directory / "case.tmp"
        temp.write_text(json.dumps(case, indent=2))
        temp.chmod(0o600)
        os.replace(temp, target)

    def load(self, case_id):
        return json.loads((self.directory(case_id) / "case.json").read_text())

    def create(self, raw):
        case = dict(
            id=uuid.uuid4().hex,
            status="new",
            photos=[],
            events=[],
            attempts={},
            report=None,
            request=None,
            runs=[],
            mode="agent",
            version=2,
        )
        return self.add_photo(case, raw)

    def add_photo(self, case, raw):
        if case["status"] not in {"new", "awaiting_photo", "incomplete", "complete"}:
            raise ValueError("This case is not accepting another photo.")
        if len(case["photos"]) >= MAX_PHOTOS:
            raise ValueError("This case already has three photos.")
        normalized, metadata = normalize_image(raw)
        if any(p["sha256"] == metadata["sha256"] for p in case["photos"]):
            raise ValueError("This is the same image. Add a different photo to supply new evidence.")
        photo_id = f"photo-{len(case['photos']) + 1}"
        directory = self.directory(case["id"])
        directory.mkdir(exist_ok=True, mode=0o700)
        target = directory / f"{photo_id}.png"
        target.write_bytes(normalized)
        target.chmod(0o600)
        case["photos"].append(dict(id=photo_id, **metadata))
        case["attempts"][photo_id] = 0
        case["status"] = "ready"
        case["request"] = None
        self.archive_report(case)
        case.pop("followup_unavailable", None)
        self.save(case)
        return case

    def archive_report(self, case):
        if case.get("report"):
            case.setdefault("report_history", []).append(case["report"])
        case["report"] = None

    def finish_partial(self, case):
        if case["status"] not in {"awaiting_photo", "incomplete", "complete"}:
            raise ValueError("Wait for the current operation to stop.")
        self.archive_report(case)
        case["report"] = build_report(case, completed_by="user")
        case["request"] = None
        case["followup_unavailable"] = True
        case["status"] = "complete"
        case["events"].append(
            dict(
                id=len(case["events"]) + 1,
                kind="user_action",
                status="ok",
                photo_id=case["photos"][-1]["id"],
                output={"action": "finish_partial", "reason": "No additional photo supplied."},
            )
        )
        self.save(case)
        return case

    def retry(self, case):
        if case["status"] != "incomplete":
            raise ValueError("Only interrupted cases can be retried.")
        if case["attempts"][case["photos"][-1]["id"]] >= ACTION_BUDGET:
            raise ValueError(
                "This photo's action budget is exhausted. Add a photo or finish a partial report."
            )
        case["status"] = "ready"
        case["events"].append(
            dict(
                id=len(case["events"]) + 1,
                kind="user_action",
                status="ok",
                photo_id=case["photos"][-1]["id"],
                output={"action": "retry", "budget_reset": False},
            )
        )
        self.save(case)
        return case

    def add_region(self, case, selection):
        args = RegionSelection.model_validate(selection)
        if case["status"] not in {"awaiting_photo", "complete", "incomplete"}:
            raise ValueError("Wait for the current operation to stop before selecting a region.")
        photo = case["photos"][-1]
        if args.photo_id != photo["id"] or photo.get("regions"):
            raise ValueError("Select one region on the current photo only.")
        if case["attempts"][photo["id"]] > ACTION_BUDGET - 2:
            raise ValueError("At least two actions must remain to investigate a region and finish.")
        if args.left >= args.right or args.top >= args.bottom:
            raise ValueError("Select a rectangle with positive width and height.")
        bounds = (
            math.floor(args.left * photo["width"]),
            math.floor(args.top * photo["height"]),
            math.ceil(args.right * photo["width"]),
            math.ceil(args.bottom * photo["height"]),
        )
        if bounds[2] - bounds[0] < 16 or bounds[3] - bounds[1] < 16:
            raise ValueError("Select a region at least 16 pixels wide and high.")
        if bounds == (0, 0, photo["width"], photo["height"]):
            raise ValueError("The whole photo is already available. Select a smaller region.")
        region_id = "region-1"
        path = self.directory(case["id"]) / f"{photo['id']}-{region_id}.png"
        with Image.open(self.photo_path(case, photo["id"])) as image:
            image.crop(bounds).save(path)
        path.chmod(0o600)
        region = dict(
            id=region_id,
            source="user_selection",
            parent_photo_id=photo["id"],
            bounds=list(bounds),
            normalized_bounds=[args.left, args.top, args.right, args.bottom],
        )
        photo["regions"] = [region]
        self.archive_report(case)
        case["events"].append(
            dict(
                id=len(case["events"]) + 1,
                kind="user_region",
                photo_id=photo["id"],
                status="ok",
                input=selection,
                output=region,
            )
        )
        case["status"], case["request"] = "ready", None
        self.save(case)
        return case

    def region_path(self, case, photo_id, region_id):
        photo = next((p for p in case["photos"] if p["id"] == photo_id), None)
        if not photo or not any(r["id"] == region_id for r in photo.get("regions", [])):
            raise ValueError("Unknown user-selected region.")
        return self.directory(case["id"]) / f"{photo_id}-{region_id}.png"

    def delete(self, case):
        if case["status"] in {"ready", "running"} or case.get("baseline", {}).get("status") == "running":
            raise ValueError("Stop the current operation before deleting the case.")
        shutil.rmtree(self.directory(case["id"]))

    def photo_path(self, case, photo_id):
        if photo_id not in {p["id"] for p in case["photos"]}:
            raise ValueError("Unknown photo ID")
        return self.directory(case["id"]) / f"{photo_id}.png"

    def recover(self):
        for target in self.root.glob("*/case.json"):
            case = json.loads(target.read_text())
            if case.get("baseline", {}).get("status") == "running":
                case["baseline"] = {
                    "status": "failed",
                    "error": "Application restarted during baseline inference.",
                }
                self.save(case)
            if case["status"] in {"running", "ready"}:
                for event in case["events"]:
                    if event.get("status") == "running":
                        event["status"] = "error"
                        event["output"] = {
                            "error": "Execution interrupted by application restart; result not recorded."
                        }
                case["status"] = "incomplete"
                case["stop_reason"] = (
                    "Application restarted before this assessment finished. Prior results retained."
                )
                self.save(case)
