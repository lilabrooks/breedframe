"""Explicit online setup. Runtime never calls the Hub."""

from pathlib import Path
from huggingface_hub import snapshot_download

MODEL = "wesleyacheng/dog-breeds-multiclass-image-classification-with-vit"
REVISION = "160ee8611d7974c550bbaaa108378fbe8be9ef9c"
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    snapshot_download(
        MODEL,
        revision=REVISION,
        local_dir=root / "models/vit",
        allow_patterns=["config.json", "preprocessor_config.json", "model.safetensors", "README.md"],
    )
    print("Classifier downloaded at pinned revision", REVISION)
