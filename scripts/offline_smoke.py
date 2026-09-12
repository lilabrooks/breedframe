"""Run under scripts/offline.sb with Ollama under the same network policy."""

import json
import httpx
from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.controller import Controller
from breedframe.config import ROOT
from breedframe.metrics import MemorySampler
from breedframe.store import Store

if __name__ == "__main__":
    external_blocked = False
    try:
        with httpx.Client(timeout=3, trust_env=False) as client:
            client.get("https://huggingface.co")
    except httpx.HTTPError:
        external_blocked = True
    if not external_blocked:
        raise SystemExit("External network is available; this is not an offline verification run.")
    store = Store(ROOT / "data/offline-cases")
    classifier = Classifier()
    case = store.create((ROOT / "data/demo/beagle.jpg").read_bytes())
    try:
        with MemorySampler() as memory:
            Agent(store, Controller(), classifier).run(case)
        result = dict(
            external_network_blocked=external_blocked,
            policy="scripts/offline.sb on Ollama and this process",
            memory=memory.result(),
            case=case,
        )
        (ROOT / "docs/evidence/offline-smoke.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(dict(status=case["status"], memory=memory.result()), indent=2))
        if case["status"] != "complete":
            raise SystemExit("Offline run failed to finish")
    finally:
        classifier.close()
