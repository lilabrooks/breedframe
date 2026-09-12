"""Check the explicit CPU fallback path on the demo image."""

import json
from breedframe.classifier import Classifier
from breedframe.config import ROOT

if __name__ == "__main__":
    classifier = Classifier(device="cpu")
    try:
        result = classifier.classify(ROOT / "data/demo/beagle.jpg")
        reference = json.loads((ROOT / "docs/evidence/first-slice.json").read_text())
        mps = next(
            e["output"]
            for e in reference["events"]
            if e.get("tool") == "classify_breed" and e["status"] == "ok"
        )
        result["same_top5_ids_as_mps"] = [x["class_id"] for x in result["candidates"]] == [
            x["class_id"] for x in mps["candidates"]
        ]
        result["max_top5_score_difference"] = max(
            abs(a["score"] - b["score"]) for a, b in zip(result["candidates"], mps["candidates"])
        )
        (ROOT / "docs/evidence/cpu-smoke.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        assert result["device"] == "cpu" and result["same_top5_ids_as_mps"]
    finally:
        classifier.close()
