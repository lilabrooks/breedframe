# 001: Local controller and isolated classifier

Status: Implemented for the prototype; model work closed on 2026-09-12. This records the implementation and closeout without claiming a separate formal owner acceptance.

## Decision

Use Qwen3 4B Q4_K_M through a project-local Ollama 0.34.0 server. Use the requested ViT through Transformers and PyTorch in a persistent child process. The controller is text-only and chooses one schema-constrained JSON action from numerical evidence per turn.

The inspected Mac is an M4 Air with 16 GB memory. No Ollama executable, running server, LM Studio application, or installed model manifests were found in the inspected standard locations. The downloaded Qwen model reports `completion`, `tools`, and `thinking`; application calls disable thinking and do not store hidden reasoning. Measured behavior is recorded separately in the evidence directory.

## Alternatives and consequences

- An existing Qwen3 8B runtime could avoid a download, but none was found locally. A new 8B model would consume more weight memory; its benefit is unmeasured here.
- A vision controller could select meaningful crops. It adds a second image interpretation model and changes the accuracy evaluation. This version cannot justify automated spatial choices.
- A single-process ViT is simpler, but Python thread timeouts cannot stop a wedged native inference call. A spawned child lets the parent terminate overdue classification and keep completed observations.
- A direct classifier is the retained baseline. It has lower orchestration cost and may be sufficient for this task. The evaluation tests whether the extra workflow earns its latency.

The four tools inspect pixels, classify, request a photo, and finish. No reference lookup is needed to report observed classifications. Finish arguments select a recorded classifier event; the app attaches observation IDs; report text and scores are derived from those records. This restricts narrative flexibility to prevent fabricated visual detail.

## Failure and data boundary

Native tool responses failed the one-action contract in a real smoke run. The chosen adapter uses Ollama structured outputs and a strict Pydantic action envelope. Model choices remain separate from execution.

Each model response consumes one of six action attempts, including invalid responses. Duplicate calls are rejected. A controller failure can be retried once; classifier failure produces an error observation the controller can inspect. Deadlines and the budget produce an incomplete state with prior results intact. Requests pause and new images resume the same case; three photos cap case growth.

JSON state is replaced atomically after each event. Uploaded images are decoded, EXIF-oriented, re-encoded without metadata, and stored under generated IDs. Filenames never enter the controller context. One API operation at a time prevents overlapping writes. Startup marks interrupted runs incomplete.

## Verification and exit

Trace upload → normalized local file → controller tool call → child classifier → persisted observation → controller-selected report in `docs/evidence/first-slice.json`. Test validators, deadlines, budget and persistence. Measure the application process tree and controller residency on this machine; report the limitations of unified-memory accounting.

Revisit the controller if repeated tool failures or latency make demonstrations unreliable. The original crop exclusion is revised below for user-supplied coordinates; automatic localization still requires separate evidence. Revisit JSON if multiple users or concurrent case edits become requirements. Switching controllers replaces the adapter and requires rerunning the fixed evaluation. Returning to the baseline preserves saved photos and classifier observations.

## Sources checked

- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Qwen3 4B model and Apache 2.0 license](https://ollama.com/library/qwen3:4b)
- [Classifier, MIT model-card metadata](https://huggingface.co/wesleyacheng/dog-breeds-multiclass-image-classification-with-vit)

## Authorized v2 extension

The owner asked to implement the prioritized enhancement plan. Human-selected coordinates now provide the localization input: normalized image → recorded user bounds → saved region PNG → classifier child → persisted event → deterministic comparison → browser and exported assessment. This adds no model or service. Regions are correlated with their parent photo and do not create an additional photo vote.

Comparison and request validation are shared by Qwen3 and a deterministic rules baseline. Score ≥ 0.5 and margin ≥ 0.15 now control reporting eligibility, while raw outputs stay visible. They are conservative heuristics with no calibration claim. All measured orchestration cases abstained, and the controller added latency without improving reports. Keep those results visible; do not expand model size or introduce an automatic detector on the assumption that it will fix them. A separate model or threshold study would need its own fixed protocol and fresh reserved data. [Measured comparison](../evidence-comparison.md).

## Prototype closeout, 2026-09-12

The existing local architecture and reporting gate remain as the measured prototype. The final candidate comparison missed supported-case coverage, and no replacement policy was adopted. Earlier suggestions in this ADR to revisit models or launch another evaluation are historical; they do not schedule further work.

Threshold changes, two-photo agreement adoption, ResNet adoption, Qwen3.5 vision screening, report-scope implementation, automatic subject selection, the proposed crop study and further data collection are closed for this prototype. Human region selection remains implemented with no demonstrated accuracy benefit. The score floor itself remains in the app; closing threshold work does not remove it or validate its calibration.

The final documentation distinguishes the historical request/resume success from current controller behavior and keeps experimental reporting policies separate from deployed behavior. The UI wording was updated after the recorded runs; inference code and experimental records remain unchanged. The [findings page](../findings.md) owns the definition of done and the single reopening condition. Unanswered questions create no automatic follow-on work.
