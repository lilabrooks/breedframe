"""A fixed, paired next-action probe; no classifier calls or app policy edits."""

import argparse
import copy
import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

import httpx

from breedframe import controller as controller_module
from breedframe.config import CONTROLLER_MODELS, OLLAMA_URL, ROOT
from breedframe.controller import Controller
from breedframe.model_identity import verify_controller
from breedframe.policies import decision_context

SOURCE = ROOT / "docs/evidence/paired-development-forced-v2.json"
CASE_IDS = ("barney", "buddy", "bo")
MODELS = ("qwen3:4b", "qwen3.5:4b")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def clearer_context(case, remaining):
    original, schema = decision_context(case, remaining)
    current = next(
        v for v in original["comparison"]["views"] if v["photo_id"] == original["current_photo_id"]
    )
    # Existing nested comparison stays intact, including its blockers.
    return dict(
        current_photo_classified=bool(current["rankings"]),
        blockers=copy.deepcopy(original["comparison"]["blockers"]),
        **original,
    ), schema


def fixtures():
    rows = {r["id"]: r for r in json.loads(SOURCE.read_text())["rows"]}
    cases = {}
    for name in CASE_IDS:
        events = rows[name]["agent"]["events"]
        index = next(
            i
            for i, e in enumerate(events)
            if e.get("tool") == "inspect_image" and e.get("photo_id") == "photo-2"
        )
        assert events[index]["status"] == "ok"
        case = dict(
            photos=[dict(id="photo-1"), dict(id="photo-2")], events=copy.deepcopy(events[: index + 1])
        )
        original, schema = decision_context(case, 5)
        clearer, clearer_schema = clearer_context(case, 5)
        assert clearer_schema == schema and not clearer["current_photo_classified"]
        assert {
            k: v for k, v in clearer.items() if k not in {"blockers", "current_photo_classified"}
        } == original
        assert set(original["allowed_tools"]) == {
            "classify_breed",
            "finish_assessment",
            "request_another_photo",
        }
        assert not original["comparison"]["report_eligible_ids"]
        assert not original["comparison"]["views"][-1]["rankings"]
        cases[name] = dict(
            case=case,
            original=original,
            clearer=clearer,
            schema=schema,
            historical_next_action=events[index + 1]["tool"],
        )
    return cases


def planned_schedule():
    # Model sessions are sequential. Reverse AB/BA order for the second model.
    return [
        dict(model=model, case_id=name, variant=variant)
        for model_index, model in enumerate(MODELS)
        for index, name in enumerate(CASE_IDS)
        for variant in (
            ("original", "clearer") if (index + model_index) % 2 == 0 else ("clearer", "original")
        )
    ]


def legal_choice(tool, args, state):
    # Decision.model_validate_json already enforces the static contract in choose().
    # These are the additional constraints in the frozen three-action schema.
    if tool not in state["allowed_tools"]:
        return False
    if tool == "classify_breed":
        return args == {"photo_id": state["current_photo_id"]}
    if tool == "finish_assessment":
        return args == {"outcome": "inconclusive", "selected_result_id": None}
    return tool == "request_another_photo" and args["reason"] in state["request_reasons"]


def summary(rows):
    counts, transitions = [], []
    for model in MODELS:
        for variant in ("original", "clearer"):
            selected = [r for r in rows if r["model"] == model and r["variant"] == variant]
            counts.append(
                dict(
                    model=model,
                    variant=variant,
                    scheduled=3,
                    attempted=len(selected),
                    classify_choices=sum(
                        r.get("tool") == "classify_breed" and r.get("legal", False) for r in selected
                    ),
                    requests=sum(
                        r.get("tool") == "request_another_photo" and r.get("legal", False) for r in selected
                    ),
                    finishes=sum(
                        r.get("tool") == "finish_assessment" and r.get("legal", False) for r in selected
                    ),
                    errors=sum("error" in r for r in selected),
                    invalid=sum(r.get("legal") is False for r in selected),
                )
            )
        for name in CASE_IDS:
            pair = {r["variant"]: r for r in rows if r["model"] == model and r["case_id"] == name}
            if len(pair) == 2:
                transitions.append(
                    dict(
                        model=model,
                        case_id=name,
                        original=pair["original"].get("tool", "error"),
                        clearer=pair["clearer"].get("tool", "error"),
                        both_legal=all(r.get("legal", False) for r in pair.values()),
                    )
                )
    return dict(counts=counts, paired_transitions=transitions)


def prepare(directory):
    directory.mkdir(parents=True, exist_ok=False)
    cases = fixtures()
    write(directory / "fixtures.json", cases)
    sources = [SOURCE, Path(__file__).resolve(), *sorted((ROOT / "breedframe").glob("*.py"))]
    protocol = dict(
        phase="development next-action probe; not a workflow or accuracy evaluation",
        models={m: CONTROLLER_MODELS[m] for m in MODELS},
        schedule=planned_schedule(),
        remaining_actions=5,
        timeout_per_decision_seconds=45,
        intervention="Prepend current_photo_classified and a copy of comparison.blockers at top level. Preserve every original state field, nested comparison, schema, system prompt and tool description.",
        fixed="Original ViT observations, report gate 0.5/0.15, original Qwen3 history for both models, no images, think=false, temperature=0, seed=42, context=8192, output=500; same Controller.choose path and runtime.",
        primary="Legal classify_breed choices over three scheduled current-photo opportunities per model and context; paired transitions are primary comparisons.",
        secondary="Request/finish choices, errors, invalid responses. Record latency and load duration for traceability only; no speed ranking.",
        interpretation="An increase is evidence for this bundled context change at these three exposed states. No change rejects only this intervention. If fresh original choices differ from history, use contemporaneous paired differences and flag baseline instability.",
        advance="Only if all 12 decisions are valid, at least five of six clearer decisions choose classification, and classification choices exceed the contemporaneous original count: advance to a separate bounded workflow study; never auto-promote app changes.",
        stop="Exactly 12 scheduled decisions, one per cell; no retry, prompt iteration, extra seeds or sample extension. Preserve errors. Abort remaining cells on runtime/digest/source drift, unrelated resident models, or concurrent app work.",
        resource="Sequential requests; unload each experiment model after its six decisions. No warmup generation, classifier inference, memory sampling, or downstream action execution.",
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in sources},
        fixtures_sha256=sha(directory / "fixtures.json"),
    )
    write(directory / "protocol.json", protocol)
    print(f"Frozen {len(protocol['schedule'])} decisions at {directory}")


def run(directory):
    protocol = json.loads((directory / "protocol.json").read_text())
    cases = json.loads((directory / "fixtures.json").read_text())
    target = directory / "results.json"
    with target.open("x") as f:
        json.dump(dict(complete=False, rows=[]), f)
    result = dict(complete=False, rows=[], protocol_sha256=sha(directory / "protocol.json"))
    base_client = httpx.Client
    recorded_response = {}

    class RecordingClient(base_client):
        def post(self, url, *args, **kwargs):
            response = super().post(url, *args, **kwargs)
            if url == OLLAMA_URL + "/api/chat":
                recorded_response.update(status_code=response.status_code, text=response.text)
            return response

    loaded_by_probe = None
    try:
        assert sha(directory / "fixtures.json") == protocol["fixtures_sha256"]
        assert all(sha(ROOT / p) == h for p, h in protocol["source_hashes"].items())
        identities = {model: verify_controller(model) for model in MODELS}
        with base_client(timeout=15, trust_env=False) as client:
            result["runtime"] = client.get(OLLAMA_URL + "/api/version").json()
            assert result["runtime"] == {"version": "0.34.0"}
            result["resident_before"] = client.get(OLLAMA_URL + "/api/ps").json()
            if result["resident_before"]["models"]:
                raise RuntimeError("Begin with no loaded model; do not unload someone else's work.")
        result["identities"] = identities
        for index, cell in enumerate(protocol["schedule"]):
            with base_client(timeout=15, trust_env=False) as client:
                health = client.get("http://127.0.0.1:8765/api/health")
                health.raise_for_status()
                if health.json()["busy"]:
                    raise RuntimeError("Concurrent application work; stop the probe.")
                verify_controller(cell["model"], client)
                residents = client.get(OLLAMA_URL + "/api/ps").json()["models"]
                if any(m["name"] != cell["model"] for m in residents):
                    raise RuntimeError("Unrelated model resident; stop the probe.")
            assert all(sha(ROOT / p) == h for p, h in protocol["source_hashes"].items())
            fixture = cases[cell["case_id"]]
            row = dict(**cell, schedule_index=index, started_at=time.time())
            chosen = Controller(cell["model"])
            recorded_response.clear()
            loaded_by_probe = cell["model"]
            started = time.monotonic()
            try:
                context = decision_context if cell["variant"] == "original" else clearer_context
                with (
                    patch.object(controller_module, "decision_context", context),
                    patch.object(controller_module.httpx, "Client", RecordingClient),
                ):
                    tool, args, metrics = chosen.choose(copy.deepcopy(fixture["case"]), 5, timeout=45)
                row.update(
                    tool=tool,
                    arguments=args,
                    metrics=metrics,
                    legal=legal_choice(tool, args, fixture[cell["variant"]]),
                )
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                row.update(
                    seconds=time.monotonic() - started,
                    request=chosen.last_request,
                    response=copy.deepcopy(recorded_response),
                )
                result["rows"].append(row)
                result["summary"] = summary(result["rows"])
                write(target, result)
            if row["request"]:
                expected_message = (
                    json.dumps(fixture[cell["variant"]]) + "\nReturn one JSON decision. /no_think"
                )
                assert row["request"]["messages"][1]["content"] == expected_message
                assert row["request"]["format"] == fixture["schema"]
            print(
                cell["model"], cell["case_id"], cell["variant"], row.get("tool", row.get("error")), flush=True
            )
            if index in {5, 11}:
                with base_client(timeout=15, trust_env=False) as client:
                    response = client.post(
                        OLLAMA_URL + "/api/generate", json=dict(model=loaded_by_probe, keep_alive=0)
                    )
                    response.raise_for_status()
                loaded_by_probe = None
        result["complete"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if loaded_by_probe:
            with base_client(timeout=15, trust_env=False) as client:
                client.post(OLLAMA_URL + "/api/generate", json=dict(model=loaded_by_probe, keep_alive=0))
        result["source_hashes_unchanged"] = all(
            sha(ROOT / p) == h for p, h in protocol["source_hashes"].items()
        )
        result["summary"] = summary(result["rows"])
        write(target, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "run"])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    (prepare if args.stage == "prepare" else run)(args.output)
