# Evidence comparison, version 2

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

The report-count comparison cannot isolate controller value: direct exposes an ungated ranking, while the 0.5 score gate blocks every recorded v2 ViT output for rules and Qwen3. The largest score is 0.222815. Qwen3 also skipped each supplied second photograph, an observed evidence-use failure under this configuration. The deterministic policy used the follow-ups and abstained. No threshold or prompt was changed between the development and reserved paired runs.

## What changed in the application

A case compares every successful whole-photo and region classification. Each view retains its photo ID, event ID, raw scores, quality flags and optional region ID. Candidate ordering uses distinct-photo leading votes, then appearances in the top five, then summed best ranks. Scores are never averaged. Multiple regions from one photo would share that photo's vote; the current UI permits only one region per photo.

An eligible visual report needs an inspected current photo, a successful current result with a resolved leading label, score at least 0.5 and margin at least 0.15, no relevant quality flags, and no conflicting leading classes across the recorded results. These thresholds were already ambiguity warnings in the prototype; v2 makes them reporting conditions. They are uncalibrated and proved too restrictive to produce any breed reports in this sample. An inconclusive assessment still exposes all observed rankings. Agreement is classifier consistency, not proof of dog presence or breed identity.

The region editor accepts a drawn rectangle or percentage bounds. The store validates those bounds against the normalized source, records both fractional and pixel coordinates, saves the actual region, and passes that file to the classifier worker. Its result returns through a persisted event into the comparison and browser/export. The application requires a region attempt after explicit selection. This is a user-directed action, not model-generated localization.

Completed cases accept another photo while archiving their prior report. A user can close a paused or interrupted case with a partial assessment, explicitly attributed to the user. Cancellation retains observations after the current bounded call returns. Retry and region selection retain the photo's consumed actions and cumulative time; only a new photo gets a fresh budget. Inactive cases can be deleted. The readable Markdown export and JSON execution record retain evidence references.

## Fixed paired protocol

The [photo manifest](evidence/photo-set-v2/manifest.json) was frozen during curation before inference. It contains 20 photos in 13 cases: six development cases and seven reserved cases, grouped by identity to avoid crossing the split. Six dog pairs have supported classifier labels, one pair is outside the label space, two cases contain multiple dogs, three are non-dog controls, and one is described as mixed breed without verified ancestry.

`scripts/evaluate_pairs.py` compares direct classification, deterministic rules and Qwen3. Both orchestration policies receive the same numerical tools, reporting conditions, three-photo limit and six-attempt budget. Ground-truth labels, source captions and filenames are excluded from controller context. Method order rotates by case. The classifier and controller are warmed on the separate demo before timing; photo acquisition and user response time are excluded.

In `policy` mode each policy starts with the same first photo. A requested follow-up receives the next prelisted photo, if available. A further request is retained, counted as unavailable and explicitly closed with a simulated user partial report. Direct classification uses one initial photo. In `forced_pair` mode all policies receive the second photo even if they would have stopped, and that extra acquisition is counted. Receiving a photo does not force the model to classify it.

All cases affect timing, completion, request burden, errors and abstention. Only supported labeled pairs affect breed-report accuracy, with abstentions and failures kept in that denominator. Improvements and regressions compare initial to final *reports*, not provisional tool scores. Non-dog, unsupported-breed and multi-dog reports have separate counters. Mixed-breed imagery has no accuracy target or validated ancestry metric. Every method's events remain available, including classifications the policy declines to report.

## Results with policy-selected follow-ups

The direct column below contains ungated classifier outputs; rules and Qwen3 contain gated reports. Applying the same numerical gate to cached direct initial-photo outputs yields 0/2 correct development reports (0/6 reports across all cases) and 0/4 correct reserved reports (0/7 across all cases). This counterfactual has no new workflow or latency measurement. The zero gated outcomes are forced by the observed score range, so these report columns cannot attribute the difference to orchestration. [Reanalysis](evidence/review-02-reconciliation/results.json).

| Split and measure | Direct | Rules | Qwen3 |
|---|---:|---:|---:|
| Development: correct reports / eligible dogs | 1/2 | 0/2 | 0/2 |
| Development: abstaining cases | 0/6 | 6/6 | 6/6 |
| Development: follow-ups supplied | 0 | 3 | 0 |
| Development: requests / unavailable requests | 0 / 0 | 9 / 6 | 0 / 0 |
| Development: mean seconds | 0.113 | 0.211 | 10.098 |
| Reserved: correct reports / eligible dogs | 3/4 | 0/4 | 0/4 |
| Reserved: abstaining cases | 0/7 | 7/7 | 7/7 |
| Reserved: follow-ups supplied | 0 | 4 | 0 |
| Reserved: requests / unavailable requests | 0 / 0 | 11 / 7 | 0 / 0 |
| Reserved: mean seconds | 0.153 | 0.276 | 10.589 |

All methods reached completion after the specified user-style closures. There were no controller errors, tool errors or failed operations. Qwen3 chose inspect → classify → finish inconclusive on every initial photo. Rules classified each available photo and requested more evidence, then received partial closure when the fixed corpus ran out.

Direct classification reported breeds for both development non-dogs and the reserved horse, for Bo's unsupported breed, and for both multi-dog scenes without selecting a target. Rules and Qwen3 reported none. Because neither produced *any* breed reports, this is evidence of abstention behavior, not reliable rejection of non-dogs. Incorrect reports among labeled reports were 1/2 direct in development and 1/4 reserved; the corresponding fraction for rules and Qwen3 is undefined, since their labeled report counts are zero.

[Development raw results](evidence/paired-development-v2.json) · [Reserved raw results](evidence/paired-reserved-policy-v2.json).

## Supplying both views

The forced run includes only the seven prelisted pairs: three development and four reserved. Each policy received all second photos, including where it made no request. Direct classification's final ranking uses the second image; the first remains recorded.

| Split and measure | Direct | Rules | Qwen3 |
|---|---:|---:|---:|
| Development: correct final reports | 1/2 | 0/2 | 0/2 |
| Development: mean seconds | 0.350 | 0.400 | 25.923 |
| Reserved: correct final reports | 3/4 | 0/4 | 0/4 |
| Reserved: mean seconds | 0.203 | 0.244 | 28.112 |

Conan's direct prediction improved from keeshond to malinois. Millie's regressed from english_springer to the unresolved published label shih. One improvement and one regression leave reserved accuracy unchanged. Neither labeled development report changed correctness.

Rules recorded leading-class disagreements in two development and two reserved pairs. Qwen3 inspected each second image, then finished inconclusive without classifying it. Its comparison consequently has only one ranked photograph. The raw direct-method `relation` field is `no_ranking` because direct results are stored outside agent tool events; direct first-to-final changes above are computed from its actual `initial_candidates` and `candidates`.

All runs retained every case, without errors or additional samples. These results do not show that a model controller makes effective use of follow-up photos. [Development forced results](evidence/paired-development-forced-v2.json) · [Reserved forced results](evidence/paired-reserved-forced-v2.json).

## Exploratory region pilot

Three development images were fixed for this pilot before any crop inference: Barney's small rear view, Buddy's close view and Bo's heavily occluded view. Whole-photo predictions had already been seen, so this is exploratory development evidence. Bounds were selected from the images and were never adjusted after crop results. The [crop manifest](evidence/crop-pilot-manifest.json) records that sequence.

| Image | Whole-photo top class | Region top class | Supported target |
|---|---|---|---|
| Barney 01 | scotch_terrier | schipperke | scotch_terrier |
| Buddy 01 | weimaraner | weimaraner | labrador_retriever |
| Bo 01 | pug | pug | Outside classifier classes |

Raw top-1 correctness fell from 1/2 to 0/2 because Barney's label changed. All three region calls completed, and no breed report was issued. Two crops were below the classifier's 224-pixel input size; Buddy's retained about 83% of the frame area, and Bo had no supported target. The pilot did not include a multiple-dog scene or a large foreground-person removal. It supports only these recorded transformations, not a general conclusion about cropping or automatic localization. Human annotation time is excluded from the recorded run times. [Crop results, bounds, hashes and actual events](evidence/crop-pilot-results.json).

## Version and evidence limits

All four paired result files report unchanged source hashes throughout their run. Later code corrections require an attempt on an explicitly selected region and preserve cumulative time across retries. Neither changes the paired trajectories, which used no regions or retries. Their original source hashes are kept intact; crop and browser records exercise the later code. The controller prompt and thresholds were not tuned in response to reserved results.

The sample is small and heavily drawn from US public archives. Source captions support identity and breed labels but do not provide genetic or pedigree verification. Training overlap is unknown. Several same-dog pairs span months or years, and Buddy's puppy/adult difference confounds an immediate-retake interpretation. There are no owner-supplied same-session blur/sharp or exposure-recovery pairs. “Reserved” means withheld from this project's development, not independent of model training.

The stricter reporting behavior also changed the demo: the latest tiny-beagle run ended inconclusive instead of requesting a photo. The original request/resume trace remains historical evidence. This regression and the missing second-photo classification belong in the prototype's measured limitations, alongside the working persistence, comparison and recovery mechanisms.

## Historical integration verification

This section records the v2 interface and checks at the time of the comparison. See [Using Scout](usage.md) for the current workspace and [current screenshots](screenshots/README.md#current-scout-interface). The original captures and exported assessment below remain unchanged.

`make check` passed 25 tests, Ruff and JavaScript syntax checks. The public demo exercised real Qwen3 and ViT calls through the browser: completed-case continuation, an explicitly selected region, persisted disagreement, a readable download, cancellation with observations retained, and user partial completion. The CLI demo also completed both stages and explicitly recorded that its follow-up came from the demo user.

[Browser comparison trace](evidence/browser-comparison-v2.json) · [Readable exported assessment](evidence/browser-assessment-v2.md) · [Cancellation trace](evidence/browser-cancelled-v2.json) · [Partial completion](evidence/browser-partial-v2.json) · [CLI trace](evidence/cli-demo-v2.json) · [Verification record](evidence/verification-v2.json).

Desktop and 390-pixel-wide mobile layouts were visually inspected, with no horizontal overflow or duplicate IDs observed. [Historical v2 desktop screenshot](screenshots/comparison-v2.png) · [Historical v2 mobile screenshot](screenshots/comparison-mobile-v2.png). These screenshots contain the beagle photograph and its resized/cropped derivatives by sannse, CC BY-SA 3.0, attributed in the README and the UI. Delete and retry paths were covered by API/unit tests; no live user case was deleted for verification.
