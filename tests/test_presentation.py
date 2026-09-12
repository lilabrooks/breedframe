import copy

from breedframe.presentation import describe_assessment


def case_with_rankings():
    return {
        "photos": [{"id": "photo-1"}],
        "events": [
            {
                "id": 1,
                "kind": "tool",
                "tool": "classify_breed",
                "status": "ok",
                "photo_id": "photo-1",
                "output": {
                    "candidates": [
                        {"class_id": 0, "label": "beagle", "score": 0.175},
                        {"class_id": 1, "label": "english_foxhound", "score": 0.112},
                    ],
                    "margin": 0.063,
                },
            }
        ],
        "report": {"outcome": "inconclusive", "candidates": []},
    }


def test_tentative_matches_show_recorded_percentages_without_changing_outcome():
    case = case_with_rankings()
    before = copy.deepcopy(case)
    summary = describe_assessment(case)
    assert summary["title"] == "Top visual match: Beagle"
    assert summary["detail"] == "Model score: 17.5%"
    assert summary["candidates"][1]["score_text"] == "11.2%"
    assert "tentative" in summary["context"]
    assert "not calibrated probabilities" in summary["score_note"]
    assert case == before


def test_unclassified_followup_does_not_reuse_an_earlier_photos_match():
    case = case_with_rankings()
    case["photos"].append({"id": "photo-2"})
    summary = describe_assessment(case)
    assert summary["candidates"] == []
    assert summary["source"] is None
    assert "current photo has no classification result" in summary["detail"]


def test_conflicting_region_is_named_and_never_averaged_with_whole_photo():
    case = case_with_rankings()
    region = copy.deepcopy(case["events"][0])
    region.update(id=2, tool="classify_region", input={"region_id": "region-1"})
    region["output"]["candidates"][0].update(class_id=2, label="golden_retriever", score=0.233)
    case["events"].append(region)
    summary = describe_assessment(case)
    assert summary["title"] == "Top visual match: Golden retriever"
    assert summary["detail"] == "Model score: 23.3%"
    assert summary["source"] == "photo-1 · region-1 · event 2"
    assert "Different views suggest different breeds" in summary["context"]


def test_failed_ranking_is_not_presented_as_a_match():
    case = case_with_rankings()
    case["events"][0]["status"] = "error"
    assert describe_assessment(case)["candidates"] == []


def test_ties_and_incomplete_labels_are_explicit():
    case = case_with_rankings()
    candidates = case["events"][0]["output"]["candidates"]
    candidates[1]["score"] = candidates[0]["score"]
    candidates[0]["unresolved_label"] = True
    summary = describe_assessment(case)
    assert summary["title"] == "Joint top visual matches: Beagle (label incomplete), English foxhound"
