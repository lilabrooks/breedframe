"""Fail visibly if the installed assets differ from the reviewed model identities."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from breedframe.model_identity import verify_controller  # noqa: E402

if __name__ == "__main__":
    config = json.loads((ROOT / "models/vit/config.json").read_text())
    assert len(config["id2label"]) == 120
    assert all(config["label2id"][label] == int(i) for i, label in config["id2label"].items())
    assert config["id2label"]["29"] == "curly" and config["id2label"]["113"] == "german_short"
    identity = verify_controller()
    print(
        f"Verified published 120-class mapping and pinned controller {identity['model']} ({identity['digest']})."
    )
