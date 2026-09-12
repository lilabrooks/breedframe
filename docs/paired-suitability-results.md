# Paired suitability controls: results and decision

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

**Both candidate reporting rules rejected the fixed non-dog controls. The conditional Qwen3.5 vision screen did not run.** The registered trigger required an observed non-dog report from either rule; none occurred. This closes the bounded experiment without changing the controller, classifier or reporting policy in the app.

Five new photographs were classified once by each classifier. Existing predictions were reused for the other 20 photos. There were ten new classifier calls, zero controller decisions and zero vision calls. The [protocol](paired-suitability-protocol.md) and its [machine-readable registration](evidence/paired-suitability/protocol.json) were saved before those calls.

## What the paired controls establish

The ViT's leading labels differed across all three non-dog pairs. With score and margin floors removed, the actual comparison and report builder rejected each pair because of disagreement. All five new photos passed the existing quality checks. Those checks did not cause these abstentions.

| Same-subject pair | First leading label | Second leading label | Breed report |
|---|---|---|---|
| Socks, a cat | Border collie | Cardigan | None |
| Valegro, a horse | Weimaraner | Kelpie | None |
| Greyfriars Bobby sculpture | Beagle | Giant schnauzer | None |

Socks reuses the old cat portrait with a documented second exposure. The horse and sculpture pairs use new subjects because reliable second views of the original controls were not established. Their original photos remain in the single-photo comparator. Two distant Fala sculpture photos were excluded by visual inspection before inference; the selected sculpture views show the depiction more clearly. [Manifest and selection record](evidence/paired-suitability/manifest.json) · [Source attribution](evidence/paired-suitability/attribution.md).

This is three negative identities, with two dependent views each. It exposes no failure of agreement, but it does not establish that correlated mistakes cannot survive two views. There are no paired unknown-ancestry or multiple-dog examples, no different-breed group, and no empty scenes or other depiction media. The original supported examples remain exposed development evidence.

## Coverage with explicit denominators

ResNet uses the frozen native-class rule: global top class must be a domestic dog and its score must be at least 0.8. No thresholds were searched in this run. ViT requires two classified views, leading-label agreement, zero numerical floors, and the existing quality and unresolved-label restrictions.

| Candidate and evidence budget | Supported reports | Wrong among reports | Non-dog reports |
|---|---:|---:|---:|
| ViT agreement, two photos per case | 3/6 cases, 50% | 0/3 | 0/3 pairs |
| ResNet, preassigned first photo of those same cases | 3/6 cases, 50% | 0/3 | 0/3 first photos |
| ResNet, each available photo evaluated separately | 8/12 photos, 66.7% | 0/8 | 0/8 photos |

The 8/12 result is not case-level coverage. On the matched first-photo comparison, both candidates report on three supported cases, with different successes: ViT agreement reports Barney, Sully and Champ; ResNet reports Buddy, Champ and Millie. This sample does not establish that one candidate dominates the other. A second acquired image is required by the agreement policy; this replay does not measure users' willingness or ability to provide it.

Across all photos, ResNet also permits a visual match for Topper and both multiple-dog scenes, and abstains on both Bo photos. Keep those cohorts outside supported-breed accuracy. The owner's scope allows cautious unknown-ancestry matches and same-breed scene matches, but the current report contract does not implement that distinction. These observations do not verify ancestry or prove that every dog in a scene shares the predicted breed.

All five new ResNet top labels are outside its domestic-dog classes: marimba, barrel, bearskin and pedestal. The reporting rule therefore abstains. That is successful rejection under this rule, not evidence that ResNet correctly recognized the cat, horses or sculptures. Context-dependent false acceptance remains a question for fresh examples.

[Cohort counts and matched first-photo comparison](evidence/paired-suitability/summary.json) · [Complete new predictions, assembled cases, comparisons and reports](evidence/paired-suitability/agreement-results.json).

## Consequence for the vision proposal

The trigger was false: zero non-dog agreement reports and zero non-dog ResNet reports. Qwen3.5's suitability capability remains unmeasured. The absence of a triggered screen is neither a favorable nor an unfavorable result for that model. Its photo-only prompt, schema, exact input hashes, schedule and decision criteria are preserved in the registration; the runner refuses to execute that stage when the trigger is false.

This result supplies no measured rejection failure for a vision screen to fix in this comparator. It also supplies no evidence that another controller would improve the workflow. Any decision to investigate vision for a different reason needs an explicit new protocol, preserving this stopped run.

## Historical next step, superseded at closeout

Follow-up status: the [new-identity comparison](identity-comparison-results.md) below has now been completed. Both fixed candidates reported on 0/6 supported cases and missed the coverage target. Its results supersede this collection recommendation and propose a bounded investigation of input framing and breed ranking.

Prepare a small, identity-disjoint comparison of the two frozen reporting candidates. Give each case a preassigned initial photo and a documented second exposure, and retain case-level coverage, wrong reports, prohibited reports and acquisition burden. Use the single-photo ResNet rule as the first comparator because it matches the observed 3/6 case coverage here with one image; keep ViT agreement as the two-photo comparator. That is a reason to evaluate the simpler acquisition path, not to promote ResNet from this sample.

Include supported dogs and genuine non-dog controls under varied framing, then keep unknown ancestry and same-breed/different-breed groups in separate scope cohorts. Decide those scope semantics before interpreting reports. Define the fixed collection, outputs and stopping rules before inference. Do not expand this completed sample or tune the thresholds against its quiet result.

## Preservation

Publication cleanup later formatted the maintained runners and changed UI copy. The [measured-source archive](evidence/frozen-sources/README.md) preserves the registered bytes and documents restoring them in a disposable checkout. Both original input guards passed after restoration; saved case outcomes were reproduced without inference. Current publication files are not presented as the original measured sources.

Inference ran under the repository's offline sandbox. The runner checked model files against the frozen hashes; the pinned ViT and ResNet files also matched their preserved audit/download records. Each classifier ran in its own process, with unloading between them and no controller generation. Source and input hashes remained unchanged through verification. The ordinary app is ready and idle with Qwen3 4B and its original classifier/reporting code; no Ollama models remain resident. [Verification](evidence/paired-suitability/verification.json).

The ten new calls completed without errors. Their timings include first model loading and are retained in the raw results, but no new whole-app latency or memory comparison was performed. The unused vision runner has not had its inference path exercised. Its existence and a passing lint check do not validate model/API compatibility.
