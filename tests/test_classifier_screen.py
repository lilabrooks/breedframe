from scripts.screen_classifier import summarize


def observation(cohort="supported_breed", correct=True, breed=True):
    return dict(cohort=cohort, correct=correct, native_top1_is_breed=breed, top1_score=0.99, margin=0.98)


def test_unsuitable_native_breed_prediction_blocks_screen():
    rows = [observation() for _ in range(6)] + [observation("non_dog", False, False)]
    assert summarize(rows, 0.5, 0.15)["meets_criteria"]
    rows.append(observation("multiple_dogs", False))
    result = summarize(rows, 0.5, 0.15)
    assert not result["meets_criteria"]
    assert result["cohorts"]["non_dog"]["reports"] == 0
    assert result["cohorts"]["multiple_dogs"]["reports"] == 1


def test_failures_stay_in_coverage_denominator_and_wrong_reports_in_error_rate():
    rows = [observation(), observation(correct=False)]
    result = summarize(rows, 0.5, 0.15)
    assert not result["meets_criteria"]
    assert result["cohorts"]["supported_breed"]["wrong"] == 1
    rows = [observation()] + [dict(cohort="supported_breed", error="timeout") for _ in range(2)]
    result = summarize(rows, 0.5, 0.15)
    assert not result["meets_criteria"]
    assert result["cohorts"]["supported_breed"] == dict(total=3, reports=1, correct=1, wrong=0, failures=2)
