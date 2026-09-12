"""Registered development experiment; never changes the application policy."""

import argparse
import base64
import copy
import hashlib
import importlib.metadata
import io
import json
import multiprocessing as mp
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
from PIL import Image

from breedframe import evidence
from breedframe.classifier import Classifier
from breedframe.config import CONTROLLER_MODELS, OLLAMA_URL, ROOT
from breedframe.images import inspect_image, normalize_image
from breedframe.metrics import MemorySampler
from breedframe.model_identity import verify_controller

DIRECTORY = ROOT / "docs/evidence/paired-suitability"
INPUTS = ROOT / "data/paired-suitability"
OLD_MANIFEST = ROOT / "docs/evidence/photo-set-v2/manifest.json"
VIT_CACHE = ROOT / "docs/evidence/classifier-audit/threshold-replay.json"
RESNET_CACHE = ROOT / "docs/evidence/classifier-screen/development-results.json"
MODEL = "qwen3.5:4b"
NEW_IDS = ["socks-02", "valegro-01", "valegro-02", "bobby-statue-01", "bobby-statue-02"]
SCHEMA = {
    "type": "object",
    "properties": {
        "subject_type": {
            "type": "string",
            "enum": ["real_dog", "dog_depiction", "other_animal", "no_animal", "uncertain"],
        },
        "dog_count": {"type": "string", "enum": ["zero", "one", "multiple", "uncertain"]},
    },
    "required": ["subject_type", "dog_count"],
    "additionalProperties": False,
}
PROMPT = """Examine the supplied image for visible real dogs. Return only the JSON object.
Use subject_type real_dog when at least one real dog is visible. Otherwise use dog_depiction
for a dog shown only as a sculpture, toy, drawing, painting or other depiction; other_animal
for a visible animal that is not a dog; no_animal when neither an animal nor a dog depiction
is visible; or uncertain when the image does not support a decision or no image is available.
dog_count counts visible real dogs, excluding depictions: zero, one, multiple, or uncertain.
Do not infer breed, ancestry, identity, or whether different dogs share a breed.
Base your answer on the supplied image, not familiarity with a named subject. /no_think
Schema: """ + json.dumps(SCHEMA, sort_keys=True)
OPTIONS = dict(
    temperature=0,
    seed=42,
    num_ctx=8192,
    num_predict=300,
    presence_penalty=0,
    repeat_penalty=1,
    top_k=20,
    top_p=0.95,
)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value, exclusive=False):
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if exclusive:
        with path.open("x") as stream:
            stream.write(text)
    else:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(text)
        temporary.replace(path)


def read(path):
    return json.loads(path.read_text())


def cohort(case):
    if case["breed_accuracy_eligible"]:
        return "supported_breed"
    if not case["live_dog_present"]:
        return "non_dog"
    return "unsupported_breed" if case["kind"] == "same_dog_pair" else case["kind"]


def prepare():
    """Normalize and hash inputs, then seal schedule and criteria without inference."""
    assert not (DIRECTORY / "protocol.json").exists()
    old = read(OLD_MANIFEST)
    cases = {i: c for c in old["cases"] for i in c["photo_ids"]}
    rows = []
    reviews = {
        "socks-02": "Cat at a lectern, no live dog visible. Different exposure from the official portrait.",
        "valegro-01": "Horse and rider in an arena, side view; no live dog visible. Source names Valegro, 2012.",
        "valegro-02": "Horse and rider approaching camera; no live dog visible. Source names Valegro, 2014.",
        "bobby-statue-01": "Dog sculpture on a fountain, surroundings and one person; no live dog visible.",
        "bobby-statue-02": "Closer front view of the same dog sculpture; no live dog visible. Different author/exposure.",
    }
    for info in old["images"]:
        c = cases[info["id"]]
        row = dict(
            id=info["id"],
            path=info["path"],
            sha256=info["sha256"],
            cohort=cohort(c),
            identity_group=c["leakage_group"],
            live_dog_present=c["live_dog_present"],
            expected_label=c["classifier_label"],
            expected_subject_type="real_dog"
            if c["live_dog_present"]
            else ("dog_depiction" if c["kind"] == "dog_sculpture" else "other_animal"),
            expected_dog_count="multiple"
            if c["kind"] == "multiple_dogs"
            else ("one" if c["live_dog_present"] else "zero"),
            prior_exposure="Existing development corpus; cached ViT and ResNet predictions reused.",
            provenance_manifest=str(OLD_MANIFEST.relative_to(ROOT)),
        )
        rows.append(row)
    for name in NEW_IDS:
        page = read(DIRECTORY / f"{name}-source.json")
        info = page["imageinfo"][0]
        path = INPUTS / "images" / f"{name}.jpg"
        depiction = name.startswith("bobby")
        rows.append(
            dict(
                id=name,
                path=str(path.relative_to(ROOT)),
                sha256=sha(path),
                cohort="non_dog",
                identity_group="greyfriars-bobby-sculpture"
                if depiction
                else ("socks" if name.startswith("socks") else "valegro"),
                live_dog_present=False,
                expected_label=None,
                expected_subject_type="dog_depiction" if depiction else "other_animal",
                expected_dog_count="zero",
                visual_review=reviews[name],
                source_title=page["title"],
                source_page=info["descriptionurl"],
                source_revision_url=f"https://commons.wikimedia.org/w/index.php?oldid={page['revisions'][0]['revid']}",
                download_url=info.get("thumburl", info["url"]),
                original_sha1=info["sha1"],
                source_metadata=str((DIRECTORY / f"{name}-source.json").relative_to(ROOT)),
                license=info["extmetadata"]["LicenseShortName"]["value"],
                prior_exposure="Selected and visually reviewed before new inference; training overlap unknown.",
            )
        )
    for row in rows:
        source = ROOT / row["path"]
        assert sha(source) == row["sha256"]
        normalized, metadata = normalize_image(source.read_bytes())
        normal_path = INPUTS / "normalized" / f"{row['id']}.png"
        vision_path = INPUTS / "vision" / f"{row['id']}.png"
        for path in (normal_path, vision_path):
            path.parent.mkdir(parents=True, exist_ok=True)
            assert not path.exists()
        normal_path.write_bytes(normalized)
        with Image.open(io.BytesIO(normalized)) as im:
            im.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            im.save(vision_path, format="PNG")
            row["vision_dimensions"] = list(im.size)
        row.update(
            normalized_metadata=metadata,
            normalized_path=str(normal_path.relative_to(ROOT)),
            normalized_sha256=sha(normal_path),
            vision_path=str(vision_path.relative_to(ROOT)),
            vision_sha256=sha(vision_path),
            inspection=inspect_image(normal_path),
        )
    assert len(rows) == 25 and len({r["normalized_metadata"]["sha256"] for r in rows}) == 25
    assert sum(r["live_dog_present"] for r in rows) == 17
    pairs = [
        dict(
            id=c["id"],
            photo_ids=c["photo_ids"],
            cohort=cohort(c),
            expected_label=c["classifier_label"],
            exposure="Previously exposed pair",
        )
        for c in old["cases"]
        if len(c["photo_ids"]) == 2
    ]
    pairs.extend(
        [
            dict(
                id="socks",
                photo_ids=["cat-01", "socks-02"],
                cohort="non_dog",
                expected_label=None,
                exposure="One exposed image; documented second photo of the same cat",
            ),
            dict(
                id="valegro",
                photo_ids=["valegro-01", "valegro-02"],
                cohort="non_dog",
                expected_label=None,
                exposure="New photos of the same named horse, 2012 and 2014",
            ),
            dict(
                id="bobby-statue",
                photo_ids=["bobby-statue-01", "bobby-statue-02"],
                cohort="non_dog",
                expected_label=None,
                exposure="New photos of the same sculpture, different authors and exposures",
            ),
        ]
    )
    manifest = dict(
        created_at_utc=now(),
        images=rows,
        pairs=pairs,
        selection="Convenience controls selected by visible content, source identity and reuse metadata before inference.",
        excluded_before_inference={
            "fala-01": "Dog sculpture too small in a wide memorial scene to be a useful depiction challenge.",
            "fala-02": "Dog sculpture too small in a wide memorial scene to be a useful depiction challenge.",
        },
        limitations=[
            "No paired unknown-ancestry or multiple-dog controls; no different-breed group.",
            "No non-animal empty scenes; depiction controls are sculptures only.",
            "Source-reported identities and breeds; no pedigree validation or confirmed training exclusion.",
            "Photos in each pair are dependent observations of one identity, not independent subjects.",
        ],
    )
    write(DIRECTORY / "manifest.json", manifest, exclusive=True)
    files = [
        Path(__file__).resolve(),
        OLD_MANIFEST,
        VIT_CACHE,
        RESNET_CACHE,
        ROOT / "uv.lock",
        ROOT / "docs/paired-suitability-protocol.md",
        ROOT / "scripts/offline.sb",
        *sorted((ROOT / "breedframe").glob("*.py")),
        *sorted((ROOT / "breedframe/static").glob("*")),
        *[DIRECTORY / f"{name}-source.json" for name in NEW_IDS],
    ]
    for model_dir in [ROOT / "models/vit", ROOT / "models/resnet50-candidate"]:
        files.extend(
            model_dir / name for name in ["config.json", "preprocessor_config.json", "model.safetensors"]
        )
    schedule = sorted(r["id"] for r in rows)
    random.Random(42).shuffle(schedule)
    schedule.append("no-image-control")
    protocol = dict(
        registered_at_utc=now(),
        manifest_sha256=sha(DIRECTORY / "manifest.json"),
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in files},
        packages={
            name: importlib.metadata.version(name) for name in ["torch", "transformers", "pillow", "httpx"]
        },
        new_classifier_ids=NEW_IDS,
        vision_schedule=schedule,
        vision_prompt=PROMPT,
        vision_schema=SCHEMA,
        vision_options=OPTIONS,
        vision_timeout_seconds=60,
        ollama_version="0.34.0",
        model=MODEL,
        model_digest=CONTROLLER_MODELS[MODEL],
        vit_rule=dict(
            min_score=0,
            min_margin=0,
            minimum_ranked_photos=2,
            retain_quality_unresolved_disagreement_and_current_photo_checks=True,
        ),
        resnet_rule=dict(min_score=0.8, min_margin=0, native_dog_ids_inclusive=[151, 268]),
        vision_trigger="All stage-A calls complete, and at least one ViT non-dog pair reports OR ResNet admits a non-dog photo among all 25.",
        vision_advance=dict(
            max_non_dog_accepts=0,
            min_live_dog_accepts=16,
            min_supported_reports=6,
            max_error_fraction=0.1,
            max_multi_dog_individual_scopes=0,
            require_all_valid=True,
            require_no_image_abstention=True,
        ),
        inference_limit="Five new ViT calls, five new ResNet calls, then only if triggered: 25 image calls and one no-image call. No retries or sample extension.",
        app_defaults_changed=False,
        controller_calls=0,
    )
    write(DIRECTORY / "protocol.json", protocol, exclusive=True)
    print(f"Frozen {len(pairs)} pairs and {len(rows)} vision images; no inference performed.")


def verify_inputs():
    protocol = read(DIRECTORY / "protocol.json")
    assert sha(DIRECTORY / "manifest.json") == protocol["manifest_sha256"]
    assert all(sha(ROOT / p) == value for p, value in protocol["source_hashes"].items())
    assert all(importlib.metadata.version(n) == v for n, v in protocol["packages"].items())
    manifest = read(DIRECTORY / "manifest.json")
    for row in manifest["images"]:
        for p, h in [
            ("path", "sha256"),
            ("normalized_path", "normalized_sha256"),
            ("vision_path", "vision_sha256"),
        ]:
            assert sha(ROOT / row[p]) == row[h]
    return protocol, manifest


def check_idle(client, permitted_models=()):
    runtime = client.get(OLLAMA_URL + "/api/version")
    runtime.raise_for_status()
    assert runtime.json() == {"version": "0.34.0"}
    health = client.get("http://127.0.0.1:8765/api/health")
    health.raise_for_status()
    state = health.json()
    assert state["ready"] and not state["busy"] and state["controller"] == "qwen3:4b"
    response = client.get(OLLAMA_URL + "/api/ps")
    response.raise_for_status()
    assert all(m["name"] in permitted_models for m in response.json()["models"])
    return state


def resnet_worker(conn):
    try:
        import torch
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        torch.set_num_threads(4)
        assert torch.backends.mps.is_available(), (
            "The registered comparator uses MPS; no silent device change."
        )
        path = ROOT / "models/resnet50-candidate"
        processor = AutoImageProcessor.from_pretrained(path, local_files_only=True, use_fast=False)
        model, loading = AutoModelForImageClassification.from_pretrained(
            path, local_files_only=True, use_safetensors=True, output_loading_info=True
        )
        assert (
            not loading["missing_keys"] and not loading["unexpected_keys"] and not loading["mismatched_keys"]
        )
        model.eval().to("mps")
        assert len(model.config.id2label) == 1000
        while True:
            image_path = conn.recv()
            started = time.monotonic()
            with Image.open(image_path) as image:
                inputs = processor(images=image.convert("RGB"), return_tensors="pt")
            with torch.inference_mode():
                logits = model(**{k: v.to("mps") for k, v in inputs.items()}).logits
                scores = logits.float().softmax(-1)[0].cpu()
            values, indices = scores.topk(5)
            conn.send(
                dict(
                    ok=dict(
                        native_scores=scores.tolist(),
                        device="mps",
                        inference_seconds=time.monotonic() - started,
                        candidates=[
                            dict(class_id=int(i), label=model.config.id2label[int(i)], score=float(s))
                            for s, i in zip(values, indices)
                        ],
                        top1_score=float(values[0]),
                        margin=float(values[0] - values[1]),
                        native_top1_is_breed=151 <= int(indices[0]) <= 268,
                    )
                )
            )
    except Exception as exc:
        conn.send(dict(error=f"{type(exc).__name__}: {exc}"))
    finally:
        conn.close()


def resnet_reports(row):
    return bool(
        "error" not in row and row["native_top1_is_breed"] and row["top1_score"] >= 0.8 and row["margin"] >= 0
    )


def pair_report(pair, images, vit):
    events = []
    for index, image_id in enumerate(pair["photo_ids"]):
        photo_id = f"photo-{index + 1}"
        events.extend(
            [
                dict(
                    id=2 * index + 1,
                    kind="tool",
                    tool="inspect_image",
                    status="ok",
                    photo_id=photo_id,
                    output=images[image_id]["inspection"],
                ),
                dict(
                    id=2 * index + 2,
                    kind="tool",
                    tool="classify_breed",
                    status="ok",
                    photo_id=photo_id,
                    output={
                        k: v
                        for k, v in vit[image_id].items()
                        if k in {"candidates", "margin", "device", "inference_seconds", "fallback"}
                    },
                ),
            ]
        )
    case = dict(photos=[dict(id=f"photo-{i + 1}") for i in range(len(pair["photo_ids"]))], events=events)
    with patch.object(evidence, "MIN_SCORE", 0), patch.object(evidence, "MIN_MARGIN", 0):
        comparison = evidence.compare(case)
        enough = len({e["photo_id"] for e in events if e["tool"] == "classify_breed"}) >= 2
        eligible_ids = comparison["report_eligible_ids"] if enough else []
        report = evidence.build_report(
            case,
            "visual_matches" if eligible_ids else "inconclusive",
            eligible_ids[0] if eligible_ids else None,
            "registered_pair_replay",
        )
    emitted = bool(report["candidates"])
    return dict(
        **pair,
        report=report,
        comparison=comparison,
        case=case,
        emitted=emitted,
        correct=emitted and report["candidates"][0]["label"] == pair["expected_label"],
    )


def agreement():
    protocol, manifest = verify_inputs()
    target = DIRECTORY / "agreement-results.json"
    state = dict(
        started_at_utc=now(),
        complete=False,
        protocol_sha256=sha(DIRECTORY / "protocol.json"),
        new_vit_rows=[],
        new_resnet_rows=[],
        controller_calls=0,
    )
    write(target, state, exclusive=True)
    classifier = Classifier(timeout=60)
    process = conn = None
    try:
        images = {r["id"]: r for r in manifest["images"]}
        with httpx.Client(trust_env=False, timeout=10) as client:
            state["app_before"] = check_idle(client)
        vit = {r["image_id"]: r for r in read(VIT_CACHE)["observations"]}
        resnet = {r["image_id"]: r for r in read(RESNET_CACHE)["rows"]}
        for name in protocol["new_classifier_ids"]:
            with httpx.Client(trust_env=False, timeout=10) as client:
                check_idle(client)
            state["active_call"] = dict(model="vit", image_id=name)
            write(target, state)
            started = time.monotonic()
            result = classifier.classify(ROOT / images[name]["normalized_path"])
            row = dict(image_id=name, **result, request_seconds=time.monotonic() - started)
            vit[name] = row
            state["new_vit_rows"].append(row)
            write(target, state)
            print("ViT", name, row["candidates"][0]["label"], flush=True)
        classifier.close()
        conn, child = mp.get_context("spawn").Pipe()
        process = mp.get_context("spawn").Process(target=resnet_worker, args=(child,), daemon=True)
        process.start()
        child.close()
        for name in protocol["new_classifier_ids"]:
            with httpx.Client(trust_env=False, timeout=10) as client:
                check_idle(client)
            state["active_call"] = dict(model="resnet", image_id=name)
            write(target, state)
            started = time.monotonic()
            conn.send(str(ROOT / images[name]["normalized_path"]))
            assert conn.poll(60), "ResNet time limit exceeded."
            output = conn.recv()
            if "error" in output:
                raise RuntimeError(output["error"])
            row = dict(image_id=name, **output["ok"], request_seconds=time.monotonic() - started)
            resnet[name] = row
            state["new_resnet_rows"].append(row)
            write(target, state)
            print("ResNet", name, row["candidates"][0]["label"], flush=True)
        state["pairs"] = [pair_report(p, images, vit) for p in manifest["pairs"]]
        state["resnet_baseline"] = [
            dict(
                image_id=r["id"],
                cohort=r["cohort"],
                emitted=resnet_reports(resnet[r["id"]]),
                correct=resnet[r["id"]].get("correct") if r["cohort"] == "supported_breed" else None,
                top1=resnet[r["id"]]["candidates"][0],
                margin=resnet[r["id"]]["margin"],
            )
            for r in manifest["images"]
        ]
        state["false_non_dog_pair_reports"] = [
            p["id"] for p in state["pairs"] if p["cohort"] == "non_dog" and p["emitted"]
        ]
        state["false_non_dog_resnet_reports"] = [
            r["image_id"] for r in state["resnet_baseline"] if r["cohort"] == "non_dog" and r["emitted"]
        ]
        state["vision_triggered"] = bool(
            state["false_non_dog_pair_reports"] or state["false_non_dog_resnet_reports"]
        )
        verify_inputs()
        state.update(complete=True, finished_at_utc=now(), active_call=None)
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        classifier.close()
        if process:
            process.terminate()
            process.join(timeout=3)
            if process.is_alive():
                process.kill()
                process.join(timeout=3)
        if conn:
            conn.close()
        write(target, state)
    print(
        json.dumps(
            {
                k: state[k]
                for k in [
                    "complete",
                    "false_non_dog_pair_reports",
                    "false_non_dog_resnet_reports",
                    "vision_triggered",
                ]
            }
        )
    )


def vision_request(protocol, row=None):
    message = dict(role="user", content=protocol["vision_prompt"])
    if row:
        message["images"] = [base64.b64encode((ROOT / row["vision_path"]).read_bytes()).decode("ascii")]
    return dict(
        model=protocol["model"],
        messages=[message],
        format=protocol["vision_schema"],
        stream=False,
        think=False,
        options=protocol["vision_options"],
        keep_alive="30m",
    )


def parse_screen(payload):
    assert payload.get("model") == MODEL, "Returned model identity mismatch."
    assert payload.get("done") and payload.get("done_reason") == "stop", "Incomplete output."
    assert not payload["message"].get("thinking"), "Unexpected thinking output."
    result = json.loads(payload["message"]["content"])
    assert isinstance(result, dict) and set(result) == set(SCHEMA["required"])
    for key, value in result.items():
        assert value in SCHEMA["properties"][key]["enum"]
    if result["subject_type"] == "real_dog":
        assert result["dog_count"] in {"one", "multiple", "uncertain"}
    elif result["subject_type"] != "uncertain":
        assert result["dog_count"] == "zero"
    accepted = result["subject_type"] == "real_dog" and result["dog_count"] in {"one", "multiple"}
    return dict(
        **result,
        accepted=accepted,
        proposed_scope=("individual" if result["dog_count"] == "one" else "scene") if accepted else None,
    )


def vision():
    protocol, manifest = verify_inputs()
    stage_a = read(DIRECTORY / "agreement-results.json")
    assert stage_a["complete"] and stage_a["vision_triggered"], (
        "Registered continuation condition is not met."
    )
    target = DIRECTORY / "vision-results.json"
    state = dict(
        started_at_utc=now(),
        complete=False,
        rows=[],
        protocol_sha256=sha(DIRECTORY / "protocol.json"),
        stage_a_sha256=sha(DIRECTORY / "agreement-results.json"),
        role="Isolated image suitability screen; no controller decisions or application actions",
    )
    write(target, state, exclusive=True)
    images = {r["id"]: r for r in manifest["images"]}
    baseline = {r["image_id"]: r for r in stage_a["resnet_baseline"]}
    sampler = MemorySampler(controller=MODEL)
    with httpx.Client(trust_env=False, timeout=protocol["vision_timeout_seconds"]) as client:
        try:
            state["app_before"] = check_idle(client)
            state["identity"] = verify_controller(MODEL, client)
            response = client.post(OLLAMA_URL + "/api/show", json=dict(model=MODEL))
            response.raise_for_status()
            state["package"] = response.json()
            assert "vision" in state["package"]["capabilities"]
            with sampler:
                state["memory_baseline"] = dict(
                    rss_bytes=sampler.peak_rss, footprint_bytes=sampler.peak_footprint
                )
                for name in protocol["vision_schedule"]:
                    check_idle(client, (MODEL,))
                    assert verify_controller(MODEL, client) == state["identity"]
                    info = images.get(name)
                    request = vision_request(protocol, info)
                    wire = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    redacted = copy.deepcopy(request)
                    if info:
                        redacted["messages"][0]["images"] = [
                            dict(
                                local_path=info["vision_path"],
                                sha256=info["vision_sha256"],
                                encoding="base64 PNG",
                            )
                        ]
                    row = dict(
                        image_id=name,
                        request=redacted,
                        request_sha256=hashlib.sha256(wire).hexdigest(),
                        started_at_utc=now(),
                    )
                    state["rows"].append(row)
                    write(target, state)
                    started = time.monotonic()
                    try:
                        response = client.post(
                            OLLAMA_URL + "/api/chat",
                            content=wire,
                            headers={"Content-Type": "application/json"},
                        )
                        row.update(
                            seconds=time.monotonic() - started,
                            status_code=response.status_code,
                            raw_response=response.text,
                        )
                        response.raise_for_status()
                        payload = response.json()
                        if payload.get("model") != MODEL:
                            raise RuntimeError("Returned model identity mismatch; aborting remaining calls.")
                        row["screen"] = parse_screen(payload)
                    except (AssertionError, ValueError) as exc:
                        row["error"] = f"{type(exc).__name__}: {exc}"
                        row["screen"] = dict(accepted=False, proposed_scope=None)
                    except Exception as exc:
                        row.update(seconds=time.monotonic() - started, error=f"{type(exc).__name__}: {exc}")
                        raise
                    if info:
                        row.update(
                            cohort=info["cohort"],
                            live_dog_present=info["live_dog_present"],
                            expected_dog_count=info["expected_dog_count"],
                            subject_type_correct=row["screen"].get("subject_type")
                            == info["expected_subject_type"],
                            dog_count_correct=row["screen"].get("dog_count") == info["expected_dog_count"],
                            resnet_baseline_emitted=baseline[name]["emitted"],
                            resnet_screened_emitted=baseline[name]["emitted"] and row["screen"]["accepted"],
                            baseline_correct=baseline[name]["correct"],
                        )
                    write(target, state)
                    print(name, row.get("screen", row.get("error")), flush=True)
            state["memory"] = sampler.result()
            state["memory"]["scope_note"] = (
                "Isolated screen runner plus project Ollama; classifiers unloaded. Not a whole-app concurrent pipeline measurement."
            )
            verify_inputs()
            state.update(complete=True, finished_at_utc=now())
        except Exception as exc:
            state["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            write(target, state)
            response = client.post(OLLAMA_URL + "/api/generate", json=dict(model=MODEL, keep_alive=0))
            state["unload_status_code"] = response.status_code
            state["app_after"] = check_idle(client)
            write(target, state)


def verify():
    protocol, manifest = verify_inputs()
    a = read(DIRECTORY / "agreement-results.json")
    assert a["complete"] and a["protocol_sha256"] == sha(DIRECTORY / "protocol.json")
    assert [r["image_id"] for r in a["new_vit_rows"]] == NEW_IDS
    assert [r["image_id"] for r in a["new_resnet_rows"]] == NEW_IDS
    out = dict(
        verified_at_utc=now(),
        source_and_input_hashes_unchanged=True,
        stage_a_sha256=sha(DIRECTORY / "agreement-results.json"),
        vision_triggered=a["vision_triggered"],
    )
    if a["vision_triggered"]:
        v = read(DIRECTORY / "vision-results.json")
        assert v["complete"] and v["stage_a_sha256"] == out["stage_a_sha256"]
        assert v["protocol_sha256"] == sha(DIRECTORY / "protocol.json")
        assert [r["image_id"] for r in v["rows"]] == protocol["vision_schedule"]
        images = {r["id"]: r for r in manifest["images"]}
        for r in v["rows"]:
            request = vision_request(protocol, images.get(r["image_id"]))
            wire = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            assert hashlib.sha256(wire).hexdigest() == r["request_sha256"]
            if "error" not in r:
                assert parse_screen(json.loads(r["raw_response"])) == r["screen"]
        rows = [r for r in v["rows"] if r["image_id"] in images]
        summary = dict(
            non_dog_accepts=sum(r["screen"]["accepted"] for r in rows if not r["live_dog_present"]),
            non_dog_total=8,
            live_dog_accepts=sum(r["screen"]["accepted"] for r in rows if r["live_dog_present"]),
            live_dog_total=17,
            supported_reports=sum(
                r["resnet_screened_emitted"] for r in rows if r["cohort"] == "supported_breed"
            ),
            supported_total=12,
            wrong_supported_reports=sum(
                r["resnet_screened_emitted"] and not r["baseline_correct"]
                for r in rows
                if r["cohort"] == "supported_breed"
            ),
            screened_non_dog_reports=sum(
                r["resnet_screened_emitted"] for r in rows if not r["live_dog_present"]
            ),
            multi_dog_individual_scopes=sum(
                r["screen"]["proposed_scope"] == "individual"
                for r in rows
                if r["expected_dog_count"] == "multiple"
            ),
            valid_calls=sum("error" not in r for r in v["rows"]),
            planned_calls=26,
            no_image_accepted=v["rows"][-1]["screen"]["accepted"],
            prevented_resnet_non_dog_reports=sum(
                r["resnet_baseline_emitted"] and not r["resnet_screened_emitted"]
                for r in rows
                if not r["live_dog_present"]
            ),
        )
        summary["advance_criteria_met"] = (
            summary["non_dog_accepts"] == 0
            and summary["live_dog_accepts"] >= 16
            and summary["supported_reports"] >= 6
            and summary["wrong_supported_reports"] / max(summary["supported_reports"], 1) <= 0.1
            and summary["multi_dog_individual_scopes"] == 0
            and summary["valid_calls"] == 26
            and not summary["no_image_accepted"]
        )
        out.update(vision_sha256=sha(DIRECTORY / "vision-results.json"), vision_summary=summary)
    else:
        assert not (DIRECTORY / "vision-results.json").exists()
        out["decision"] = (
            "No observed rejection failure under the registered trigger; stop without vision inference."
        )
    with httpx.Client(trust_env=False, timeout=10) as client:
        out["app_after"] = check_idle(client)
    write(DIRECTORY / "verification.json", out, exclusive=True)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "agreement", "vision", "verify"])
    args = parser.parse_args()
    {"prepare": prepare, "agreement": agreement, "vision": vision, "verify": verify}[args.phase]()
