# Replacement classifier screen

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

ResNet-50 improved raw breed ranking on the existing photos but failed the screen's original definition of unsuitable inputs. **Its rejection is reopened** after the [methods review and owner clarification](review-02-response.md). Real dogs of unknown ancestry may receive cautious visual matches, and same-breed groups may receive clearly labeled scene-level matches. The historical screen below retains its original cohort definition. The app still uses its original ViT, Qwen3 4B and reporting thresholds.

The owner selected these criteria before candidate inference: at least 50% coverage on supported breeds, at most 10% wrong breed reports among reports, and no reports on unsuitable inputs in the fixed test set. The development screen applies the same criteria as an early rejection check. Passing it would only permit a fresh-data study.

## Metadata screening

Three candidates were checked against their pinned configuration, processor and model card before downloading weights:

| Candidate | Finding | Decision |
|---|---|---|
| `dima806/133_dog_breeds_image_detection` | Apache-2.0 declaration; ViT with the same 224-pixel preprocessing as the baseline. Adds Portuguese Water Dog but omits Scottish Terrier, losing a breed in the regression set. | Reject at label screening. No weights downloaded. |
| `dima806/dogs_70_breeds_image_detection` | Apache-2.0 declaration; ViT with 70 classes and baseline-style preprocessing. Lacks English Springer Spaniel in the existing labeled set. | Reject at label screening. No weights downloaded. |
| `microsoft/resnet-50` | Apache-2.0 declaration; ImageNet-1k classifier with all five regression-set breed labels and non-dog classes. The safetensors file is 102,482,854 bytes. | Run one development screen. |

Sources checked in this task: [133-breed model](https://huggingface.co/dima806/133_dog_breeds_image_detection), [70-breed model](https://huggingface.co/dima806/dogs_70_breeds_image_detection), [ResNet-50 model](https://huggingface.co/microsoft/resnet-50). Pinned metadata is retained under [classifier-screen evidence](evidence/classifier-screen/development-protocol.json). Published accuracy figures use different datasets and were not used to rank these candidates.

The 133-breed card links a Kaggle notebook, but the fetched page exposed no notebook content. Its per-image training overlap remains unknown. ResNet documents ImageNet-1k training; overlap with our public photographs is also unknown. All existing photos are development evidence regardless of their former split.

## ResNet experiment

Revision: `34c2154c194f829b11125337b98c8f5f9965ff19`. The installed Transformers implementation loaded the pinned safetensors without missing or mismatched weights and ran on MPS under the project's offline policy. No controller calls were made.

The candidate uses its own saved processor: a 224-pixel output with resize/crop behavior, bicubic resampling and ImageNet normalization. The baseline's square-resize settings were not substituted. The resolved processor configuration is saved in the results.

Softmax runs across all 1,000 native classes. A candidate report requires the global top class to be one of the 118 reviewed domestic-dog entries (IDs 151–268), then satisfy the score and margin cutoffs. Scores are never renormalized over dogs. This is a candidate-specific gate for the diagnostic, not an adapter installed in BreedFrame.

The original cohorts remain fixed: 12 labeled photos of six dogs, two unsupported-breed photos of Bo, three non-dogs, two multiple-dog photos and one unknown-ancestry photo. The five accuracy labels have explicit native-ID mappings. This does not establish equivalence across the complete baseline and candidate label spaces; Bo remains unsupported.

The protocol fixed all 20 inputs and 117 score/margin combinations before inference. Its early exit required at least the baseline's 8/12 raw correct predictions and at least one tested gate meeting the owner's criteria. No photos were added or rerun after seeing the results. [Protocol](evidence/classifier-screen/development-protocol.json) · [Download hashes](evidence/classifier-screen/download.json).

## Results and stopping decision

Raw top-one correctness rose from 8/12 to 9/12. Buddy's first photo and Millie's second improved; Barney's first regressed. Correctness on the six initial labeled photos stayed at 4/6. These paired, familiar photos do not establish a general accuracy gain.

The cat was classified as Egyptian cat and the horse as sorrel, so the native-class gate rejected both. The sculptures, multiple dogs and unknown-ancestry dog still produced breed labels.

At the original numerical cutoffs, score 0.5 and margin 0.15, the candidate gate permits 9/12 labeled-photo reports, all nine correct. It also permits the sculpture, both multiple-dog images and the unknown-ancestry image. Under the owner's criteria, those four unsuitable reports fail the screen.

The Champ-and-Major photo produces a German Shepherd score above 0.999. That result survives cutoffs that accept most correct single-dog results. Across all 117 tested settings, none combines the required coverage and error rate with zero unsuitable reports. The fixed early exit was reached, so no threshold was selected and no fresh evaluation set was consumed. [Full native scores, timings and gate results](evidence/classifier-screen/development-results.json).

This failure belongs to this candidate plus its native-class/score/margin gate. It does not rule out using the classifier with separately measured subject selection or suitability checks.

## Original next-priority proposal, superseded after review

The proposal below is retained as the conclusion reached at the end of the screen. The [revised order of work](review-02-response.md) defers subject detection and this single-image-only collection. It first separates reporting metrics from orchestration, probes the skipped-current-photo decision, and defines controls for candidate reporting policies under the clarified product scope.

Investigate how to establish a suitable, selected live-dog subject before making a breed report. The high-scoring multiple-dog photo is the earliest cheap regression case for that work. Any additional model or required user selection changes the workflow and needs its own comparison; a classifier name change alone does not provide that evidence.

Fresh photo collection was deferred after the failed development gate. No new holdout is claimed. When a revised system passes the cheap checks, freeze the following collection before choosing a reporting policy:

- Two identity-disjoint groups, development and reserved evaluation, each with 12 supported-breed subjects, two unsupported breeds, four non-dogs (including dog depictions), two multiple-dog scenes and two unknown-ancestry dogs. One image per subject or scene in this first study, 44 images total.
- Preserve source labels, licenses, original URLs, file and normalized-pixel hashes, capture/upload dates, identity uncertainty and possible training overlap. Exclude every known v2 dog identity and duplicate exposure. Public-photo novelty to this project does not prove absence from training.
- Fix both groups before tuning. Select at most one policy on development data; require the owner's coverage/error criteria there before opening reserved results. Keep failures and abstentions in their denominators. If no policy qualifies, stop without evaluating the reserved group.
- Evaluate the frozen policy once. For the 12 reserved supported subjects, at least six reports are needed; the wrong-report limit is evaluated among those reports. Report each unsuitable cohort separately and require zero reports across them. Zero observed errors in this small set does not establish a zero population error rate.

The final workflow would then need its own test with Qwen3 fixed, including requests, completion, latency and memory. This single-photo classifier screen measures none of those outcomes and does not validate follow-up usefulness.

Verification: all 33 tests pass, along with Ruff and JavaScript syntax checks. The frozen inputs and runner hashes match, and the app health check confirms the original Qwen3 configuration remains ready. [Verification record](evidence/classifier-screen/verification.json).
