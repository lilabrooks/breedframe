import threading

import pytest

from breedframe.agent import Agent
from breedframe.evidence import build_report, compare
from breedframe.policies import RulesController, decision_context
from breedframe.store import Store
from test_agent import FakeClassifier, ScriptedController, photo, textured_photo


def assessed(store, first=True):
    case = store.create(textured_photo())
    Agent(store, RulesController(), FakeClassifier()).run(case)
    if not first:
        store.add_photo(case, textured_photo(20))
        Agent(store, RulesController(), FakeClassifier()).run(case)
    return case


def test_two_photos_agree_without_averaging_scores(tmp_path):
    store = Store(tmp_path)
    case = assessed(store, first=False)
    report = case["report"]
    assert report["outcome"] == "visual_matches"
    assert report["comparison"]["relation"] == "agreement"
    candidate = report["candidates"][0]
    assert candidate["supporting_photo_ids"] == ["photo-1", "photo-2"]
    assert "score" not in candidate
    assert len(candidate["observations"]) == 2
    assert len(case["report_history"]) == 1
    assert store.load(case["id"])["report"] == report


def test_disagreement_blocks_report_even_with_high_scores(tmp_path):
    store = Store(tmp_path)
    case = assessed(store, first=False)
    rank = [e for e in case["events"] if e.get("tool") == "classify_breed"][-1]
    rank["output"]["candidates"][0].update(class_id=1, label="pug", score=0.99)
    comparison = compare(case)
    assert comparison["relation"] == "disagreement"
    assert comparison["report_eligible_ids"] == []
    with pytest.raises(ValueError):
        build_report(case, "visual_matches", rank["id"])
    assert build_report(case)["comparison"]["views"][0]["rankings"]


def test_weak_scores_and_poor_quality_stay_provisional(tmp_path):
    store = Store(tmp_path)
    case = assessed(store)
    rank = next(e for e in case["events"] if e.get("tool") == "classify_breed")
    rank["output"]["candidates"][0]["score"] = 0.08
    assert not compare(case)["report_eligible_ids"]
    rank["output"]["candidates"][0]["score"] = 0.9
    case["events"][0]["output"]["quality_flags"] = ["exposure"]
    assert not compare(case)["report_eligible_ids"]


def test_schema_removes_unsupported_reasons(tmp_path):
    store = Store(tmp_path)
    case = assessed(store)
    state, schema = decision_context(case, 3)
    assert "low_resolution" not in state["request_reasons"]
    assert "low_resolution" not in schema["$defs"]["RequestArgs"]["properties"]["reason"]["enum"]


def test_region_provenance_votes_and_duplicate_protection(tmp_path):
    store = Store(tmp_path)
    case = assessed(store)
    before = case["attempts"]["photo-1"]
    selection = dict(photo_id="photo-1", left=0.0, top=0.0, right=0.8, bottom=1.0)
    store.add_region(case, selection)
    assert case["attempts"]["photo-1"] == before
    assert not compare(case)["report_eligible_ids"]
    assert decision_context(case, 3)[0]["allowed_tools"] == ["classify_region"]
    Agent(store, RulesController(), FakeClassifier()).run(case)
    assert case["report"]["candidates"][0]["supporting_photo_ids"] == ["photo-1"]
    assert len(case["report"]["candidates"][0]["observations"]) == 2
    assert case["photos"][0]["regions"][0]["bounds"] == [0, 0, 256, 240]
    with pytest.raises(ValueError):
        store.add_region(case, selection)
    with pytest.raises(ValueError):
        store.region_path(case, "photo-1", "../../outside")


def test_finish_partial_and_retry_preserve_limits(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    Agent(store, RulesController(), FakeClassifier()).run(case)
    assert case["status"] == "awaiting_photo"
    store.finish_partial(case)
    assert case["report"]["outcome"] == "inconclusive"
    assert case["report"]["completed_by"] == "user"
    assert not decision_context(case, 2)[0]["request_reasons"]
    case["status"] = "incomplete"
    case["attempts"]["photo-1"] = 6
    with pytest.raises(ValueError, match="exhausted"):
        store.retry(case)


def test_cancel_before_tool_does_not_execute_it(tmp_path):
    store = Store(tmp_path)
    case = store.create(textured_photo())
    cancelled = threading.Event()

    class CancellingController(ScriptedController):
        def choose(self, *args):
            cancelled.set()
            return "inspect_image", {"photo_id": "photo-1"}, {}

    Agent(store, CancellingController([]), FakeClassifier()).run(case, cancelled=cancelled.is_set)
    assert case["status"] == "incomplete"
    assert "Cancelled" in case["stop_reason"]
    assert case["events"] == []
    assert case["attempts"]["photo-1"] == 1
    store.retry(case)
    assert case["attempts"]["photo-1"] == 1


def test_retry_does_not_reset_photo_deadline(tmp_path):
    store = Store(tmp_path)
    case = store.create(textured_photo())
    case["runs"] = [{"photo_id": "photo-1", "seconds": 240}]
    Agent(store, ScriptedController([]), FakeClassifier()).run(case)
    assert case["status"] == "incomplete"
    assert "deadline" in case["stop_reason"]
    assert case["attempts"]["photo-1"] == 0
