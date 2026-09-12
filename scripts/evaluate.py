"""Fixed preselected cases, once per method. No filtering on outcomes."""

import hashlib
import json
import platform
import time
from statistics import mean

from breedframe.agent import Agent, successful
from breedframe.classifier import Classifier
from breedframe.controller import Controller
from breedframe.config import ROOT
from breedframe.metrics import MemorySampler
from breedframe.store import Store


def evaluate():
    manifest_path = ROOT / "docs/evidence/evaluation-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    store = Store(ROOT / "data/evaluation-cases")
    classifier = Classifier()
    agent = Agent(store, Controller(), classifier)
    rows = []
    with MemorySampler() as memory:
        for i, fixture in enumerate(manifest["cases"]):
            raw = (ROOT / fixture["path"]).read_bytes()
            case = store.create(raw)
            row = dict(
                id=fixture["id"],
                label=fixture["label"],
                group=fixture["group"],
                non_dog=fixture.get("non_dog", False),
                input_sha256=hashlib.sha256(raw).hexdigest(),
                order=["baseline", "agent"] if i % 2 == 0 else ["agent", "baseline"],
            )
            for method in row["order"]:
                started = time.monotonic()
                if method == "baseline":
                    try:
                        row[method] = dict(
                            result=classifier.classify(store.photo_path(case, "photo-1")), status="complete"
                        )
                    except Exception as exc:
                        row[method] = dict(status="failed", error=str(exc))
                else:
                    agent.run(case)
                    row[method] = dict(
                        status=case["status"],
                        report=case["report"],
                        request=case["request"],
                        attempts=case["attempts"]["photo-1"],
                        tool_calls=sum(e["kind"] == "tool" for e in case["events"]),
                        tool_errors=sum(e["status"] == "error" for e in case["events"]),
                        last_candidates=successful(case, "classify_breed")[-1]["output"]["candidates"]
                        if successful(case, "classify_breed")
                        else [],
                        events=case["events"],
                    )
                row[method]["seconds"] = round(time.monotonic() - started, 3)
            rows.append(row)
            print(
                f"{fixture['id']}: baseline {row['baseline']['seconds']}s, agent {row['agent']['status']} {row['agent']['seconds']}s",
                flush=True,
            )
    classifier.close()
    labeled = [r for r in rows if r["label"]]

    def candidates(r, method):
        if method == "baseline":
            return r[method].get("result", {}).get("candidates", [])
        return (r[method]["report"] or {}).get("candidates", [])

    summary = {}
    for method in ("baseline", "agent"):
        summary[method] = dict(
            total_cases=len(rows),
            labeled_denominator=len(labeled),
            top1_correct=sum(
                bool(candidates(r, method)) and candidates(r, method)[0]["label"] == r["label"]
                for r in labeled
            ),
            top5_correct=sum(r["label"] in [c["label"] for c in candidates(r, method)] for r in labeled),
            mean_seconds=round(mean(r[method]["seconds"] for r in rows), 3),
            incomplete_cases=sum(r[method]["status"] != "complete" for r in rows),
            abstentions=sum(not candidates(r, method) for r in rows),
            non_dog_breed_reports=sum(r["non_dog"] and bool(candidates(r, method)) for r in rows),
        )
    summary["agent"].update(
        requests=sum(r["agent"]["status"] == "awaiting_photo" for r in rows),
        mean_tool_calls=mean(r["agent"]["tool_calls"] for r in rows),
        errors=sum(r["agent"]["tool_errors"] for r in rows),
        unfinished_failures=sum(r["agent"]["status"] == "incomplete" for r in rows),
    )
    result = dict(
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        controller_source_sha256=hashlib.sha256((ROOT / "breedframe/controller.py").read_bytes()).hexdigest(),
        platform=platform.platform(),
        run_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        memory=memory.result(),
        summary=summary,
        rows=rows,
    )
    (ROOT / "docs/evidence/evaluation-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    evaluate()
