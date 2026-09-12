"""Fixed development diagnostics and offline gate replay; never tune app defaults."""

import argparse
import hashlib
import io
import inspect
import itertools
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from breedframe import evidence
from breedframe.classifier import Classifier
from breedframe.config import ROOT, MODEL_DIR, CONTROLLER
from breedframe.images import normalize_image

EVIDENCE = ROOT / "docs/evidence"
MANIFEST = EVIDENCE / "photo-set-v2/manifest.json"
FILES = [
    "paired-development-v2.json",
    "paired-reserved-policy-v2.json",
    "paired-development-forced-v2.json",
    "paired-reserved-forced-v2.json",
]
PROBE_IDS = ["barney-02", "buddy-02", "cat-01"]
SCORES = [0, 0.05, 0.1, 0.15, 0.2, 0.5]
MARGINS = [0, 0.025, 0.05, 0.1, 0.15]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def cohort(fixture):
    if fixture["breed_accuracy_eligible"]:
        return "supported_breed"
    if not fixture["live_dog_present"]:
        return "non_dog"
    if fixture["kind"] == "same_dog_pair":
        return "unsupported_breed"
    return fixture["kind"]


def case_from_events(events, count):
    return {
        "photos": [{"id": f"photo-{i + 1}"} for i in range(count)],
        "events": events,
    }


def replay(manifest):
    fixtures = {f["id"]: f for f in manifest["cases"]}
    policy = [r for name in FILES[:2] for r in json.loads((EVIDENCE / name).read_text())["rows"]]
    forced = [r for name in FILES[2:] for r in json.loads((EVIDENCE / name).read_text())["rows"]]
    scenarios = {
        name: []
        for name in [
            "individual_photos",
            "initial_photos",
            "paired_evidence",
            "recorded_agent_policy",
            "recorded_agent_forced",
        ]
    }
    observations = []
    for row in policy:
        f = fixtures[row["id"]]
        scenarios["recorded_agent_policy"].append((f, case_from_events(row["agent"]["events"], 1)))
    for row in forced:
        f = fixtures[row["id"]]
        scenarios["paired_evidence"].append((f, case_from_events(row["rules"]["events"], 2)))
        scenarios["recorded_agent_forced"].append((f, case_from_events(row["agent"]["events"], 2)))
    # Exactly one recorded result per image; never count reruns as new samples.
    rows = forced + [r for r in policy if len(fixtures[r["id"]]["photo_ids"]) == 1]
    for row in rows:
        f = fixtures[row["id"]]
        for i, result in enumerate(row["direct"]["direct_results"]):
            inspection = next(
                e
                for e in row["rules"]["events"]
                if e.get("tool") == "inspect_image" and e["photo_id"] == result["photo_id"]
            )
            events = [
                dict(
                    id=1,
                    kind="tool",
                    tool="inspect_image",
                    status="ok",
                    photo_id="photo-1",
                    output=inspection["output"],
                ),
                dict(
                    id=2,
                    kind="tool",
                    tool="classify_breed",
                    status="ok",
                    photo_id="photo-1",
                    output=result["output"],
                ),
            ]
            c = case_from_events(events, 1)
            single = dict(f, id=f["photo_ids"][i])
            scenarios["individual_photos"].append((single, c))
            if i == 0:
                scenarios["initial_photos"].append((single, c))
            observations.append(
                dict(
                    image_id=single["id"],
                    case_id=f["id"],
                    cohort=cohort(f),
                    expected_label=f["classifier_label"],
                    quality_flags=inspection["output"]["quality_flags"],
                    **result["output"],
                )
            )
    assert len(observations) == len({r["image_id"] for r in observations}) == 20
    replay_rows = []
    for score, margin in itertools.product(SCORES, MARGINS):
        # Isolated diagnostic process only. The running app keeps its constants.
        with patch.object(evidence, "MIN_SCORE", score), patch.object(evidence, "MIN_MARGIN", margin):
            for scenario, cases in scenarios.items():
                groups, outcomes = {}, []
                for f, c in cases:
                    comparison = evidence.compare(c)
                    ids = comparison["report_eligible_ids"]
                    report = evidence.build_report(
                        c,
                        "visual_matches" if ids else "inconclusive",
                        ids[0] if ids else None,
                        "diagnostic_replay",
                    )
                    # Verify JSON serialization of the actual report contract.
                    assert json.loads(json.dumps(report)) == report
                    emitted = bool(report["candidates"])
                    correct = emitted and report["candidates"][0]["label"] == f["classifier_label"]
                    g = groups.setdefault(
                        cohort(f), dict(denominator=0, eligible=0, abstained=0, correct=0, incorrect=0)
                    )
                    g["denominator"] += 1
                    g["eligible"] += int(emitted)
                    g["abstained"] += int(not emitted)
                    if f["breed_accuracy_eligible"]:
                        g["correct"] += int(correct)
                        g["incorrect"] += int(emitted and not correct)
                    outcomes.append(
                        dict(
                            id=f["id"],
                            eligible=emitted,
                            blockers=comparison["blockers"],
                            label=report["candidates"][0]["label"] if emitted else None,
                        )
                    )
                replay_rows.append(
                    dict(score=score, margin=margin, scenario=scenario, cohorts=groups, outcomes=outcomes)
                )
    return dict(observations=observations, grid=replay_rows)


def numerical_probe(manifest, directory):
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    import numpy as np
    import torch
    import transformers
    from PIL import Image, ImageOps
    from transformers import AutoImageProcessor, AutoModelForImageClassification, pipeline
    from transformers.pipelines import ImageClassificationPipeline

    torch.set_num_threads(4)
    processor = AutoImageProcessor.from_pretrained(MODEL_DIR, local_files_only=True, use_fast=False)
    model, loading = AutoModelForImageClassification.from_pretrained(
        MODEL_DIR, local_files_only=True, use_safetensors=True, output_loading_info=True
    )
    model.eval()
    reference = pipeline("image-classification", model=model, image_processor=processor, device="cpu")
    write(
        directory / "installed-source.json",
        dict(
            forward=inspect.getsource(type(model).forward),
            pipeline_postprocess=inspect.getsource(ImageClassificationPipeline.postprocess),
            processor_preprocess=inspect.getsource(type(processor).preprocess),
        ),
    )
    images = {i["id"]: i for i in manifest["images"]}
    config = json.loads((MODEL_DIR / "preprocessor_config.json").read_text())
    result = dict(
        transformers=transformers.__version__,
        torch=torch.__version__,
        loading_info=loading,
        processor=config,
        classifier_head=str(model.classifier),
        label_mapping_inverse=all(model.config.label2id[v] == k for k, v in model.config.id2label.items()),
        rows=[],
    )
    worker = Classifier()
    try:
        with tempfile.TemporaryDirectory(prefix="breedframe-classifier-audit-") as tmp:
            for image_id in PROBE_IDS:
                info = images[image_id]
                raw = (ROOT / info["path"]).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == info["sha256"]
                normalized, metadata = normalize_image(raw)
                path = Path(tmp) / f"{image_id}.png"
                path.write_bytes(normalized)
                with Image.open(io.BytesIO(raw)) as original, Image.open(path) as saved:
                    source = ImageOps.exif_transpose(original).convert("RGB")
                    saved = saved.convert("RGB")
                    inputs = processor(images=saved, return_tensors="pt")
                    reference_inputs = processor(images=source, return_tensors="pt")
                    resized = saved.resize(
                        (config["size"]["width"], config["size"]["height"]),
                        resample=Image.Resampling(config["resample"]),
                    )
                    array = (np.asarray(resized).astype(np.float64) * config["rescale_factor"]).astype(
                        np.float32
                    )
                    manual = (
                        (array - np.array(config["image_mean"], dtype=np.float32))
                        / np.array(config["image_std"], dtype=np.float32)
                    ).transpose(2, 0, 1)[None]
                    head_values = []
                    hook = model.classifier.register_forward_hook(
                        lambda _m, _i, o: head_values.append(o.detach())
                    )
                    with torch.inference_mode():
                        logits = model(**inputs).logits
                    hook.remove()
                    scores = logits.float().softmax(-1)[0]
                    pipeline_result = reference(saved, top_k=5)
                actual = worker.classify(path)
                values, indices = scores.topk(5)
                row = dict(
                    image_id=image_id,
                    normalized_metadata=metadata,
                    worker=actual,
                    input_shape=list(inputs["pixel_values"].shape),
                    input_dtype=str(inputs["pixel_values"].dtype),
                    normalized_pixels_equal=source.tobytes() == saved.tobytes(),
                    original_processor_equal=torch.equal(
                        inputs["pixel_values"], reference_inputs["pixel_values"]
                    ),
                    manual_processor_max_abs_error=float(
                        np.abs(inputs["pixel_values"].numpy() - manual).max()
                    ),
                    logits=head_values[0][0].tolist(),
                    logits_are_linear_head_output=torch.equal(logits, head_values[0]),
                    logits_finite=bool(torch.isfinite(logits).all()),
                    softmax_sum=float(scores.sum()),
                    softmax_preserves_argmax=int(logits.argmax(-1)[0]) == int(scores.argmax()),
                    cpu_top5_class_ids=indices.tolist(),
                    cpu_top5_scores=values.tolist(),
                    pipeline_result=pipeline_result,
                    pipeline_max_score_error=max(
                        abs(p["score"] - float(v)) for p, v in zip(pipeline_result, values)
                    ),
                    worker_max_score_error=max(
                        abs(p["score"] - float(v)) for p, v in zip(actual["candidates"], values)
                    ),
                )
                row["passed"] = all(
                    [
                        row["normalized_pixels_equal"],
                        row["original_processor_equal"],
                        row["manual_processor_max_abs_error"] <= 1e-6,
                        row["logits_are_linear_head_output"],
                        row["logits_finite"],
                        abs(row["softmax_sum"] - 1) <= 1e-6,
                        row["softmax_preserves_argmax"],
                        row["pipeline_max_score_error"] <= 1e-6,
                        row["worker_max_score_error"] <= 1e-5,
                        [p["class_id"] for p in actual["candidates"]] == indices.tolist(),
                        [p["label"] for p in pipeline_result]
                        == [model.config.id2label[int(i)] for i in indices],
                    ]
                )
                result["rows"].append(row)
                write(directory / "numerical-probe.json", result)
    finally:
        worker.close()
    result["passed"] = (
        all(r["passed"] for r in result["rows"])
        and result["label_mapping_inverse"]
        and not any(loading.values())
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(MANIFEST.read_text())
    paths = [
        Path(__file__),
        MANIFEST,
        *sorted((ROOT / "breedframe").glob("*.py")),
        *[EVIDENCE / n for n in FILES],
        *[MODEL_DIR / n for n in ["config.json", "preprocessor_config.json", "model.safetensors"]],
    ]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    protocol = dict(
        controller=CONTROLLER,
        controller_calls=0,
        app_defaults_changed=False,
        probe_ids=PROBE_IDS,
        score_grid=SCORES,
        margin_grid=MARGINS,
        source_hashes=hashes,
        purpose="Mechanism verification and development sensitivity, not calibration or validation.",
        stopping_rule="Run three fixed probes and all grid cells once; retain failures; no sample extension.",
        scope="All 20 existing photos are exposed development evidence. Replay freezes observations, not controller behavior under new thresholds.",
        numerical_tolerances=dict(processor=1e-6, cpu_pipeline=1e-6, cpu_worker=1e-5),
    )
    write(args.output / "protocol.json", protocol)
    state = dict(complete=False)
    write(args.output / "completion.json", state)
    try:
        write(args.output / "threshold-replay.json", replay(manifest))
        probe = numerical_probe(manifest, args.output)
        write(args.output / "numerical-probe.json", probe)
        state.update(
            complete=True,
            numerical_checks_passed=probe["passed"],
            source_hashes_unchanged=all(digest(ROOT / p) == h for p, h in hashes.items()),
        )
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        write(args.output / "completion.json", state)


if __name__ == "__main__":
    main()
