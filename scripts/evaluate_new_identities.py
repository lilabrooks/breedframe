"""Prospective case-level comparison; no production policy changes."""

import argparse
import importlib.metadata
import json
import multiprocessing as mp
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from breedframe.classifier import Classifier
from breedframe.config import ROOT
from breedframe.images import inspect_image, normalize_image
from scripts.evaluate_suitability import (
    check_idle,
    pair_report,
    read,
    resnet_reports,
    resnet_worker,
    sha,
    write,
)

DIRECTORY = ROOT / "docs/evidence/identity-comparison"
INPUTS = ROOT / "data/identity-comparison"


def now():
    return datetime.now(timezone.utc).isoformat()


def prepare():
    assert not (DIRECTORY / "protocol.json").exists()
    selection = read(DIRECTORY / "selection.json")
    cases = selection["cases"]
    rng = random.Random(42)
    images = []
    for case in sorted(cases, key=lambda c: c["id"]):
        rng.shuffle(case["photo_ids"])
        case["initial_photo_id"] = case["photo_ids"][0]
        case["followup_photo_id"] = case["photo_ids"][1]
        for name in case["photo_ids"]:
            source = INPUTS / "images" / f"{name}.jpg"
            raw = source.read_bytes()
            normalized, metadata = normalize_image(raw)
            path = INPUTS / "normalized" / f"{name}.png"
            path.parent.mkdir(exist_ok=True)
            assert not path.exists()
            path.write_bytes(normalized)
            images.append(
                dict(
                    id=name,
                    case_id=case["id"],
                    path=str(source.relative_to(ROOT)),
                    sha256=sha(source),
                    normalized_path=str(path.relative_to(ROOT)),
                    normalized_sha256=sha(path),
                    normalized_metadata=metadata,
                    inspection=inspect_image(path),
                    source_metadata=str((DIRECTORY / f"{name}-source.json").relative_to(ROOT)),
                    visual_review=selection["visual_reviews"][name],
                )
            )
    assert len(cases) == 13 and len(images) == 26
    assert len({r["normalized_metadata"]["sha256"] for r in images}) == 26
    old = read(ROOT / "docs/evidence/paired-suitability/manifest.json")
    assert not ({r["sha256"] for r in images} & {r["sha256"] for r in old["images"]})
    assert not (
        {r["normalized_metadata"]["sha256"] for r in images}
        & {r["normalized_metadata"]["sha256"] for r in old["images"]}
    )
    old_ids = set(selection["previously_inferred_subject_ids"])
    assert not (old_ids & {subject for c in cases for subject in c["subject_ids"]})
    manifest = dict(
        created_at_utc=now(),
        cases=cases,
        images=images,
        first_photo_assignment="Python Random(42), shuffle each pair in sorted case-id order",
        exposure=selection["exposure"],
        exclusions=selection["exclusions"],
        previous_subjects=sorted(old_ids),
    )
    write(DIRECTORY / "manifest.json", manifest, exclusive=True)
    schedule = sorted(
        cases, key=lambda c: ({"non_dog": 0, "supported_breed": 1}.get(c["cohort"], 2), c["id"])
    )
    calls = [dict(model="resnet", case_id=c["id"], image_id=c["initial_photo_id"]) for c in schedule]
    calls += [dict(model="vit", case_id=c["id"], image_id=i) for c in schedule for i in c["photo_ids"]]
    files = [
        Path(__file__).resolve(),
        ROOT / "scripts/evaluate_suitability.py",
        ROOT / "scripts/offline.sb",
        ROOT / "uv.lock",
        DIRECTORY / "selection.json",
        ROOT / "docs/identity-comparison-protocol.md",
        ROOT / "docs/evidence/paired-suitability/manifest.json",
        *sorted((ROOT / "breedframe").glob("*.py")),
        *sorted((ROOT / "breedframe/static").glob("*")),
        *[ROOT / r["source_metadata"] for r in images],
    ]
    for model in ["vit", "resnet50-candidate"]:
        files.extend(
            ROOT / "models" / model / n
            for n in ["config.json", "preprocessor_config.json", "model.safetensors"]
        )
    write(
        DIRECTORY / "protocol.json",
        dict(
            registered_at_utc=now(),
            manifest_sha256=sha(DIRECTORY / "manifest.json"),
            source_hashes={str(p.relative_to(ROOT)): sha(p) for p in files},
            packages={n: importlib.metadata.version(n) for n in ["torch", "transformers", "pillow", "httpx"]},
            schedule=calls,
            classifier_timeout_seconds=60,
            controller_calls=0,
            vision_calls=0,
            resnet=dict(score=0.8, margin=0, native_dog_ids_inclusive=[151, 268], photos_per_case=1),
            vit=dict(score=0, margin=0, photos_per_case=2, retain_other_application_checks=True),
            primary_criteria=dict(
                supported_cases=6,
                min_reports=3,
                max_error_fraction=0.1,
                non_dog_cases=3,
                max_non_dog_reports=0,
            ),
            termination="Complete all 39 calls once unless runtime/concurrency/source integrity fails. No tuning or sample extension.",
        ),
        exclusive=True,
    )
    print("Frozen 13 cases, 26 images, 39 classifier calls; no inference performed.")


def verify_inputs():
    protocol = read(DIRECTORY / "protocol.json")
    assert sha(DIRECTORY / "manifest.json") == protocol["manifest_sha256"]
    assert all(sha(ROOT / p) == h for p, h in protocol["source_hashes"].items())
    assert all(importlib.metadata.version(n) == v for n, v in protocol["packages"].items())
    manifest = read(DIRECTORY / "manifest.json")
    for image in manifest["images"]:
        assert sha(ROOT / image["path"]) == image["sha256"]
        assert sha(ROOT / image["normalized_path"]) == image["normalized_sha256"]
    return protocol, manifest


def account(case, model, emitted, top1, raw):
    label = top1["label"] if top1 else None
    correct = None
    if case["cohort"] == "supported_breed" and emitted:
        correct = (
            top1["class_id"] == case["expected_native_id"]
            if model == "resnet"
            else label == case["expected_label"]
        )
    scope = "no_label_proposal"
    if emitted:
        scope = {
            "non_dog": "prohibited_non_dog_report",
            "unknown_ancestry": "individual_visual_match_only_no_ancestry_claim",
            "unsupported_breed": "unsupported_breed_proposal_no_exact_label_available",
            "shared_description_group": "scene_scope_required_exact_shared_breed_unverified",
            "different_breed_group": "subject_selection_required_before_standalone_report",
        }.get(case["cohort"], "individual_visual_match")
    return dict(
        case_id=case["id"],
        cohort=case["cohort"],
        model=model,
        emitted=emitted,
        top1=top1,
        correct=correct,
        scope_obligation=scope,
        evidence=raw,
    )


def evaluate(manifest, calls):
    images = {r["id"]: r for r in manifest["images"]}
    vit = {r["image_id"]: r["output"] for r in calls if r["model"] == "vit"}
    resnet = {r["image_id"]: r["output"] for r in calls if r["model"] == "resnet"}
    rows = []
    for c in manifest["cases"]:
        r = resnet[c["initial_photo_id"]]
        emitted = resnet_reports(r)
        rows.append(
            account(
                c,
                "resnet",
                emitted,
                r["candidates"][0] if emitted else None,
                dict(
                    image_id=c["initial_photo_id"],
                    native_top1=r["candidates"][0],
                    score=r["top1_score"],
                    margin=r["margin"],
                ),
            )
        )
        p = pair_report(c, images, vit)
        rows.append(
            account(
                c,
                "vit",
                p["emitted"],
                p["report"]["candidates"][0] if p["emitted"] else None,
                dict(comparison=p["comparison"], report=p["report"], case=p["case"]),
            )
        )
    groups = {}
    for model in ["resnet", "vit"]:
        cohorts = {}
        for cohort in sorted({c["cohort"] for c in manifest["cases"]}):
            subset = [r for r in rows if r["model"] == model and r["cohort"] == cohort]
            reports = [r for r in subset if r["emitted"]]
            g = dict(cases=len(subset), reports=len(reports), abstentions=len(subset) - len(reports))
            if cohort == "supported_breed":
                g.update(
                    correct=sum(r["correct"] is True for r in reports),
                    wrong=sum(r["correct"] is False for r in reports),
                    coverage=len(reports) / len(subset),
                    error_fraction=sum(r["correct"] is False for r in reports) / len(reports)
                    if reports
                    else None,
                )
            cohorts[cohort] = g
        supported, negatives = cohorts["supported_breed"], cohorts["non_dog"]
        assert supported["cases"] == 6 and negatives["cases"] == 3
        groups[model] = dict(
            cohorts=cohorts,
            primary_targets_met=(
                supported["reports"] >= 3
                and supported["wrong"] / max(supported["reports"], 1) <= 0.1
                and negatives["reports"] == 0
            ),
            product_ready=False,
        )
    return dict(
        rows=rows,
        models=groups,
        scope_note="Annotations diagnose scope after inference; they never gate proposals.",
    )


def run():
    protocol, manifest = verify_inputs()
    target = DIRECTORY / "results.json"
    state = dict(
        started_at_utc=now(),
        complete=False,
        calls=[],
        controller_calls=0,
        vision_calls=0,
        protocol_sha256=sha(DIRECTORY / "protocol.json"),
    )
    write(target, state, exclusive=True)
    images = {r["id"]: r for r in manifest["images"]}
    process = conn = None
    vit = Classifier(timeout=60)
    try:
        with httpx.Client(trust_env=False, timeout=10) as client:
            state["app_before"] = check_idle(client)
            for call in protocol["schedule"]:
                check_idle(client)
                if call["model"] == "vit" and process:
                    process.terminate()
                    process.join(timeout=3)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=3)
                    conn.close()
                    process = conn = None
                row = dict(**call, started_at_utc=now())
                state["calls"].append(row)
                write(target, state)
                path = ROOT / images[call["image_id"]]["normalized_path"]
                started = time.monotonic()
                try:
                    if call["model"] == "resnet":
                        if process is None:
                            conn, child = mp.get_context("spawn").Pipe()
                            process = mp.get_context("spawn").Process(
                                target=resnet_worker, args=(child,), daemon=True
                            )
                            process.start()
                            child.close()
                        conn.send(str(path))
                        assert conn.poll(60), "ResNet request time limit exceeded."
                        result = conn.recv()
                        if "error" in result:
                            raise RuntimeError(result["error"])
                        row["output"] = result["ok"]
                    else:
                        row["output"] = vit.classify(path)
                    row["seconds_including_first_load"] = time.monotonic() - started
                except Exception as exc:
                    row.update(error=f"{type(exc).__name__}: {exc}", seconds=time.monotonic() - started)
                    raise
                write(target, state)
                print(call["model"], call["image_id"], row["output"]["candidates"][0]["label"], flush=True)
            state["evaluation"] = evaluate(manifest, state["calls"])
            verify_inputs()
            state["app_after"] = check_idle(client)
            state.update(complete=True, finished_at_utc=now())
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        vit.close()
        if process:
            process.terminate()
            process.join(timeout=3)
            if process.is_alive():
                process.kill()
                process.join(timeout=3)
        if conn:
            conn.close()
        write(target, state)
    print(json.dumps(state["evaluation"]["models"], indent=2))


def verify():
    protocol, manifest = verify_inputs()
    result = read(DIRECTORY / "results.json")
    assert result["complete"] and result["protocol_sha256"] == sha(DIRECTORY / "protocol.json")
    assert [{k: r[k] for k in ["model", "case_id", "image_id"]} for r in result["calls"]] == protocol[
        "schedule"
    ]
    assert len(result["calls"]) == 39 and all("error" not in c for c in result["calls"])
    assert evaluate(manifest, result["calls"]) == result["evaluation"]
    expected = {
        str(r["expected_native_id"]): r["expected_label"]
        for r in manifest["cases"]
        if r["cohort"] == "supported_breed"
    }
    config = read(ROOT / "models/resnet50-candidate/config.json")
    assert set(expected).issubset(config["id2label"])
    with httpx.Client(trust_env=False, timeout=10) as client:
        health = check_idle(client)
    write(
        DIRECTORY / "verification.json",
        dict(
            verified_at_utc=now(),
            results_sha256=sha(DIRECTORY / "results.json"),
            source_and_input_hashes_unchanged=True,
            all_39_calls_accounted_for=True,
            saved_reports_and_metrics_reproduced=True,
            app_after=health,
        ),
        exclusive=True,
    )
    print(
        "Verified 39 calls, 26 candidate case outcomes, saved reports, denominators, and unchanged app inputs."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "run", "verify"])
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "verify": verify}[args.phase]()
