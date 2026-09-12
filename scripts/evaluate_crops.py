"""One fixed exploratory crop pilot through the actual region pipeline."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.config import ROOT
from breedframe.evidence import compare, successful
from breedframe.policies import RulesController
from breedframe.store import Store


def run(output):
    manifest = ROOT / "docs/evidence/crop-pilot-manifest.json"
    protocol = json.loads(manifest.read_text())
    sources = [manifest, Path(__file__).resolve(), *sorted((ROOT / "breedframe").glob("*.py"))]

    def hashes():
        return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}

    result = dict(protocol=protocol, source_hashes=hashes(), rows=[], complete=False)
    with output.open("x") as stream:
        json.dump(result, stream)
    store = Store(ROOT / "data/crop-pilot-cases")
    classifier = Classifier()
    try:
        classifier.classify(ROOT / "data/demo/beagle.jpg")
        for fixture in protocol["cases"]:
            raw = (ROOT / fixture["path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != fixture["sha256"]:
                raise ValueError("Fixture hash changed")
            case = store.create(raw)
            started = time.monotonic()
            agent = Agent(store, RulesController(), classifier)
            agent.run(case)
            whole = successful(case, "classify_breed")[0]
            store.add_region(
                case,
                dict(
                    photo_id="photo-1",
                    **dict(zip(["left", "top", "right", "bottom"], fixture["bounds"], strict=True)),
                ),
            )
            agent.run(case)
            if case["status"] == "awaiting_photo":
                store.finish_partial(case)
            crops = successful(case, "classify_region")
            crop = crops[0] if crops else None
            region = case["photos"][0]["regions"][0]
            result["rows"].append(
                dict(
                    image_id=fixture["image_id"],
                    label=fixture["label"],
                    whole=whole,
                    crop=crop,
                    region=region,
                    crop_sha256=hashlib.sha256(
                        store.region_path(case, "photo-1", region["id"]).read_bytes()
                    ).hexdigest(),
                    relation=compare(case)["relation"],
                    status=case["status"],
                    report=case["report"],
                    seconds=round(time.monotonic() - started, 3),
                    events=case["events"],
                    stop_reason=case.get("stop_reason"),
                )
            )
            output.write_text(json.dumps(result, indent=2) + "\n")
            print(
                fixture["image_id"],
                whole["output"]["candidates"][0]["label"],
                crop["output"]["candidates"][0]["label"] if crop else "CROP FAILED",
                flush=True,
            )
        labeled = [r for r in result["rows"] if r["label"]]
        result["summary"] = dict(
            cases=len(result["rows"]),
            labeled_denominator=len(labeled),
            whole_correct=sum(r["whole"]["output"]["candidates"][0]["label"] == r["label"] for r in labeled),
            crop_correct=sum(
                bool(r["crop"]) and r["crop"]["output"]["candidates"][0]["label"] == r["label"]
                for r in labeled
            ),
            missing_crop_results=sum(not r["crop"] for r in result["rows"]),
            breed_reports=sum(bool(r["report"] and r["report"]["candidates"]) for r in result["rows"]),
        )
        result["complete"] = hashes() == result["source_hashes"]
    finally:
        classifier.close()
        output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
