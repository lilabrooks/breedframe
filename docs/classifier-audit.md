# Classifier and reporting threshold audit

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

The numerical audit found no preprocessing or scoring defect in the checked path. Keep Qwen3 4B and the existing reporting thresholds for now. Lower cutoffs permit some correct reports on these photographs, but also admit unsuitable inputs; this evidence does not justify a new default.

## Numerical checks

Three fixed development photos covered a correct prediction (Barney's closer view), an incorrect prediction (Buddy's adult view) and a non-dog (Socks the cat). The protocol and hashes were saved before execution. All checks passed under the project's offline network policy, with no controller calls.

The saved processor resizes to 224 × 224 with bilinear interpolation, rescales by 1/255 and normalizes each channel with mean and standard deviation 0.5. Manual calculation matched the processor tensor exactly on all three inputs. EXIF-aware RGB normalization and PNG storage preserved the decoded pixels and processor output.

The model loaded without missing, unexpected or mismatched weights. Its 120-class label maps are inverses; this verifies index consistency, while the seven unresolved published labels remain unresolved. The classifier returns a linear layer's logits and the app applies softmax once, consistent with the installed Transformers single-label pipeline. [ViT implementation](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/vit/modeling_vit.py) · [Pipeline implementation](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/pipelines/image_classification.py).

The CPU pipeline and app's MPS worker returned the same top-five classes. Their largest score difference was below 0.000001. This checks implementation consistency on three inputs; it does not explain the training cause of the model's diffuse scores or reproduce its published accuracy.

[Protocol and asset hashes](evidence/classifier-audit/protocol.json) · [Numerical results and raw logits](evidence/classifier-audit/numerical-probe.json) · [Installed source](evidence/classifier-audit/installed-source.json).

## What lowering the gate permits

The replay used one recorded whole-photo result for each of the 20 existing images. All are now exposed development evidence, including the former reserved split. The 12 breed-labeled photos show six dogs across five classes, so these are correlated observations, not 12 independent dogs.

Thirty score/margin combinations were fixed before replay. Each ran through the actual comparison and report builder, retaining quality, unresolved-label, current-photo and disagreement requirements. These selected rows summarize the full grid:

| Minimum score / margin | Correct eligible / 12 labeled photos | Wrong eligible / labeled reports | Non-dog eligible / 3 | Unsupported breed / 2 | Multiple dogs / 2 | Unknown ancestry / 1 |
|---|---:|---:|---:|---:|---:|---:|
| 0.50 / 0.15, current | 0/12 | —, no reports | 0/3 | 0/2 | 0/2 | 0/1 |
| 0.20 / 0.15 | 2/12 | 0/2 | 0/3 | 0/2 | 0/2 | 0/1 |
| 0.15 / 0.05 | 3/12 | 0/3 | 1/3 | 0/2 | 0/2 | 0/1 |
| 0.10 / 0.025 | 4/12 | 0/4 | 1/3 | 0/2 | 1/2 | 0/1 |
| 0 / 0 | 8/12 | 3/11 | 3/3 | 2/2 | 2/2 | 1/1 |

At zero cutoffs, Millie's second photo still fails because its leading label is unresolved. Every whole photo has an empty heuristic quality-flag list, including the unsuitable inputs. Unknown ancestry eligibility records a report about an unverified subject; the replay does not generate or measure ancestry claims. Cohort counts remain separate.

The sculpture photo scores 0.180789 with margin 0.137699. Both exceed Millie's correctly classified first photo (0.122199 / 0.101960), Sully's two correct photos and Conan's correct second photo. Any pair of minimum score and margin cutoffs accepting one of those results also accepts the sculpture, given these identical empty quality flags. That is a concrete limit of this gate on this corpus.

Across the entire tested grid, settings admitting no unsuitable inputs produce at most 2/12 correct labeled-photo reports. This is an observed development result, not a validated operating point or a claim about every possible threshold.

The replay also distinguishes evidence availability:

- Initial-photo evidence: 13 cases, six labeled dogs; at 0.20/0.15 only one labeled case is eligible.
- Both classified photos: seven pairs, six labeled dogs; even at zero cutoffs only three labeled pairs are eligible. Buddy, Millie and Conan disagree across views; Bo is also blocked by disagreement.
- Recorded Qwen3 forced-follow-up evidence: all seven cases remain ineligible at every cutoff because the current photo lacks a classifier result. Changing thresholds cannot fill that recorded gap.

Eligibility is a counterfactual report boundary. A new cutoff would also change the controller's context and possibly its actions; this replay measures neither those actions nor follow-up burden, completion time or latency. [Full grid, per-case blockers and observations](evidence/classifier-audit/threshold-replay.json).

## Persistence and checks

Barney's real probe result was attached to its normalized photo, passed through the current gate, saved with `Store`, reloaded through the case API and exported as Markdown. The stored report remained inconclusive, retained score 0.222815 and exposed the weak-score blocker. This used the recorded probe output and made no additional inference call. [Saved case](evidence/classifier-audit/representative-case.json) · [Export](evidence/classifier-audit/representative-report.md) · [Handoff verification](evidence/classifier-audit/handoff-verification.json).

`make check` passes: 31 tests, Ruff checks and JavaScript syntax. Two existing dependency deprecation warnings remain. Application source, weights and historical results are unchanged. [Completion record](evidence/classifier-audit/completion.json).

To repeat this development audit with a new output directory:

```sh
PYTHONPATH=. /usr/bin/sandbox-exec -f scripts/offline.sb .venv/bin/python scripts/audit_classifier.py --output data/classifier-audit-repeat
```

## Next decision

Update: the [replacement classifier screen](classifier-screen.md) is complete. Its ResNet rejection was subsequently reopened after the [methods review and owner clarification](review-02-response.md). The original screen treated every unknown-ancestry and multiple-dog report as prohibited; the owner now permits cautious visual matches and clearly scoped same-breed scene reports. Defaults remain unchanged, and the revised investigation has not selected a reporting policy.

Investigate one replacement classifier's breed ranking and ability to reject unsuitable inputs. Start with its label coverage, published preprocessing, training-data overlap, license and local runtime requirements; reject an incompatible candidate before downloading or evaluating it. A breed-only classifier may still require a separate subject-presence check. This audit establishes the need to measure that behavior, not the effectiveness of a particular replacement.

Use the current corpus for regression and development only. Before threshold selection, freeze a fresh collection and identity-group split, minimum useful coverage and acceptable report-error criteria. Include supported breeds, unsupported breeds, non-dogs, multiple dogs and unknown ancestry; retain each cohort's denominator even if a candidate changes label coverage. End the evaluation at the fixed sample count, including failures and abstentions.

A candidate that fails the cheap compatibility or development checks stops there. A candidate that passes still needs its frozen policy evaluated on untouched data, followed by the complete Qwen3 workflow with the same photo availability and budgets. Preserve the existing default if those criteria fail. No replacement or new threshold is selected by this audit.
