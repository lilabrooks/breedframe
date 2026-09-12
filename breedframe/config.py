import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("BREEDFRAME_DATA", ROOT / "data/cases"))
MODEL_DIR = ROOT / "models/vit"
OLLAMA_URL = "http://127.0.0.1:11434"
CONTROLLER = os.environ.get("BREEDFRAME_CONTROLLER", "qwen3:4b")
CONTROLLER_MODELS = {
    "qwen3:4b": "359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7",
    "qwen3.5:4b": "2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd",
}
if CONTROLLER not in CONTROLLER_MODELS:
    raise ValueError("BREEDFRAME_CONTROLLER must name a reviewed, pinned local controller.")
ACTION_BUDGET = 6
MAX_PHOTOS = 3
CONTROLLER_TIMEOUT = 45
CLASSIFIER_TIMEOUT = 60
CASE_SECONDS = 240
MAX_UPLOAD = 12 * 1024 * 1024
LIMITATIONS = [
    "Likely visual breed matches only. Scores are uncalibrated model outputs, not genetic ancestry percentages.",
    "Candidates are alternative classifications across 120 known classes. This model cannot reliably reject non-dogs or unfamiliar breeds.",
    "The text-only controller cannot see coat, ears, body shape, or other visual features. It uses numerical tool observations.",
]
