# Historical prototype evaluation

These measurements describe the original prompt and reporting policy. See the [current comparison](evidence-comparison.md) for the expanded corpus and stricter reporting behavior.

The benefit hypothesis was that an agent could recognize when another photo would help and avoid premature breed reports. The fixed sample supports the interaction behavior, but does not show higher classification accuracy.

## Protocol

The [manifest](evidence/evaluation-manifest.json) was written before the first inference run. It contains five inputs from four source groups. Source captions support the two breed labels; these are not genetic or pedigree verification. The golden retriever and its 48×32 derivative count separately in per-input metrics and share a source group.

All five inputs affect latency, tool-call, request, abstention, error and incomplete rates. The three labeled inputs affect top-1 and top-5 report accuracy. The two synthetic controls affect false breed-report counts. No photo is omitted because it is difficult or unlabeled.

The baseline and agent receive identical normalized pixels, use the same classifier and run once per input, alternating method order. No follow-up image is provided during evaluation: a request is both an abstention and an incomplete case at cutoff. An inconclusive finished assessment would be an abstention but not incomplete. System exhaustion or failure would count as both incomplete and abstaining unless explicitly reported otherwise. Raw provisional predictions are retained but never substituted for a missing final report when computing report accuracy.

Six action attempts and a 240-second per-photo deadline bound each agent run. Calls have a 45-second controller limit and a 60-second classifier limit, capped by the remaining deadline. The manifest and controller-source hashes are stored with the results.

## Observations

| Input | Direct top candidate | Agent outcome | Direct seconds | Agent seconds | Agent attempts |
|---|---|---|---:|---:|---:|
| Golden retriever | golden_retriever | Correct visual report | 3.805 | 8.870 | 4 |
| Pug | pug | Correct visual report | 0.049 | 6.772 | 3 |
| Golden retriever, 48×32 | golden_retriever | Requested another photo | 0.032 | 3.633 | 2 |
| Dark solid image | redbone | Requested another photo | 0.104 | 3.648 | 2 |
| Checkerboard | pug | Incorrect dog-breed report | 0.030 | 15.094 | 5 |

Both labeled source photos produced correct leading labels. The agent abstained on a degraded image that the baseline still classified correctly, reducing correct reports over all labeled inputs from 3/3 to 2/3. Among the two labeled cases it chose to report, both were correct; that narrower denominator is not the main accuracy metric.

The request and abstention rates were each 2/5 (40%). Two cases remained incomplete because no follow-up was supplied. One of two synthetic controls still received an agent breed report. Pixel diagnostics and known-class scores cannot establish dog presence.

There were three rejected action attempts: an unsupported low-resolution claim on the full-resolution golden photo, the same unsupported claim on the checkerboard, and a repeated attempt on the checkerboard. The validator rejected them, returned the errors as observations, and the controller eventually finished. These failures remain in the trace and latency totals.

## Demo development, kept separate

The native-tool trial exhausted its token allowance with an unstructured response. A schema-constrained action envelope supplied a reliable parse boundary. The first schema version exposed another problem: the controller confused breed class IDs with observation IDs. The app now attaches the observed evidence and restricts selected classifier IDs to successful current-photo events.

An initial tiny-beagle demo produced a premature report. The prompt was revised to treat resolution/exposure concerns as evidence gaps worth addressing before reporting. That revision was tested on the demo beagle and frozen before evaluation. Earlier failures remain in `first-slice-native-failed.json`, `first-slice-schema-v1.json`, and `demo-low-resolution-v1.json`.

The final recorded request path is inspection → request → pause → new photo → classification → inspection → report. The new image produced the first ranking, so the report explicitly says there was no earlier ranking to compare. There is no scripted scenario controller. The browser also exercised upload, reload while paused, and continuation of the same case.

## Memory and offline verification

The original evaluation captured RSS and Ollama residency. RSS was only 0.90 GiB in that warm run, so it was insufficient by itself to characterize combined local-model memory. A separate demo run restarted the controller under a non-loopback network denial and sampled both RSS and the macOS physical-footprint ledger. This changed cache/runtime conditions, so its latency is reported separately from evaluation.

The separate run completed in 14.779 seconds with 4 action attempts. It sampled 68 times at a requested 200 ms interval: peak summed RSS 4,348,035,072 bytes (4.05 GiB), peak summed process footprint 2,283,411,600 bytes (2.13 GiB), and Ollama residency 3,856,589,127 bytes (3.59 GiB). Actual sampling cadence includes process-inspection overhead.

`proc_pid_rusage` v0 uses the ABI checked in this Mac's installed Darwin SDK `sys/resource.h` and `libproc.h`. These are separate OS/runtime accounting views. Shared, reclaimable, compressed and Metal allocations can be treated differently; the counters are not additive. This is not a measurement of total system consumption or a guaranteed memory ceiling. The browser and unrelated applications are excluded.

The offline policy was applied to both Ollama and the client/classifier process. An external HTTPS probe failed under the policy; loopback controller calls and local ViT inference succeeded. The application does not need a cached web page or hosted API to assess a photo. [Raw offline record](evidence/offline-smoke.json).

## Limits

Five convenience inputs cannot establish general accuracy, calibration, non-dog rejection or benefit for mixed-breed dogs. The sample contains no independently verified ancestry labels, and training overlap is unknown. The derived golden image is correlated with its source.

Quality thresholds are simple heuristics, not a learned or validated photo-quality model. A high-detail checkerboard can pass them. The controller can still make unsupported choices; schema validity is not evidence validity. Keep the rejected calls and weak-score warnings visible.
