"""One preselected development case for identity, payload and separate cold-memory evidence."""

import argparse
import copy
import hashlib
import json
import time
from pathlib import Path

import httpx

from breedframe.agent import Agent
from breedframe.classifier import Classifier
from breedframe.config import CONTROLLER, OLLAMA_URL, ROOT
from breedframe.controller import Controller
from breedframe.metrics import MemorySampler
from breedframe.model_identity import verify_controller
from breedframe.store import Store


class ObservedController(Controller):
    def __init__(self):
        super().__init__()
        self.requests = []

    def choose(self, *args):
        try:
            return super().choose(*args)
        finally:
            if self.last_request:
                self.requests.append(copy.deepcopy(self.last_request))


def probe(output):
    result = dict(controller=CONTROLLER, identity=verify_controller(), complete=False)
    with output.open("x") as f:
        json.dump(result, f)
    with httpx.Client(trust_env=False, timeout=15) as client:
        running = client.get(OLLAMA_URL + "/api/ps").json()["models"]
        for model in running:
            if model["name"] not in {"qwen3:4b", "qwen3.5:4b"}:
                raise ValueError("Unrelated model is loaded; do not disturb it for a comparison.")
            response = client.post(
                OLLAMA_URL + "/api/generate", json={"model": model["name"], "keep_alive": 0}
            )
            response.raise_for_status()
        result["resident_before"] = client.get(OLLAMA_URL + "/api/ps").json()
    if result["resident_before"]["models"]:
        raise RuntimeError("Controller did not unload before cold probe")
    manifest = json.loads((ROOT / "docs/evidence/photo-set-v2/manifest.json").read_text())
    fixture = next(i for i in manifest["images"] if i["id"] == "barney-01")
    raw = (ROOT / fixture["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == fixture["sha256"]
    store = Store(ROOT / "data/controller-probes" / output.stem)
    case = store.create(raw)
    controller, classifier = ObservedController(), Classifier()
    try:
        with MemorySampler(CONTROLLER) as memory:
            started = time.monotonic()
            warm_case = store.create((ROOT / "data/demo/beagle.jpg").read_bytes())
            result["startup_decision"] = controller.choose(warm_case, 6)
            classifier.classify(ROOT / "data/demo/beagle.jpg")
            result["cold_warmup_seconds"] = round(time.monotonic() - started, 3)
            Agent(store, controller, classifier).run(case)
        result.update(memory=memory.result(), case=case, requests=controller.requests)
        result["text_only"] = all(
            isinstance(m["content"], str) and not m.get("images")
            for request in controller.requests
            for m in request["messages"]
        )
        result["persisted_case_matches"] = store.load(case["id"]) == case
        result["complete"] = case["status"] in {"awaiting_photo", "complete"} and result["text_only"]
    except Exception as exc:
        result.update(error=f"{type(exc).__name__}: {exc}", case=case, requests=controller.requests)
    finally:
        classifier.close()
        output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"case", "requests"}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    probe(parser.parse_args().output)
