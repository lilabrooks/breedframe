# Paired controls and a conditional vision suitability screen

Registered before new inference. This is a bounded development experiment, authorized by the owner's instruction to proceed. It evaluates two-photo agreement first, then runs an isolated Qwen3.5 image screen only if the fixed controls expose a rejection failure. The application keeps Qwen3 4B, its ViT classifier, and its existing reporting policy.

## Decision and earliest stopping evidence

Two-photo leading-label agreement is a candidate reporting rule. Its observed 3/6 correct supported-dog reports came from an exposed set without paired non-dogs. Agreement can preserve a systematic error across views; this experiment asks whether three concrete controls expose that failure.

Stage A makes exactly five new ViT and five new ResNet predictions. The other 20 photographs retain their recorded predictions. Complete all three negative pairs even after a failure. **Run stage B only if a non-dog pair permits a ViT agreement report, or the frozen ResNet rule permits a report on any of the eight non-dog photographs.** If neither occurs, stop. Do not collect more controls to obtain a positive finding. A quiet result on this convenience sample would leave rejection reliability uncertain.

Stage B, if triggered, makes exactly 25 image-input calls and one no-image call to the pinned `qwen3.5:4b` package. It asks about visible real dogs and their count, without breed inference or controller decisions. A failure does not authorize prompt tuning, retries, another model, or additional photographs in this round. A passing screen can justify a separately registered evaluation; it cannot promote itself into the app.

## Frozen inputs and denominators

The manifest contains the existing 20 photos and five new ones: a second Socks photo, two views of the named horse Valegro, and two photographs of the Greyfriars Bobby sculpture. Captions, licenses, revisions, download URLs, file hashes and human visual review are retained. The cat pair reuses one exposed photo. The original horse and dog-sculpture photographs remain in the single-photo screen; no reliable second exposure of those exact subjects was established. Two distant Fala sculpture photographs were rejected before inference because the dog depiction occupied too little of the scene for the intended challenge. Their metadata and rejection remain recorded.

Pair identities follow source descriptions and visible content. New views are separate exposures, rather than crops or duplicate encodings. Their common subjects make them dependent observations. The old corpus is exposed development evidence, and training-set overlap is unknown for all photographs. No part of this run is a blind population estimate.

| Cohort | Stage A agreement | ResNet comparator and stage B | Metrics affected |
|---|---:|---:|---|
| Supported breeds | 6 pairs, 12 photos | 12 photos | Coverage, correct reports, errors among reports; live-dog acceptance and count |
| Unsupported breed, Bo | 1 pair, 2 photos | 2 photos | Unsupported-label reports; live-dog acceptance and count, not supported-breed accuracy |
| Unknown ancestry, Topper | No pair | 1 photo | Visual-match availability; live-dog acceptance and count, no ancestry accuracy claim |
| Multiple dogs | No pairs | 2 photos | Visual-match availability, count and proposed report scope; no individual-breed accuracy claim |
| Non-dogs | 3 pairs, 6 photos | 8 photos | False breed reports and false live-dog acceptance; never included in supported coverage |
| No-image control | None | 1 additional model call | Validity and unsupported acceptance; excluded from all photo denominators |

The eight negative photos comprise two cats, three horses and three dog sculptures. They represent five subjects or artifacts. There are no empty scenes, other depiction media, paired mixed-ancestry dogs, or different-breed groups. Those gaps limit interpretation without changing this round's fixed sample.

The owner permits cautious visual matches for dogs of unknown ancestry and clearly labeled scene-level matches when multiple dogs share a breed. An individual report in a multiple-dog scene requires a selected subject. A whole-frame classifier label plus a count does not establish that every dog shares the label. This experiment records a proposed scene scope and leaves that condition unresolved; it does not implement a valid multi-dog reporting workflow.

## Stage A: direct classifiers and fixed reporting rules

Use the pinned ViT and its saved slow processor through the existing `Classifier`, with the app's normalized images. Patch score and margin floors to zero only inside the diagnostic process. Require two distinct classified photos and retain the existing inspection, quality, unresolved-label, disagreement and current-photo conditions. Persist the actual comparison and `build_report` output for each of the ten pairs. This is direct evidence assembly; controllers cannot skip the second classification.

Retain the previously selected ResNet-50 comparator: native global top class must be a domestic dog, native score at least 0.8, margin at least zero. Domestic-dog classes are IDs 151–268 in its pinned 1,000-class label space. Do not renormalize dog scores or tune thresholds. Load its own saved processor and float32 model on MPS, as in the earlier screen. Keep full native outputs for new photographs. The ViT and ResNet score scales remain distinct.

The models run sequentially and are unloaded between stages. Each new classifier request has a 60-second bound including first loading. Retain errors and abort the remaining stage on a classifier/runtime failure. A partially completed stage cannot satisfy the vision trigger. Report six-pair coverage for agreement and 12-photo coverage for ResNet separately. Also show ResNet on the preassigned first photo of each pair when comparing case counts. Two-photo agreement requires another acquired image; this replay does not measure the resulting user burden or follow-up success.

## Stage B: an isolated image screen

Pin Qwen3.5 to digest `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`, Q4_K_M, and Ollama 0.34.0. Verify the installed vision capability before generation and the returned model on every call. Use independent single-message requests with no conversation history. Source titles, filenames, captions, expected labels and classifier outputs never enter the prompt. Visible text within the image remains available.

Normalize each photograph with the application function, then fit the full frame within 1024 × 1024 using LANCZOS, preserving aspect ratio and never enlarging a small source. Encode fresh RGB PNGs without metadata. Save normalized and vision-input hashes and dimensions. The vision model uses its own internal processor; this is a declared evidence and preprocessing change from the text-controller experiment.

Use the exact prompt and JSON schema in `protocol.json`. Output is limited to `subject_type` (`real_dog`, `dog_depiction`, `other_animal`, `no_animal`, `uncertain`) and `dog_count` (`zero`, `one`, `multiple`, `uncertain`). The consumer accepts only `real_dog` with count `one` or `multiple`; uncertainty, errors and contradictory outputs fail closed. Count one proposes individual scope and multiple proposes scene scope. Type and count accuracy are also reported separately.

Use temperature 0, seed 42, context 8192, maximum output 300 tokens, presence penalty 0, repeat penalty 1, top-k 20, top-p 0.95, and `think=false`. Each call has a 60-second bound, including loading. One seed determines a fixed shuffled image order. The identical no-image request runs last, omitting only the `images` field. Since every text request is otherwise identical, one no-image call is a grounding control, not 25 independent controls or a matched controller-performance comparison. Changing the evidence does not measure whether Qwen3.5 is a better controller.

Ollama's REST API accepts base64 image data in the message `images` array and a JSON schema in `format`. The runner records request byte hashes, reconstructable local image references and complete raw responses. [Vision API](https://docs.ollama.com/capabilities/vision), [structured output API](https://docs.ollama.com/capabilities/structured-outputs).

Compose the screen with the fixed ResNet decisions offline: a report remains eligible only if both accept. This can remove reports but cannot fix breed rankings. Preserve supported, unsupported, unknown-ancestry, multiple-dog and non-dog results separately. Record which baseline false reports were prevented, which correct reports were lost, and whether there was any incremental rejection benefit over ResNet alone.

Advance the screen to another evaluation only if all 26 calls are valid, the no-image control abstains, all eight non-dogs are rejected, at least 16/17 live-dog photos are accepted, at least 6/12 supported photos retain reports with at most 10% wrong reports, and neither multiple-dog photo is assigned individual scope. Zero wrong reports is needed at these small report counts to meet the owner's percentage. These are development criteria, not statistical guarantees. Passing without preventing a ResNet false report does not demonstrate a reason to add the screen to that comparator.

No-image latency is excluded from image latency. Separate first-load cost using the native duration fields. Sample process RSS and macOS footprint every 200 ms for the isolated runner and project Ollama, retaining errors and baseline/peak accounting. The app remains idle and classifiers are unloaded; this does not measure simultaneous app, classifier and vision memory. Ollama residency, RSS and footprint overlap and must not be summed. Instrumentation is present throughout this screen and may affect timings.

Run inference under the repository's offline sandbox. Abort remaining calls on runtime/model drift, concurrent app work, unrelated resident models, HTTP failure or timeout. Check source and input hashes before and after each stage; any drift invalidates completion. Retain a malformed completed answer as a failed-closed observation and continue the fixed schedule. Unload Qwen3.5 when finished and verify the ordinary app is ready with its original defaults.

## Preservation and execution

`scripts/evaluate_suitability.py prepare` performs normalization, inspection and hashing without generation. It saves `manifest.json` and then `protocol.json`, including the runner, application, processors, weights, cached evidence and this document. Subsequent phases reject changed hashes and refuse to overwrite an existing result file. Verification reconstructs every vision request and checks the raw output against the saved consumer decision. This traces bytes through normalization, image handoff, model response, the deterministic consumer and the saved result.

```sh
PYTHONPATH=. .venv/bin/python scripts/evaluate_suitability.py prepare
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=. sandbox-exec -f scripts/offline.sb .venv/bin/python scripts/evaluate_suitability.py agreement
# Only when agreement-results.json records vision_triggered: true:
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=. sandbox-exec -f scripts/offline.sb .venv/bin/python scripts/evaluate_suitability.py vision
PYTHONPATH=. .venv/bin/python scripts/evaluate_suitability.py verify
```

Results and interpretation belong in a separate document so this protocol remains frozen. Do not infer deployment readiness, ancestry accuracy, reliable rejection rates or controller superiority from this run.
