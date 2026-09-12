# Current-photo context probe

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

**Making the missing current-photo classification more prominent did not make either controller choose classification.** All 12 scheduled decisions completed legally. The context change remains an experiment; application code and the reporting policy are unchanged.

## Fixed comparison

The probe reconstructed three development states from the preserved Qwen3 forced-pair run: Barney, Buddy and Bo, immediately after inspection of photo 2. Each state already contained a photo-1 ranking, an empty photo-2 ranking, five remaining actions and a blocker saying the current photo had no classifier result. Classification, an inconclusive finish and a request were all allowed.

Both pinned controllers received each same saved state in two forms:

- **Original:** the current application's `decision_context` output.
- **Clearer:** prepend `current_photo_classified: false` and a top-level copy of `comparison.blockers`. Preserve every original field and its order, including the complete nested comparison and its blockers.

This is a bundled prominence change. It does not isolate the Boolean field from the repeated blockers. The original Qwen3 history was used for both models so their available evidence matched; the probe did not replay a new first-photo trajectory for each model.

The system prompt, tool descriptions, user-message suffix, dynamic schema and action budget stayed fixed. Requests used the existing `Controller.choose` path, temperature 0, seed 42, `think=false`, context 8192, output limit 500, and the same explicit sampling penalties as the earlier comparison. The reporting gate remained score 0.5 and margin 0.15. No photograph, caption or ground-truth label was added to either controller's input.

The schedule alternated original/clearer order across cases and reversed that order for the second model: three states × two contexts × two models, one decision per cell. Models ran sequentially in Ollama 0.34.0 under the project's offline network policy. There were no retries, extra seeds, warmup generations or downstream tool executions. Cold-load time is included in some recorded durations; this is not a model-speed comparison.

[Frozen protocol and schedule](evidence/current-photo-context/protocol.json) · [Saved states and schemas](evidence/current-photo-context/fixtures.json) · [Runner](../scripts/probe_current_photo_context.py).

## Observed decisions

| Controller | Context | Classification choices / 3 | Request choices / 3 | Inconclusive finish choices / 3 |
|---|---|---:|---:|---:|
| Qwen3 4B | Original | 0/3 | 0/3 | 3/3 |
| Qwen3 4B | Clearer | 0/3 | 0/3 | 3/3 |
| Qwen3.5 4B | Original | 0/3 | 3/3 | 0/3 |
| Qwen3.5 4B | Clearer | 0/3 | 2/3 | 1/3 |

Qwen3.5 changed its Barney choice from `request_another_photo` to `finish_assessment`. Its Buddy and Bo choices remained requests. Qwen3's three paired choices were unchanged. These are chosen actions at fixed decision points; no request was sent to a user and no classifier tool was executed.

The advance condition required all 12 decisions to be valid, at least five of the six clearer-context decisions to choose classification, and more classification choices than the contemporaneous original context. It was not met. No cell was repeated or added after observing the result.

[Actual requests, raw responses, identities, per-cell results and summaries](evidence/current-photo-context/results.json).

## Interpretation and limits

The two added fields did not resolve the skipped-current-photo choice in these three states under the existing reporting policy. One changed request/finish choice is insufficient to claim a reliable reduction in request burden. There are no new completed cases, breed reports or accuracy estimates from this probe.

Both contexts still described a policy whose numerical gate blocks every recorded v2 ViT result. The probe holds that condition fixed; it cannot establish how these controllers would use the same state under another reporting rule. It also cannot rule out effects from other context representations, prompts, thinking settings or task formulations.

The primary evidence-use denominator is three decision opportunities per model and context, including the unsupported-breed Bo case. This is a small, previously exposed development set. The model does not receive the case's source label or know that Bo is outside the classifier's label space.

Two-photo agreement was not enabled or evaluated in this context probe. The later [paired-control experiment](paired-suitability-results.md) rejected all three fixed non-dog pairs; it remains development evidence with unknown-ancestry and multiple-dog pairing gaps. Before promoting any such rule, define its output scope and evaluate new identities, retaining the owner's clarified treatment of unknown ancestry and same-breed scenes.

A workflow that classifies every supplied photo deterministically remains a possible comparison. That would change the division of work between code and controller and must be evaluated as such. This null result does not automatically select that design or justify a larger controller.

## Preservation

The source hashes remained unchanged throughout the probe. All captured requests matched the declared state and schema; after accounting for model name and state, their payloads were identical. Returned model names and pinned digests matched. No response contained thinking text or received image inputs.

The experiment models were unloaded. The ordinary app remains ready with Qwen3 4B and the original classifier/reporting code. [Verification record](evidence/current-photo-context/verification.json).

To prepare a separate future protocol without overwriting this evidence:

```sh
PYTHONPATH=. .venv/bin/python scripts/probe_current_photo_context.py prepare --output data/context-probe-new
```

Preparation makes no model calls. A later `run` stage uses that frozen directory; an existing results file prevents an automatic rerun. Repeating these states would remain development work and requires a reason beyond seeking a different outcome.
