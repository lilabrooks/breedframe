"""Run the frozen ResNet development screen without changing the application."""

import hashlib
import itertools
import json
import os
from pathlib import Path
import tempfile
import time

from breedframe.config import ROOT
from breedframe.images import normalize_image

DIRECTORY = ROOT / "docs/evidence/classifier-screen"


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def summarize(rows, score, margin):
    groups = {}
    for row in rows:
        group = groups.setdefault(row["cohort"], dict(total=0, reports=0, correct=0, wrong=0, failures=0))
        group["total"] += 1
        if "error" in row:
            group["failures"] += 1
            continue
        eligible = row["native_top1_is_breed"] and row["top1_score"] >= score and row["margin"] >= margin
        group["reports"] += int(eligible)
        if row["cohort"] == "supported_breed":
            group["correct"] += int(eligible and row["correct"])
            group["wrong"] += int(eligible and not row["correct"])
    labeled = groups["supported_breed"]
    unsuitable = sum(v["reports"] for k, v in groups.items() if k != "supported_breed")
    return dict(
        score=score,
        margin=margin,
        cohorts=groups,
        meets_criteria=labeled["reports"] / labeled["total"] >= 0.5
        and labeled["wrong"] / max(labeled["reports"], 1) <= 0.1
        and unsuitable == 0,
    )


def main():
    target = DIRECTORY / "development-results.json"
    if target.exists():
        raise FileExistsError("Preserve the completed or failed screen; no automatic reruns.")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    import torch
    import transformers
    from PIL import Image
    from transformers import AutoImageProcessor, AutoModelForImageClassification

    protocol = json.loads((DIRECTORY / "development-protocol.json").read_text())
    manifest = json.loads((ROOT / "docs/evidence/photo-set-v2/manifest.json").read_text())
    assets = json.loads((DIRECTORY / "download.json").read_text())
    model_dir = ROOT / "models/resnet50-candidate"
    for name, info in assets["files"].items():
        assert hashlib.sha256((model_dir / name).read_bytes()).hexdigest() == info["sha256"]
    for path, digest in protocol["source_hashes"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    state = dict(
        complete=False,
        rows=[],
        controller_calls=0,
        protocol_sha256=hashlib.sha256((DIRECTORY / "development-protocol.json").read_bytes()).hexdigest(),
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        torch=torch.__version__,
        transformers=transformers.__version__,
    )
    write(target, state)
    try:
        torch.set_num_threads(4)
        started = time.monotonic()
        processor = AutoImageProcessor.from_pretrained(model_dir, local_files_only=True, use_fast=False)
        model, loading = AutoModelForImageClassification.from_pretrained(
            model_dir, local_files_only=True, use_safetensors=True, output_loading_info=True
        )
        assert not any(loading.values()), loading
        assert len(model.config.id2label) == 1000
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        model.eval().to(device)
        state.update(
            device=device,
            loading_info=loading,
            processor=processor.to_dict(),
            load_seconds=time.monotonic() - started,
        )
        with tempfile.TemporaryDirectory(prefix="breedframe-resnet-screen-") as tmp:
            for info in manifest["images"]:
                fixture = next(f for f in manifest["cases"] if info["id"] in f["photo_ids"])
                group = (
                    "supported_breed"
                    if fixture["breed_accuracy_eligible"]
                    else "non_dog"
                    if not fixture["live_dog_present"]
                    else "unsupported_breed"
                    if fixture["kind"] == "same_dog_pair"
                    else fixture["kind"]
                )
                row = dict(
                    image_id=info["id"],
                    identity_group=fixture["leakage_group"],
                    cohort=group,
                    expected_native_id=protocol["label_map"].get(fixture["classifier_label"]),
                )
                try:
                    raw = (ROOT / info["path"]).read_bytes()
                    assert hashlib.sha256(raw).hexdigest() == info["sha256"]
                    normalized, metadata = normalize_image(raw)
                    image_path = Path(tmp) / "input.png"
                    image_path.write_bytes(normalized)
                    started = time.monotonic()
                    with Image.open(image_path) as image:
                        inputs = processor(images=image.convert("RGB"), return_tensors="pt")
                    with torch.inference_mode():
                        logits = model(**{k: v.to(device) for k, v in inputs.items()}).logits.float()
                        scores = logits.softmax(-1)[0].cpu()
                    values, indices = scores.topk(5)
                    native_id = int(indices[0])
                    row.update(
                        normalized_metadata=metadata,
                        seconds=time.monotonic() - started,
                        native_top1_is_breed=native_id in protocol["reportable_native_ids"],
                        correct=native_id == row["expected_native_id"],
                        top1_score=float(values[0]),
                        margin=float(values[0] - values[1]),
                        native_scores=scores.tolist(),
                        candidates=[
                            dict(class_id=int(i), label=model.config.id2label[int(i)], score=float(s))
                            for i, s in zip(indices, values)
                        ],
                    )
                    assert len(row["native_scores"]) == 1000 and bool(torch.isfinite(scores).all())
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    state["rows"].append(row)
                    write(target, state)
                    raise
                state["rows"].append(row)
                write(target, state)
                print(info["id"], row["candidates"][0]["label"], flush=True)
        grid = [
            summarize(state["rows"], s, m)
            for s, m in itertools.product(protocol["score_grid"], protocol["margin_grid"])
        ]
        correct = sum(r["correct"] for r in state["rows"] if r["cohort"] == "supported_breed")
        state.update(
            complete=True,
            grid=grid,
            raw_correct=correct,
            labeled_photos=12,
            passes_development_screen=correct >= 8 and any(r["meets_criteria"] for r in grid),
            thresholds_selected=False,
        )
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        write(target, state)


if __name__ == "__main__":
    main()
