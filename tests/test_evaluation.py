from scripts.evaluate_pairs import summarize


def test_abstentions_failures_and_improvements_keep_fixed_denominators():
    rows = []
    for i, (candidates, status, initial) in enumerate(
        [
            ([], "complete", True),
            ([{"label": "beagle"}], "complete", False),
            ([], "failed", False),
        ]
    ):
        row = dict(
            id=str(i),
            breed_accuracy_eligible=True,
            live_dog_present=True,
            kind="same_dog_pair",
            label="beagle",
        )
        for method in ("direct", "rules", "agent"):
            row[method] = dict(
                candidates=candidates,
                status=status,
                seconds=2,
                initial_correct=initial,
                initial_photo_classified=i != 2,
                supplied_followups=1 if i == 1 else 0,
                followup_photos_classified=1 if i == 1 else 0,
                requests=2 if i == 1 else 0,
            )
        rows.append(row)
    summary = summarize(rows)["agent"]
    assert summary["labeled_denominator"] == 3
    assert summary["correct_reports"] == 1
    assert summary["abstentions"] == 2
    assert summary["incomplete"] == 1
    assert summary["labeled_first_to_final_improvements"] == 1
    assert summary["labeled_first_to_final_regressions"] == 1

    assert summary["initial_photos_classified"] == 2
    assert summary["supplied_followups"] == summary["followup_photos_classified"] == 1
    assert summary["cases_requesting_followup"] == 1
    assert summary["requests"] == 2
