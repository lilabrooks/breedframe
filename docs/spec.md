# BreedFrame specification

**Closeout, 2026-09-12:** the prototype is complete and model experiments are closed. Breed-report usefulness missed the final coverage target. Requirements and historical outcomes below are retained; [findings and remaining limits](findings.md) govern the final status.

Build a local dog-photo assessment prototype for experimentation with model-controlled workflows. The required outcome is a visible, model-controlled investigation, including a case that asks for another photo and resumes with its prior evidence.

The current workspace checks local model availability before enabling Scout. Missing or incomplete model assets, an unavailable controller, or a failed health connection produce a visible setup panel. New inference is disabled until both models are available; saved results remain readable while the API is reachable. See [local setup](setup.md) for installation and recovery.

## Product contract

Owner clarification after the methods review: allow cautious visual-match reports for real dogs of unknown ancestry, and clearly labeled scene-level matches when multiple dogs share a breed. An individual-dog report still needs a selected subject in a multiple-dog scene. The current report schema does not yet express this scope distinction; see the [review response](review-02-response.md) for the accepted direction and remaining work.

- Photos and inference stay on this Mac. Downloads happen only during explicit setup. Runtime binds to loopback and loads local weights.
- Report **likely visual breed matches**. Scores are uncalibrated classifier outputs, not ancestry percentages. Candidates are alternatives. A known-class classifier cannot establish that an image contains a dog.
- Preserve the model's original class indices and published labels, including unresolved truncated names.
- A text-only local controller chooses actions from evidence returned by tools. It never receives invented visual descriptions.
- Show each actual tool execution, its inputs and results, candidate history, status, requests, and unresolved uncertainty. Show short explanations, never hidden reasoning.

## Workflow

Upload → local controller → validated tool call → recorded result → controller chooses again. Six action attempts per photo; invalid calls consume budget. Bound controller and classifier time, block duplicate work, and preserve partial observations on failure. A system stop is labeled incomplete, never presented as an agent conclusion.

The implemented tool set is inspect_image, classify_breed, classify_region, request_another_photo, and finish_assessment. Regions use explicit user-selected coordinates. Automatic localization and breed-reference retrieval remain omitted.

A request pauses the same persisted case. A new photo resumes it with earlier observations available and a fresh six-action budget. Cap each case at three photos. Compare actual candidate history across photos and regions without averaging raw scores. Disagreement, weak scores and unresolved quality or label concerns block eligible breed reports. A crop shares its parent photo's vote. Permit an inconclusive report. Completed cases can accept more evidence while retaining report history. Support partial completion, cancellation, retry without resetting budgets, readable export and deletion.

## Implementation and acceptance

1. Establish a real photo → controller → classifier → report trace before building the UI.
2. Browser UI supports upload, live progress, evidence history, pause/resume, report, and a direct-classifier baseline.
3. Demonstrate two model-selected paths with separate curated demo inputs, including a request/resume path.
4. Freeze a small licensed evaluation manifest before tuning. Run baseline and agent on identical inputs. Count all cases, requests, abstentions, failures, latency and tool calls; report label accuracy only where labels support it. Do not claim generalization from a tiny convenience set.
5. Test argument validation, budget exhaustion, failures and persistence/resumption. Verify UI and offline operation after setup.
6. README includes setup, screenshots, architecture, attribution, measured results and limits. Keep data, model files, caches and secrets out of Git. Publishing is outside this request.

## Weekend scope and assumptions

Single user, one server process, one active inference operation, local JSON case storage, Python API and plain browser assets. No cloud APIs, accounts, breed ancestry claims, dog detector, automatic bounding boxes, or medical advice. A small text controller's benefit over the classifier is an unproven hypothesis. Memory accounting on unified memory must state what was measured and avoid double-counting GPU allocations.

## Original prototype outcome

The real controller demonstrated both a direct report path and an inadequate-photo request/resume path. The fixed five-input evaluation found no classification improvement and exposed three invalid tool attempts. Offline model execution, MPS and the explicit CPU path were exercised. See README and docs/evaluation.md for measured values and evidence limits.

## Expanded implementation outcome

The historical v2 browser put case status and evidence comparison before the trace. Its report-count comparison is confounded: direct outputs are ungated, while the 0.5 reporting gate blocks every recorded v2 ViT result for rules and Qwen3. Gating the cached direct outputs also produces zero reports. Qwen3 did not request follow-ups or classify the supplied second views; these remain measured action choices under that configuration. The original request/resume demonstration is historical, not evidence that the current controller reliably chooses that path. See [recorded v2 results](evidence-comparison.md). The crop pilot does not establish the usefulness of subject-separating crops.

## Current Scout interface

The current workspace orders **Photo evidence**, **Scout’s activity**, and **Assessment**. It starts empty, with explicit upload and demo actions. Photo guidance allows up to 3 views of the same dog and directs users to separate cases for different dogs or breeds. This guidance doesn't implement the scene-level reporting scope described above.

Scout is the local agent's UI name. Its text controller chooses actions; separate tools inspect image quality, classify pixels, and assemble the result. A prominent live banner and repeating step cards identify current work, while the timeline retains actual inputs, results, and action attribution. **How this works** explains the AI/ML roles. Progress accounts for connection loss, cancellation, and completion, with reduced-motion styling.

Assessment leads with the current photo's top visual match and model score, qualifies tentative results, and retains detailed uncertainty in an expandable section. The display and readable export share the same summary. The model, reporting thresholds, and stored `inconclusive` outcome remain unchanged; showing a tentative match makes no new accuracy claim.

**Clear all** resets to an empty workspace while preserving history. **Saved cases** reopens prior cases and includes a confirmed permanent clear action for all cases, photos, and reports in the browser store. Active work blocks reset and deletion. See [Using Scout](usage.md) for the current flow and [UI hardening](https://github.com/lilabrooks/breedframe/milestone/2) for the planned browser checks.
