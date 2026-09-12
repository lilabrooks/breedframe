import time
from pathlib import Path

import pytest
from PIL import Image
from breedframe.classifier import Classifier, _load_processor


@pytest.mark.parametrize("asset", ["config.json", "preprocessor_config.json", "model.safetensors"])
@pytest.mark.parametrize("empty", [False, True])
def test_missing_model_fails_without_download(tmp_path, monkeypatch, asset, empty):
    import breedframe.classifier as module

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
        (tmp_path / name).write_bytes(b"placeholder")
    if empty:
        (tmp_path / asset).write_bytes(b"")
    else:
        (tmp_path / asset).unlink()

    def unexpected_spawn(*args, **kwargs):
        pytest.fail("Missing assets must fail before multiprocessing or ML initialization.")

    monkeypatch.setattr(module.mp, "get_context", unexpected_spawn)
    classifier = Classifier(model_dir=tmp_path, timeout=0.001)
    try:
        with pytest.raises(RuntimeError, match=f"^OSError: Missing or empty classifier file:.*{asset}"):
            classifier.classify(tmp_path / "missing.png")
        assert classifier.process is None and classifier.conn is None
    finally:
        classifier.close()


def _stalled_worker(conn, model_dir, preference):
    """A real spawned process that cannot complete within the parent's deadline."""
    time.sleep(60)


def test_classifier_deadline_kills_worker(tmp_path, monkeypatch):
    import multiprocessing as mp
    import breedframe.classifier as module

    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
        (tmp_path / name).write_bytes(b"placeholder")
    monkeypatch.setattr(module, "_worker", _stalled_worker)
    existing = {child.pid for child in mp.active_children()}
    classifier = Classifier(model_dir=tmp_path, timeout=0.001)
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        classifier.classify(tmp_path / "missing.png")
    assert classifier.process is None
    assert {child.pid for child in mp.active_children()} <= existing
    assert time.monotonic() - started < 5


PROCESSOR_CONFIG = Path(__file__).parent / "fixtures" / "vit"


def test_real_processor_loads_and_normalizes_offline(monkeypatch):
    import numpy as np
    import torch

    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    processor = _load_processor(PROCESSOR_CONFIG)
    assert type(processor).__name__ == "ViTImageProcessorPil"

    # Spatial and channel variation exposes backend/resampling changes hidden by a solid colour.
    y, x = np.indices((37, 53))
    rgb = np.stack(((x * 17 + y * 31) % 256, (x * y * 7) % 256, (x * 43 + y * 11) % 256), axis=-1)
    image = Image.fromarray(rgb.astype(np.uint8))
    pixels = processor(images=image, return_tensors="pt")["pixel_values"]
    resized = np.asarray(image.resize((224, 224), resample=Image.Resampling.BILINEAR)).copy()
    expected = torch.from_numpy(resized).permute(2, 0, 1).unsqueeze(0).float()
    expected = (expected / 255.0 - 0.5) / 0.5
    assert pixels.shape == (1, 3, 224, 224)
    torch.testing.assert_close(pixels, expected, rtol=0, atol=1e-6)


@pytest.mark.parametrize("label_count", [120, 119])
def test_real_worker_with_generated_weights(tmp_path, label_count):
    """Exercise the production loader and inference without downloading trained weights."""
    import shutil
    import torch
    from transformers import ViTConfig, ViTForImageClassification

    model_dir = tmp_path / "model"
    labels = {i: f"class_{i}" for i in range(label_count)}
    rng_state = torch.random.get_rng_state().clone()
    with torch.random.fork_rng(devices=[]):
        # Seed only the CPU generator; torch.manual_seed also changes accelerator RNGs.
        torch.random.default_generator.manual_seed(0)
        model = ViTForImageClassification(
            ViTConfig(
                hidden_size=16,
                num_hidden_layers=1,
                num_attention_heads=2,
                intermediate_size=32,
                id2label=labels,
                label2id={label: i for i, label in labels.items()},
            )
        )
    assert torch.equal(torch.random.get_rng_state(), rng_state)
    # The seed makes generated weights reproducible; the fixed bias below guarantees ranking order.
    # Fixed logits cover ordinary and truncated IDs through real worker inference.
    # The separate processor test verifies sensitivity to image pixels.
    ranked_ids = [0, 29, 57, label_count - 1, 1]
    with torch.no_grad():
        model.classifier.weight.zero_()
        model.classifier.bias.zero_()
        model.classifier.bias[ranked_ids] = torch.tensor([5.0, 4.0, 3.0, 2.0, 1.0])
    model.save_pretrained(model_dir, safe_serialization=True)
    shutil.copyfile(PROCESSOR_CONFIG / "preprocessor_config.json", model_dir / "preprocessor_config.json")
    path = tmp_path / "photo.png"
    Image.new("RGB", (32, 48), "white").save(path)
    classifier = Classifier(model_dir=model_dir, device="cpu", timeout=60)
    try:
        if label_count != 120:
            with pytest.raises(RuntimeError, match="^ValueError: Classifier requires a 120-class"):
                classifier.classify(path)
            assert classifier.process is None
            return
        result = classifier.classify(path)
        process = classifier.process
        repeated = classifier.classify(path)
        assert classifier.process is process and process.is_alive()
        assert result["device"] == "cpu"
        assert result["fallback"] is None
        assert repeated["candidates"] == result["candidates"]
        candidates = result["candidates"]
        assert [item["class_id"] for item in candidates] == ranked_ids
        assert [item["unresolved_label"] for item in candidates] == [False, True, True, False, False]
        assert len(candidates) == 5
        assert len({item["class_id"] for item in candidates}) == 5
        assert all(item["label"] == labels[item["class_id"]] for item in candidates)
        scores = [item["score"] for item in candidates]
        assert all(0 <= score <= 1 for score in scores)
        assert scores == sorted(scores, reverse=True)
        assert result["margin"] == pytest.approx(scores[0] - scores[1], abs=2e-6)
    finally:
        classifier.close()
