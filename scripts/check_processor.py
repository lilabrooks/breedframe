"""Compare the offline test fixture with the processor fetched during explicit setup."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/vit/preprocessor_config.json"


def check_processor(model_dir, fixture=FIXTURE):
    actual_path = Path(model_dir) / "preprocessor_config.json"
    expected = json.loads(Path(fixture).read_text())
    actual = json.loads(actual_path.read_text())
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        raise ValueError("Processor configurations must be JSON objects.")
    if actual != expected:
        changed = sorted(
            k
            for k in actual.keys() | expected.keys()
            if k not in actual or k not in expected or actual[k] != expected[k]
        )
        raise ValueError(
            f"Processor fixture drift in {actual_path}: {', '.join(changed)}. "
            "Review the pinned model revision and tests/fixtures/vit provenance before updating the fixture."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", nargs="?", type=Path, default=ROOT / "models/vit")
    args = parser.parse_args()
    try:
        check_processor(args.model_dir)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Processor check failed: {exc}\n")
    print("Downloaded processor matches the reviewed offline test fixture.")
