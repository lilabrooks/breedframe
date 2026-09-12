# Qwen3.5 4B controller comparison

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

**Keep Qwen3 4B as the default.** Qwen3.5 4B Q4_K_M completed the fixed comparison without errors but produced no useful evidence-use or reporting improvement. It requested no follow-ups in normal policy mode, skipped classification of all seven supplied second photographs, and asked for a third photo in five forced-pair cases. The candidate remains an explicit local option; it was not promoted.

The subsequent classifier audit and screen are complete. The [methods review response](review-02-response.md) now governs the next steps. The unchanged 0.5 score gate prevented breed reports on the recorded outputs, so this controller comparison cannot isolate an accuracy advantage from report counts or establish that either model is intrinsically unable to assess breeds. Its evidence-use and request observations remain measurements of the specific configurations exercised.

## What stayed fixed

The application SYSTEM prompt, action schema, image normalization, ViT inference and reporting policy are byte-identical to the archived baseline. Both models receive numerical observations without photographs, filenames or source captions. Budgets remain six attempts and 240 seconds per photo, with three photos per case. The ViT revision is `160ee8611d7974c550bbaaa108378fbe8be9ef9c`.

The candidate digest is `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`. The baseline digest is `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Both run in Ollama 0.34.0 on the same M4 Air. [Installed package identities](evidence/controller-comparison/installed-models.json).

Temperature 0, seed 42, context 8192, output limit 500 and `think=false` are unchanged. The candidate package sets presence penalty 1.5, whereas the baseline leaves it at Ollama's default zero. Before any candidate inference, both requests were made explicit with presence penalty 0, repeat penalty 1, top-k 20 and top-p 0.95, matching the baseline's effective settings. Model-native templates and stop tokens remain model-specific and are archived. [Ollama 0.34.0 defaults](https://raw.githubusercontent.com/ollama/ollama/v0.34.0/api/types.go) · [Baseline package](evidence/controller-comparison/qwen3-4b-package.json) · [Candidate package](evidence/controller-comparison/qwen3.5-4b-package.json).

The baseline source had no commit, so it was archived with per-file hashes and its existing raw results before edits. Candidate changes add explicit selection, digest checks, returned-model validation, request metadata, correct memory attribution and additional evidence-use counters. [Baseline preservation](evidence/controller-comparison/baseline-preservation.json) · [Candidate freeze](evidence/controller-comparison/candidate-freeze.json) · [Unchanged policy check](evidence/controller-comparison/unchanged-policy-check.json).

## Protocol and limits

The predeclared schedule contains six development and seven reserved cases in normal policy mode, plus three development and four reserved pairs in a separate forced two-photo mode. Each candidate run includes direct-classifier and deterministic-rules controls, with rotating method order and sequential inference. Models are warmed on the separate demo before timing; memory sampling is excluded from these timings, as in the preserved baseline. [Fixed protocol](evidence/controller-comparison/protocol.json).

Development probes checked compatibility before the candidate was frozen. No prompt, threshold, tool or photograph was adjusted in response to candidate predictions. The reserved cases were already observed with the baseline; this is a fixed comparison set, not a fresh blind evaluation. Every scheduled case, error and abstention stays in its original denominator. More photo requests alone do not establish useful evidence acquisition. The old and new controller timings come from separate sequential sessions, not interleaved repeated trials; background load and thermal conditions were not controlled. Treat the numbers as observed run costs, not a stable model-speed ranking.

The score gate limits interpretation: the highest leading ViT score observed in the earlier paired runs was 0.223, below the 0.5 minimum for a breed report. A text-controller change cannot make those same outputs eligible. Evidence use, supported decisions, cost and failure behavior therefore matter alongside the unchanged report metrics. This comparison cannot isolate the classifier's calibration or the value of adding vision.

## Development results

| Measure | Preserved Qwen3 4B | Qwen3.5 4B |
|---|---:|---:|
| Policy mode: correct reports / eligible dogs | 0/2 | 0/2 |
| Policy mode: cases requesting follow-up | 0/6 | 0/6 |
| Policy mode: abstentions | 6/6 | 6/6 |
| Policy mode: mean seconds | 10.098 | 10.473 |
| Forced pairs: second photos classified / supplied | 0/3 | 0/3 |
| Forced pairs: requests after the second photo | 0 | 3 |
| Forced pairs: mean seconds | 25.923 | 23.307 |

In policy mode, Qwen3.5 inspected, classified and finished inconclusive on every initial development image. In forced-pair mode it inspected each second photo, skipped classification, then requested another photo with `insufficient_evidence`. Those three requests exhausted the fixed photo supply and received explicit user-style partial closure. The request reasons passed validation, but the extra requests did not use the supplied evidence or improve a report.

The direct and rules controls reproduced all recorded development candidate rankings exactly in policy mode. Direct classification reported the correct breed in 1/2 labeled cases; rules classified all three available follow-ups and abstained on every case. All development methods completed under the stated closure rule without tool or controller errors. [Policy run](evidence/controller-comparison/development-policy.json) · [Forced-pair run](evidence/controller-comparison/development-forced.json).

## Reserved results

| Policy-mode measure | Direct control | Rules control | Preserved Qwen3 4B | Qwen3.5 4B |
|---|---:|---:|---:|---:|
| Correct reports / eligible dogs | 3/4 | 0/4 | 0/4 | 0/4 |
| Cases with no breed report | 0/7 | 7/7 | 7/7 | 7/7 |
| Initial photos classified | 7/7 | 7/7 | 7/7 | 7/7 |
| Follow-ups supplied / classified | 0/0 | 4/4 | 0/0 | 0/0 |
| Mean seconds | 0.137 | 0.222 | 10.589 | 16.250 |

Both text controllers completed the initial-photo cases inconclusive without a request. The rules control used all four available follow-ups, then received seven user-style closures for requests beyond the fixture supply. No method had a tool error, controller error or failed operation. The direct control reported a breed for the horse and for the multi-dog scene without selection; the other methods issued no breed reports at all. Zero false reports with zero report coverage is not evidence of reliable dog detection. [Reserved policy run](evidence/controller-comparison/reserved-policy.json) · [Preserved baseline](evidence/paired-reserved-policy-v2.json).

### Reserved forced pairs

| Measure | Preserved Qwen3 4B | Qwen3.5 4B | Current rules control |
|---|---:|---:|---:|
| Correct final reports / eligible dogs | 0/4 | 0/4 | 0/4 |
| Second photos classified / supplied | 0/4 | 0/4 | 4/4 |
| Requests after the second photo | 0 | 2 | 4 |
| Mean seconds | 28.112 | 31.331 | 0.489 |

Qwen3.5 requested a third photo for Sully and Conan after inspecting but not classifying their second photos. Champ and Millie ended inconclusive after the same inspection-only continuation. Both third-photo requests received explicit partial closure. This reproduces the original evidence-use gap and adds request burden in two cases. [Reserved forced run](evidence/controller-comparison/reserved-forced.json).

The direct control again ended at 3/4 correct: Conan improved and Millie regressed. Rules classified every supplied second image, recorded two disagreements and abstained. Neither text controller improved a breed report in any split or mode.

## Verification and decision

All four candidate runs completed with frozen source hashes unchanged. The direct and rules controls reproduced their earlier candidate rankings exactly in every case across all four runs. All 74 candidate tool events recorded the pinned Qwen3.5 identity, matching returned name, zero image inputs and thinking disabled. There were no tool or controller errors. [Run and control verification](evidence/controller-comparison/comparison-verification.json).

`make check` passed 29 tests, Ruff and JavaScript syntax checks. New tests cover identical text-only payloads across model options, digest mismatch before inference, returned-model mismatch, unsupported-model rejection and evidence-use metric denominators. The public development probes independently traced model selection through startup, request, actual tool output, saved case and report. The candidate download command was exercised against the cached pinned model.

The candidate does not meet the plan's promotion condition. Its normal-mode decisions were unchanged, it did not classify any supplied follow-up, and its additional forced-mode requests did not improve reports. Recorded reserved latency and the separate process-footprint observation also give no reason to prefer it. The default remains Qwen3 4B; both pinned packages and both source snapshots remain available. A new controller or larger model trial would need a specific unresolved question beyond this result.

## Separate memory probes

Both probes unload the controller first, then warm on the same demo and run Barney's first development photograph. They save the actual text-only requests, verified model identity, real tool events and reloaded case. This is one resource probe per model, with cold warmup reported separately from the main warm comparison.

| Observed counter | Qwen3 4B | Qwen3.5 4B |
|---|---:|---:|
| Cold warmup, seconds | 9.944 | 10.598 |
| Peak summed process RSS, GiB | 4.063 | 4.376 |
| Peak summed macOS process footprint, GiB | 2.061 | 5.646 |
| Ollama-reported residency at probe end, GiB | 3.592 | 3.144 |

RSS and process footprint sample the probe, classifier child, project-local Ollama and its children every 200 ms, deduplicated by PID. These counters account for shared and Metal allocations differently; they are neither additive nor unique whole-machine memory deltas. The candidate's lower Ollama residency does not establish lower total memory use. One short probe does not measure a sustained peak or prove a memory leak. Both probes completed without sampling errors. [Baseline probe](evidence/controller-comparison/baseline-probe.json) · [Candidate probe](evidence/controller-comparison/candidate-probe.json).

## Local use

After normal project setup, explicitly install and select the candidate with:

```sh
sh scripts/download_controller.sh qwen3.5:4b
BREEDFRAME_CONTROLLER=qwen3.5:4b sh scripts/start.sh
```

The downloader uses a temporary local server on port 11435, checks the reviewed digest, then exits. The application uses the existing offline inference policy. Stop a running app before starting another. Omit the environment variable to use Qwen3 4B. Unknown, missing or changed model identities fail visibly; the application does not substitute another controller.

To reproduce a development comparison with a new output path:

```sh
BREEDFRAME_CONTROLLER=qwen3.5:4b PYTHONPATH=. .venv/bin/python scripts/evaluate_pairs.py --split development --mode policy --output data/my-qwen35-development.json
```

Repeated use of these photographs is development evidence. After this controller round closed, the separate [classifier audit](classifier-audit.md) verified preprocessing and score calculation and replayed threshold sensitivity. Fresh data must still be reserved before selecting and validating a new reporting policy.

The final API check confirmed the candidate identity on a temporary port using the saved public case, with no extra inference. The ordinary app was restored with Qwen3 4B, the candidate was unloaded, and both temporary servers were stopped. [Candidate API check](evidence/controller-comparison/candidate-api-verification.json) · [Final verification](evidence/controller-comparison/final-verification.json).
