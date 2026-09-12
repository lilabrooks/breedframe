# New-identity comparison: both candidates miss coverage

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

**Neither fixed reporting candidate met the owner's coverage target.** Single-photo ResNet and two-photo ViT agreement each reported on 0/6 supported cases. Both rejected the three non-dog cases, and both abstained on all four diagnostic cases.

The comparison completed all 39 scheduled classifier calls: 13 ResNet calls and 26 ViT calls. It used 26 newly selected photos, with the initial photo assigned before inference. There were no controller decisions, vision calls, threshold changes or application changes. [Frozen protocol](identity-comparison-protocol.md) · [Registration](evidence/identity-comparison/protocol.json) · [Manifest](evidence/identity-comparison/manifest.json).

## Case-level results

| Cohort | Cases | ResNet reports, one photo per case | ViT reports, two photos per case |
|---|---:|---:|---:|
| Supported breeds | 6 | 0 | 0 |
| Non-dogs | 3 | 0 | 0 |
| Unsupported breed, Kabosu | 1 | 0 | 0 |
| Unknown ancestry, Yuki | 1 | 0 | 0 |
| Owner-described collie group | 1 | 0 | 0 |
| Different-breed group, Buffy and Yume | 1 | 0 | 0 |

Both candidates therefore have 0% supported-case coverage, below the required 50%. Error rates among reports are undefined because there were no reports. The negative controls alone cannot establish usefulness when every real-dog case also receives an abstention.

The earlier exposed cases yielded three correct reports out of six for each candidate under the matched acquisition comparison. That result did not carry over to this collection. These subjects are separate from prior classifier inference, but the source distribution remains narrow: five supported dogs are historical US presidential pets, two are white collies, and public-image training overlap is unknown. This is evidence about these cases, not a population accuracy estimate for contemporary pet photographs.

## What prevented useful reports

All 13 ViT pairs disagreed on their leading label. Agreement failed with numerical floors already at zero; lowering those floors cannot create agreement. All 26 images passed the existing quality checks, so those checks did not explain the complete abstention.

ResNet's raw leading label was correct on only one of the six supported initial photos. ViT was also correct on one of those initial photos and on one of the twelve supported photos overall. Both correct initial predictions were Laddie Boy, the Airedale. ViT's second Laddie photo instead led with Scottish deerhound.

| Supported case | Expected label | ResNet first choice | Native score |
|---|---|---|---:|
| Blanco | Collie | Golden retriever | 0.7486 |
| Fala | Scottish terrier | Groenendael | 0.6236 |
| Koni | Labrador retriever | Curly-coated retriever | 0.2952 |
| Laddie Boy | Airedale | Airedale | 0.6626 |
| Liberty | Golden retriever | Irish setter | 0.4585 |
| Rob Roy | Collie | Book jacket | 0.8070 |

The five dog labels fall below the frozen 0.8 score requirement. Rob Roy's higher score belongs to a non-dog class, so it also fails the rule.

**Thresholds alone cannot meet the owner's targets on these six ResNet outputs.** Only one correct leading label is available, while coverage requires at least three reports and the error limit permits no wrong reports at this sample size. There is also a concrete score/margin conflict: wrongly labeled Blanco exceeds correctly labeled Laddie in both score (0.7486 versus 0.6626) and margin (0.7043 versus 0.5374). Any pair of minimum score and margin floors admitting Laddie also admits Blanco. This follows from the stored predictions; no threshold sweep or new inference was performed.

[Full native predictions and saved reports](evidence/identity-comparison/results.json) · [Raw correctness, cohort totals and threshold argument](evidence/identity-comparison/summary.json).

## What the inputs show

After the fixed run, the saved processors were applied to the six initial images to inspect their actual input composition. This generated no classifier predictions and changed no evaluated inputs.

Fala remains a small dog among people and scenery. Liberty and Koni share substantial space with people. Blanco is prominent yet misclassified, while ResNet's crop clips the top of Laddie's head and still yields the correct leading label. These observations support investigating framing; they do not establish that framing caused the errors or that cropping will fix them.

[Processor input comparison](evidence/identity-comparison/processor-inputs.png) · [Tensor shapes and hashes from the inspection](evidence/identity-comparison/processor-inspection.json).

## Historical direction, superseded at closeout

Keep both candidates out of the app. The next useful experiment is a registered comparison of full-frame inputs with manually marked dog regions on these fixed failures and the correct Laddie control. Keep the classifier and its processor fixed, record how much of each frame is retained and the region's native resolution, and measure whether the leading breed ranking improves. Small source regions cannot acquire missing detail through enlargement.

That study would measure the value of supplied regions. Automatic subject selection, rejection of non-dogs after cropping and multi-dog report scope would still need their own evidence before product adoption. A manual-region result cannot establish those capabilities. If the regions do not improve ranking, stop that intervention and reconsider classifier suitability and the intended photo distribution before adding more orchestration.

Qwen3.5 suitability screening remains unmeasured. Under a fixed reporting rule, a screen that only removes reports cannot raise coverage from zero. This round supplies a breed-ranking problem to investigate before spending effort on that rejection-only role. A controller swap also has no demonstrated remedy for these stored ranking failures.

The owner-described collie group does not establish a precise shared subtype, and the current report contract lacks the accepted individual-versus-scene distinction. Both group cases abstained here, leaving those output paths unvalidated. Unknown ancestry remains eligible for cautious visual matching; Yuki's abstention is retained as an availability result rather than a prohibited-input success.

## Preservation

Publication cleanup later formatted the maintained runners and changed UI copy. The [measured-source archive](evidence/frozen-sources/README.md) preserves the registered bytes and documents restoring them in a disposable checkout. Both original input guards passed after restoration; saved case outcomes were reproduced without inference. Current publication files are not presented as the original measured sources.

The runner verified all 39 planned calls and reproduced the 26 candidate case outcomes, comparisons and reports from saved outputs without inference. Input, application, processor and weight hashes remained unchanged. The model files also matched their preserved download/audit records. [Verification](evidence/identity-comparison/verification.json).

Inference ran under the repository's offline sandbox. The ordinary app remains ready and idle with Qwen3 4B, its original ViT and its original reporting policy. Both experiment classifier processes were closed; no Ollama model is resident. Timings retain first loading per classifier, but this was not a whole-app resource comparison. [Photo attribution and source records](evidence/identity-comparison/attribution.md).
