# New-identity comparison of fixed reporting candidates

Compare single-photo ResNet with two-photo ViT agreement on 13 newly assembled cases. The photos and subjects are separate from previous classifier inference in this repository. This is a small prospective comparison within a convenience collection; public archival images may have appeared in training.

The existing app stays unchanged. There are no controller decisions, vision-model calls, new thresholds, crops selected by a model, or automated subject-selection claims in this round.

## Collection and exposure

Freeze 26 photos as 13 pairs before inference. Every pair uses two separate exposures of the named subject or group. The two Kabosu exposures are 30 seconds apart at one event; they count as one case. Each initial photo is assigned by a fixed seeded shuffle after visual curation, without consulting predictions. Both candidates receive the same initial photo. ViT receives the listed second photo as well; ResNet never receives it.

| Cohort | Cases | Primary or diagnostic denominator |
|---|---:|---|
| Supported single dogs: Blanco, Fala, Koni, Laddie Boy, Liberty, Rob Roy | 6 | Report coverage, correct reports, wrong reports among reports |
| Non-dogs: Larry the cat, Frankel the horse, modern Shibuya Hachiko sculpture | 3 | Prohibited breed reports, counted per case |
| Kabosu, a source-reported Shiba Inu outside both label spaces | 1 | Unsupported-breed proposals; excluded from supported accuracy |
| Yuki, source-reported mixed ancestry | 1 | Cautious visual-match proposals; no ancestry accuracy claim |
| Susie and Shay, owner-described collies | 1 | Shared breed-description group and report-scope diagnostics; exact subtype unverified |
| Buffy and Yume, source-described Bulgarian shepherd and Akita | 1 | Different-breed group; a standalone report needs subject selection |

The six supported dogs span five labels, with two white collies. Five are historical US presidential pets and one is Koni. Their archival style, small native images and limited breed coverage constrain generalization. These cases add new identities without eliminating the earlier collection's source bias.

Source captions, primary archive descriptions, license records and human visual review establish the annotations. They do not independently establish pedigree. Blanco's archive pages identify both photographs and their public-domain status. The LBJ Library describes Blanco as a collie and Yuki as mixed breed; the same source dates Her's death to 1964, contradicting a Commons caption that places her in a 1966 photo. That proposed beagle pair is excluded. [LBJ Library](https://www.lbjlibrary.org/life-and-legacy/the-man-himself/lbjs-dogs).

Fala's living-dog photos have not been classified here before. Two images of a sculpture depicting Fala were viewed and excluded during earlier curation, without inference; that human exposure is disclosed. [Fala's breed](https://www.nps.gov/articles/fala.htm). Rob Roy and Laddie Boy's labels follow the White House Historical Association's descriptions. [Rob Roy](https://www.whitehousehistory.org/white-house-pets/top-dogs-at-the-white-house), [Laddie Boy](https://www.whitehousehistory.org/photos/photo-2-3). Liberty and Koni's source photo captions specify their breeds. Kabosu's reported breed is Shiba Inu, which is absent from the pinned label maps. [Kabosu](https://foundation.dogecoin.com/blog/2024-05-24-kabosu-obituary/).

One Hachiko candidate contains live cats at the sculpture's feet; it does not provide the intended view of the dog depiction. Other candidates obscure the sculpture with a crowd or repeat a wide view. The chosen pair uses a visible full-scene view and a closer, partly occluded view while someone measures the sculpture. These exclusions occur before inference. They leave this pair dependent on that framing, not a general depiction benchmark.

## Fixed methods and report scope

**ResNet:** retain the previously selected rule, with native global top class in domestic-dog IDs 151–268, score at least 0.8, and margin at least zero. Use the pinned ResNet-50 revision and its own slow processor, float32 on MPS. Do not renormalize dog scores. Make exactly one prediction per case, on its assigned initial photo. This rule has no separate image-quality gate.

**ViT agreement:** use the pinned application classifier on both photos. Set score and margin floors to zero in the isolated diagnostic process, require two distinct classified photos, and retain existing inspection, quality, unresolved-label, disagreement and current-photo restrictions. Save the actual `compare` and `build_report` outputs. This is a comparison of complete reporting candidates, whose quality checks differ; it does not isolate the classifier architecture alone.

Each classifier receives metadata-free normalized image pixels, using the unchanged application normalization. Neither receives the case's expected label, source caption, cohort or file title. Metadata and annotations remain in the evaluator. The classifier worker consumes only a path to the normalized file and opens its pixels; there is no text prompt.

Keep proposed labels separate from a valid product report. For an individual real dog of unknown ancestry, the owner permits a cautious visual match without an ancestry claim. For multiple dogs sharing a breed, a clearly labeled scene report is permitted. Susie and Shay's owner calls both collies, but their exact subtype and ancestry are unverified; report proposals and compatibility with that broad description without certifying exact scene-breed accuracy. Buffy and Yume are source-described as different breeds; any unscoped label proposal requires subject selection before a standalone report.

Ground-truth scope annotations never suppress a classifier output or rescue a gate. They are used after prediction to identify unresolved scope obligations. No oracle suitability check is added to either candidate. The current application contract cannot implement these distinctions, so this experiment cannot establish product readiness even if the primary numeric targets pass.

## Criteria, ordering and terminal conditions

For each candidate, the owner's numeric targets become: at least 3/6 supported cases reported, no more than 10% wrong reports among those reports, and zero reports on the three non-dog cases. With at most six supported reports, any wrong report fails the error target. A single non-dog report fails rejection. Unsupported-breed and scope cohorts retain their own counts and cannot inflate supported coverage or be silently counted as prohibited non-dogs.

Order non-dog cases first, supported cases second, and the four diagnostic cases last. This exposes an irreversible rejection failure cheaply. Complete the fixed schedule after a valid unfavorable prediction to retain the coverage and scope evidence needed to judge direction. Do not add examples, swap initial photos, tune thresholds, combine the candidates, or try vision in response to the results.

Run ResNet's 13 initial-photo calls, unload it, then run ViT's 26 calls. Each worker request has a 60-second bound, including first loading. A runtime error aborts remaining calls and prevents a completed comparison; retain the attempted call and all previous outputs. Also abort on concurrent app work or unexpected model residency. Check source, input, processor and weight hashes before and after the run. An existing results file prevents an automatic rerun.

If neither candidate meets the primary targets, keep both out of the app and use the recorded failure type to choose a new investigation. If exactly one passes, it advances only to a bounded workflow study after unresolved scope obligations are addressed. If both pass, prefer evaluating the one-photo acquisition path next; this is a burden preference, not proof of greater accuracy. A different outcome may justify another registered experiment, never an undeclared continuation of this one.

Report the paired case outcomes, disagreements between the candidates, per-cohort totals, and nominal acquisition budget of one versus two photos. The photo burden is assigned by design; there are no measured user requests, retake success rates, elapsed collection times or user-effort estimates. Retain per-call timing with first loading identified. Do not add memory instrumentation or present a whole-app latency comparison.

## Preservation and execution

The runner prepares normalized images, quality observations, shuffled initial-photo assignments and a manifest without inference. Registration captures the runner, reused evaluation helpers, application sources, pinned model files, package versions, annotations and this protocol. Raw outputs and full native ResNet scores are retained separately from the final accounting. Verification rebuilds pair comparisons and report candidates from saved observations without generation and checks every planned call and denominator.

```sh
PYTHONPATH=. .venv/bin/python scripts/evaluate_new_identities.py prepare
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH=. sandbox-exec -f scripts/offline.sb .venv/bin/python scripts/evaluate_new_identities.py run
PYTHONPATH=. .venv/bin/python scripts/evaluate_new_identities.py verify
```

Inference stays under the repository's offline network sandbox. The app remains idle and uses its existing Qwen3 controller and reporting policy. This registration replaces neither the previous stopped vision protocol nor its evidence.
