# Findings and prototype closeout

**Model work is closed for this prototype as of 2026-09-12.** BreedFrame demonstrates a local, bounded investigation with visible evidence and persisted cases. Useful breed reporting did not meet the owner's criteria in the final comparison. No further experiment is scheduled.

The experimentation produced a working prototype and documented the measured limits of its design. The current default is Qwen3 4B, the original ViT and the 0.5 score / 0.15 margin reporting gate. ResNet and two-photo agreement remain experimental policies. [Original purpose and contract](spec.md) · [Architecture and closure decision](adr/001-local-inference.md).

## The reporting tradeoff

The historical v1 evaluation emitted correct golden retriever and pug reports at scores 0.084443 and 0.476691. It also reported a checkerboard as a pug at 0.013304. Two other cases finished incomplete. These were five inputs, including three labeled dog inputs; the three emitted reports are a separate denominator. [Saved v1 rows and reports](evidence/evaluation-results.json).

The v2 gate blocks every leading score in the recorded 20-photo corpus, including correct predictions. Its maximum is 0.222815. This prevents those false reports while also eliminating useful report coverage. Applying the same gate to cached direct outputs produces zero reports too, so comparing ungated direct rankings against gated agent reports cannot isolate controller value. [V2 comparison](evidence-comparison.md).

Scores also overlap in ways that frustrate a simple floor. In those 20 saved observations, the dog sculpture ranks fourth by leading score at 0.180789. Only three correct supported-dog predictions exceed it, covering Barney and Champ. A score-only rule rejecting that sculpture can retain correct predictions for at most 2/6 supported identities, even allowing either available photo. This bound applies to those saved top-one outputs and that rule family. It establishes no universal limit on other model uses. [Replay observations](evidence/classifier-audit/threshold-replay.json).

## What the evidence supports

| Capability or result | Evidence and status | Limit |
|---|---|---|
| Local inference and visible tool execution | Recorded local runs with pinned models and an offline execution check; implemented action budgets and persisted observations | Demonstrated on this Mac; this closeout performs no new runtime or software verification. [Offline record](evidence/offline-smoke.json) |
| Request and resume | V1 requested another photo and resumed to a correct beagle report | Historical configuration. Qwen3 requested no follow-ups in the measured v2 policy runs. [V1 trace](evidence/browser-resumed.json) |
| Region selection, case recovery and evidence display | Current controls have recorded browser demonstrations | Region selection does not establish crop accuracy or automatic dog detection. [V2 browser record](evidence/browser-comparison-v2.json) |
| Raw breed ranking | ViT top-one correctness was 8/12 supported photos in the earlier corpus and 1/12 in the new collection | Convenience archives with different composition; no reliable “works well on clear photos” boundary is established. [New results](identity-comparison-results.md) |
| Useful breed reports | Each experimental policy reported correctly on 3/6 exposed supported cases; each reported on 0/6 new supported cases | Policies were unadopted. Error among reports is undefined in the latter collection. [Matched comparison](paired-suitability-results.md) |
| Non-dog rejection | ViT rejected three paired negative controls; ResNet rejected eight negative photos while also reporting some exposed dog cases | Small development samples show observed rejection, not reliable dog detection. Both policies later abstained on every cohort. [Control counts](evidence/paired-suitability/summary.json) |
| Controller follow-up use | Both text controllers skipped supplied classifications; the 12-decision context probe did not improve classification choices | This intervention failed. Other model roles remain unmeasured. [Probe](current-photo-context.md) |

When no result is eligible, the [decision schema](../breedframe/policies.py) permits only `inconclusive` as the finish outcome. The controller still chooses among allowed evidence-gathering, request and finish actions. A different controller cannot override the gate, but the code does not prove that all controllers would acquire identical evidence.

## Why stop here

The final registered comparison required at least 50% supported-case coverage, at most 10% wrong reports among reports, and zero prohibited-input reports. Both fixed candidates missed coverage at 0/6. Each classifier had only one correct leading label among six supported initial photos; all thirteen ViT pairs disagreed. These results give no basis to promote either policy. [Final summary](evidence/identity-comparison/summary.json).

The new collection is archive-heavy and changes photographic composition as well as identity. It cannot settle performance on contemporary personal phone photographs or explain the accuracy drop causally. Public-image training overlap remains unknown. We have enough evidence to close this prototype's breed-report investigation without claiming that breed reporting is impossible.

The proposed manual-crop study would still leave a product-adoption decision unresolved. A positive ranking result alone would not establish report coverage, rejection or user benefit. That additional work is outside this completed phase of experimentation. The existing manual-region feature remains available, with no accuracy-improvement claim.

The Qwen3.5 text comparison earned no promotion. Its conditional vision stage never triggered, so vision was neither validated nor rejected as a capability. Threshold changes, controller swaps, agreement-policy adoption, ResNet adoption, vision screening, automatic selection, report-scope implementation, the crop study and further photo collection are closed for this prototype. The current gate stays in place as a documented limitation. Accepted unknown-ancestry and scene-report preferences remain in the specification; their output paths remain unimplemented.

## Reading the final review accurately

The [independent review](review-product-value-and-stopping.md) supports stopping. A few arguments require narrower wording:

- Serialized observations can repeat the same prediction. Their count is neither a count of distinct images nor a complete record of all local use. V1 did emit reports; current v2 evidence shows no eligible breed reports.
- The checkerboard score does not prove that every useful floor admits it. A score-only floor of 0.05 separates that recorded checkerboard from the two correct v1 reports. This arithmetic counterexample is not a proposed threshold; the v2 sculpture overlap is the stronger limited finding.
- The earlier candidate controls did reject non-dogs while reporting some supported cases. The latest all-abstaining comparison cannot erase that evidence or establish general rejection reliability.
- Crop benefit remains unknown. One regression and the size of the improvement required do not prove that crops cannot help. Stopping is a scope and investment decision.

## Completion and reopening

Completion means the README leads to these findings, the demo narrative distinguishes current and historical behavior, prior next-step proposals are marked closed, and the repository is recorded in Git. Historical protocols, results and reviews remain intact. No further model result is required to finish.

Model work reopens only through an explicit owner decision to pursue a practical tool with a defined input population, use case and effort budget. A new model release or hypothesis may inform that decision; it does not automatically restart the project. Further questions remain documented without becoming an active backlog.
