import json

from breedframe import evidence
from scripts.audit_classifier import MANIFEST, replay


def test_replay_preserves_cohorts_and_missing_followup_evidence():
    result = replay(json.loads(MANIFEST.read_text()))
    assert len(result["observations"]) == 20
    assert len(result["grid"]) == 150
    expected = {
        "individual_photos": 20,
        "initial_photos": 13,
        "paired_evidence": 7,
        "recorded_agent_policy": 13,
        "recorded_agent_forced": 7,
    }
    for row in result["grid"]:
        assert sum(g["denominator"] for g in row["cohorts"].values()) == expected[row["scenario"]]
        for group, counts in row["cohorts"].items():
            assert counts["eligible"] + counts["abstained"] == counts["denominator"]
            if group == "supported_breed":
                assert counts["correct"] + counts["incorrect"] == counts["eligible"]
        if row["scenario"] == "recorded_agent_forced" or (row["score"], row["margin"]) == (0.5, 0.15):
            assert all(not o["eligible"] for o in row["outcomes"])
    assert (evidence.MIN_SCORE, evidence.MIN_MARGIN) == (0.5, 0.15)


def test_relaxed_gate_retains_non_dog_and_unresolved_label_failures():
    result = replay(json.loads(MANIFEST.read_text()))
    row = next(
        r
        for r in result["grid"]
        if r["scenario"] == "individual_photos" and (r["score"], r["margin"]) == (0, 0)
    )
    outcomes = {o["id"]: o for o in row["outcomes"]}
    assert outcomes["statue-01"]["eligible"]
    assert outcomes["cat-01"]["eligible"]
    assert not outcomes["millie-02"]["eligible"]
    assert row["cohorts"]["supported_breed"] == {
        "denominator": 12,
        "eligible": 11,
        "abstained": 1,
        "correct": 8,
        "incorrect": 3,
    }
