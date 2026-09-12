"""Real model runs on demo-only inputs; never substitutes scripted controller choices."""

import json
from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.controller import Controller
from breedframe.config import ROOT
from breedframe.store import Store

if __name__ == "__main__":
    store = Store(ROOT / "data/demo-cases")
    classifier = Classifier()
    agent = Agent(store, Controller(), classifier)
    case = store.create((ROOT / "data/demo/beagle-tiny.png").read_bytes())
    try:
        agent.run(case)
        (ROOT / "data/demo-first-v2.json").write_text(json.dumps(case, indent=2) + "\n")
        print("First photo:", case["status"], flush=True)
        if case["status"] not in {"awaiting_photo", "complete"}:
            raise SystemExit("The model run was interrupted. Actual trace retained.")
        print(
            "Follow-up supplied by demo user; requested by agent:",
            case["status"] == "awaiting_photo",
            flush=True,
        )
        store.add_photo(case, (ROOT / "data/demo/beagle.jpg").read_bytes())
        agent.run(case)
        (ROOT / "data/demo-resumed-v2.json").write_text(json.dumps(case, indent=2) + "\n")
        print("Resumed:", case["status"], "case:", case["id"], flush=True)
    finally:
        classifier.close()
