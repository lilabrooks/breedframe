# Review 02: methods, model use and direction

Second independent review, 2026-09-11. No earlier review document exists here
(`docs/` holds only `review-prompt-2.md`, and git has no commits yet), so this
one is self-contained.

Everything below comes from the recorded evidence and the source. I ran no
inference, changed no configuration, downloaded nothing, and consumed no
reserved data. The one thing I executed is a pure call to
`breedframe.policies.decision_context` on a case dict rebuilt from
`docs/evidence/paired-reserved-forced-v2.json`, to check what the controller was
actually permitted to do at one recorded turn.

## Verdict

Subject selection should not be the next work, and the ResNet rejection should
be reopened. The last three rounds measured a configuration rather than a model
capability. Three settings, each checkable in minutes, made those experiments
incapable of producing a non-zero result.

1. `MIN_SCORE = 0.5` ([evidence.py:5](../breedframe/evidence.py#L5)) is higher
   than every ViT classification this project has ever recorded. The maximum
   leading score anywhere under `docs/evidence/` is **0.476691** (the pug demo
   image, a clean and correct call, in `evaluation-results.json`). On the v2
   corpus the maximum is **0.222815**. Count of recorded observations at or
   above 0.5: **zero**. The app cannot report a breed on any image it has ever
   seen.
2. The `direct` arm of the paired comparison is not gated at all
   ([evaluate_pairs.py:105-110, 121-128](../scripts/evaluate_pairs.py#L121)),
   while `rules` and `agent` report only through the 0.5 gate. So "Direct 3/4,
   Rules 0/4, Qwen3 0/4" is a comparison of two reporting policies. Direct
   under the same gate is 0/12, and that number is already in the repository
   (`classifier-audit/threshold-replay.json`, `individual_photos`, s=0.5).
3. Both controllers stop without classifying the current photo whenever any
   earlier ranking exists. Across the four forced-pair runs (7 pairs per model),
   the CLI demo and the browser demo, supplied second photos classified:
   **0 of 16**. Under the replay's `recorded_agent_forced` scenario, report
   eligibility is zero at all 30 threshold cells, because the current photo has
   no ranking. No threshold change can rescue the follow-up path while that
   holds.

None of the three is a statement about model capability. Until at least (1) and
(3) are fixed, every further orchestration experiment will keep measuring a
constant, and "no controller advantage" will keep being true for reasons that
have nothing to do with the controller.

**The decision that should change now:** stop treating the absolute-score floor
as given. The app already contains a reporting rule that meets the owner's
coverage and error criteria on the existing photographs (cross-view
leading-class agreement), and the score floor is what hides it. That is a
one-constant change plus one condition, with no new model, no detector and no
new data.

## What the evidence establishes

- The ViT ranks reasonably and calibrates terribly. Raw top-1 correct on 12
  labeled photos: 8/12. Highest score on any of those 20 images: 0.2228. The
  audit checked preprocessing, the processor tensor, the softmax and MPS/CPU
  agreement and found no defect, so the flat scores are a property of the
  fine-tune, not the pipeline.
- Absolute softmax mass does not separate suitable from unsuitable inputs for
  this ViT. The dog sculpture scores 0.1808 with margin 0.1377, third highest
  of all 20 images. Any score cutoff admitting champ-01 (0.1843) admits the
  sculpture.
- Cross-view agreement does separate them, on the dogs. Of 7 same-dog pairs,
  the 3 whose leading class agrees across both photos (Sully, Champ, Barney)
  are all correct; the 4 that disagree (Buddy, Millie, Conan, Bo) each contain
  at least one wrong or out-of-class prediction. With no score or margin floor,
  the replay's `paired_evidence` scenario gives 3/6 eligible, 3 correct, 0
  wrong. That is 50% coverage and 0% error among reports, which clears both of
  the owner's quantitative bars using the owner's own classifier.
- ResNet-50 carries real score signal. Its 9 correct calls sit between 0.7618
  and 0.9997; its 3 supported-breed errors sit at 0.3964, 0.4107 and 0.4105.
  Its global 1000-class space also self-rejected four hard inputs by putting a
  non-dog class on top: cat-01 (Egyptian cat), horse-01 (sorrel), bo-01
  (groom), conan-01 (suit of clothes).
- The ViT and ResNet-50 are correct on different photos. Union of correct:
  10/12. Both correct: 7/12. Where their mapped leading labels agree, all 7 are
  correct, and none of the cat, horse, sculpture, Bo, mixed-ancestry or
  Champ-and-Major images produce agreement.
- Qwen3 4B can do the behavior the project now says it can't demonstrate. The
  v1 evaluation records 2 correct visual reports and 2 follow-up requests
  (`evaluation-results.json`). It also records 1 wrong report (checkerboard to
  pug) and 3 rejected invalid requests. The capability is there; the current
  configuration suppresses it.

## What the evidence cannot establish

- Any rate. 12 labeled photos are 6 dogs. 3/3 and 0/3 on 6 subjects is
  compatible with a wide band of true values.
- Non-dog rejection by any policy. "Zero false reports" accompanies "zero
  reports", which the docs say plainly and correctly.
- Non-dog rejection by the agreement rule specifically. Every non-dog,
  multi-dog and unknown-ancestry case in this corpus is a single image, so a
  two-photo rule can never be exercised on them. Its zero on those cohorts is
  arithmetic, not evidence.
- Whether ResNet-50's near-1.0 confidences reflect competence or exposure. It
  is ImageNet-1k trained, Stanford Dogs is an ImageNet subset, and these are
  widely republished archive photographs. 0.9997 on a photo is also what
  memorization looks like.
- Anything about immediate retakes. The pairs span months to years and Buddy
  changes age.
- Anything about follow-up usefulness with a model in the loop, because the
  model never classified a follow-up.

## Prioritized findings

### Demonstrated flaws

**F1. Critical. The reporting gate is unreachable by the default classifier.**

`MIN_SCORE = 0.5` and `MIN_MARGIN = 0.15` at
[evidence.py:5-6](../breedframe/evidence.py#L5), applied in `weak()` at
[evidence.py:19](../breedframe/evidence.py#L19), and required for eligibility at
[evidence.py:52](../breedframe/evidence.py#L52). Sweeping every leading-candidate
score under `docs/evidence/` (excluding the ResNet screen): maximum 0.476691,
observations at or above 0.5: 0. `evidence-comparison.md` describes the
thresholds as having "proved too restrictive to produce any breed reports in
this sample", which frames a configuration error as a finding about the sample.

Consequence: the app reports nothing, ever. The spec's required outcome
(spec.md, "a visible, model-controlled investigation, including a case that asks
for another photo") is no longer reproducible with defaults, which
`evidence-comparison.md` notes as a demo regression. Three experiments (v2
paired, the Qwen3.5 comparison, the forced-pair scenarios) spent real inference
time measuring a value fixed at zero.

Correction: drop the absolute-score floor. See F5 for what replaces it.

Counterargument: a conservative gate that never fires is a defensible failure
direction for a product that disclaims certainty, and the docs never claim
otherwise. Fair, but the same gate is also what makes the orchestration
comparison uninformative, and the app still prints the ungated label one button
away (F2), so the conservatism is not consistent.

**F2. Critical. The three-policy table compares reporting policies, not
orchestration.**

For `direct`, candidates come straight from the classifier output
([evaluate_pairs.py:105, 121-126](../scripts/evaluate_pairs.py#L121)). For
`rules` and `agent` they come from `case["report"]["candidates"]`, which
`build_report` fills only when `outcome == "visual_matches"`
([evidence.py:169](../breedframe/evidence.py#L169)). `summarize()` then counts
"reports" identically for all three
([evaluate_pairs.py:36-37](../scripts/evaluate_pairs.py#L36)).

The same asymmetry is in the product. `app.js:151` prints
`scotch terrier · 0.053 raw score` for the baseline button while the agent's
verdict on the same photo is "inconclusive".

Consequence: README's "Correct breed reports / all eligible dogs: 3/4, 0/4,
0/4" and spec.md's "The fixed three-way evaluation found no controller
advantage" read as orchestration results. They are gate results. The
counterfactual is already recorded: gated direct is 0/12.

Correction: add a gated-direct column from cached scores (zero new inference)
and say in README, spec.md and evidence-comparison.md that the maximum recorded
ViT score is 0.2228 on this corpus, so no gated policy could report.

Counterargument: the point of the baseline was always "what would a bare
classifier print", and evidence-comparison.md does say the abstention result is
not evidence of rejection. True, but it never says the gate alone accounts for
the entire difference, and a reader will not derive that.

**F3. High. Both controllers skip classifying the current photo whenever an
earlier ranking exists.**

Supplied second photos classified: Qwen3 0/3 development and 0/4 reserved
(`paired-*-forced-v2.json`), Qwen3.5 0/3 and 0/4
(`controller-comparison/*-forced.json`), plus `cli-demo-v2.json` and
`browser-comparison-v2.json`. 16 opportunities, 0 classifications. In the
browser run the second photo got a ranking only because the user drew a region,
which `policies.py:28` then forces.

I checked whether that was a choice. Rebuilding the Sully forced-pair state
just before event 5 and calling `decision_context` returns:

```
allowed_tools            : ['classify_breed', 'finish_assessment', 'request_another_photo']
actions_remaining        : 5
blockers                 : ['The current photo has no classifier result.']
finish outcome constraint: {'const': 'inconclusive', 'type': 'string'}
tools offered in grammar : ['classify_breed', 'finish_assessment', 'request_another_photo']
```

`classify_breed` was in the grammar, 5 of 6 attempts remained, and the state
told the model in plain words what was missing. Qwen3 chose `finish_assessment`
with a schema-forced `inconclusive`. Qwen3.5 on the same case did something
worse: it asked for a third photo with reason `insufficient_evidence` while
declining the free evidence in hand (`reserved-forced.json`, sully, ev5).

So this is a controller choice, not a schema restriction, not a budget limit
and not an orchestration defect.

Consequence: under the replay's `recorded_agent_forced` scenario, report
eligibility is 0 at all 30 threshold cells because the current photo has no
ranking. The skip is a hard blocker on the entire follow-up path, independent
of any threshold work. Fixing the gate alone leaves the follow-up path at zero.

Mechanism worth one cheap test: two independently trained models with different
weights and tokenizers took the identical unusual action all 16 times, which
points at the shared stimulus rather than at either model. At the photo-1
post-inspect turn, `comparison.candidates` is empty and `relation` is
`no_ranking`, and both models classify. At the photo-2
post-inspect turn, `comparison.candidates` is already full of photo-1's five
candidates and `relation` is `single_photo`, and both models stop. The current
photo's status lives one level down, inside
`comparison.views[-1].rankings == []`.

Correction: state it at the top level. One key, `current_photo_classified:
false`, and put `blockers` first in the state JSON. If both models still skip,
the input isn't the cause, and the honest move is to classify each new photo
deterministically before consulting the controller, exactly as `RulesController`
already does.

Counterargument: the model may simply have no room to reason. `think=false`,
`/no_think` appears twice in the prompt, and the grammar forces the first token
to open the JSON object, so there are zero deliberation tokens (`eval_count`
35-47 across recorded turns). On that reading the fix is thinking mode, not
legibility. I'd still try the free change first: thinking would multiply a
latency already at 10.6 s per case against a 45 s controller timeout, and the
spec's "never hidden reasoning" pushes the other way.

**F4. High. The ResNet-50 screen could not have passed, and its failure
definition contradicts the product contract.**

`screen_classifier.py:35` defines `unsuitable` as every report in any cohort
other than `supported_breed`. That folds four different things together:
non-dogs, a live dog of an unsupported breed (Bo), scenes with two dogs, and a
live dog of unknown ancestry (Topper).

Two images make the criteria unsatisfiable by any score/margin gate, not just
the 117 tested:

- multi-02 (Champ and Major, both German Shepherds) scores 0.9998 with margin
  0.9997, higher than every supported-breed photo. Every threshold that admits
  any report admits it.
- mixed-01 (Topper) scores 0.9814. Excluding it requires a cutoff above
  0.9814, which leaves 5 of 12 supported photos, or 41.7% coverage, below the
  50% bar. Admitting buddy-01 at 0.9680, which you need for 6/12, admits
  mixed-01.

So `passes_development_screen: false` was fixed before the model ran. The
"cheap exit" was not a cheap signal; it was the full criteria, and it could
only fire.

Now the definitional half. The product's own words are "Report **likely visual
breed matches**. Scores are uncalibrated classifier outputs, not ancestry
percentages. Candidates are alternatives" (spec.md), and in the UI, "Scores are
model outputs, not ancestry percentages. A photo cannot establish a dog's
genetic breed" (`index.html:23`). Against that contract:

- Topper: source-described mixed-breed terrier, ResNet says West Highland white
  terrier at 0.9814. That is a plausible visual resemblance claim about a
  terrier, and it is precisely what the product promises to deliver. The app
  has no way to express an ancestry claim at all: `FinishArgs` is
  `outcome` plus `selected_result_id`
  ([contracts.py:37-39](../breedframe/contracts.py#L37)) and the report attaches
  `LIMITATIONS` verbatim. So a report on a mixed-breed dog is not wrong under
  the contract, and ancestry uncertainty is not determinable from pixels by any
  mechanism in or proposed for this system.
- Bo: Portuguese Water Dog, ResNet says standard poodle at 0.3544. Curly-coated
  water dog resembling another curly-coated water dog is a defensible
  resemblance output, and the README already warns that an unfamiliar breed can
  receive a leading match.
- multi-02: two German Shepherds, answer "German shepherd". Wrong only against
  a promise about one selected dog. It is unsuitable for an unselected-subject
  report, not for every possible report.
- statue-01: standard schnauzer at 0.5347. This one is a real error under any
  reading.

With "unsuitable" restricted to non-dogs, ResNet-50 at score >= 0.8 gives 8/12
coverage, 0 wrong among reports, and 0/3 non-dog reports. At >= 0.9 it gives
6/12, 0 wrong, 0/3. Both clear all three of the owner's criteria as the owner
worded them.

Consequence: the classifier screen's conclusion, and the pivot to subject
selection that followed it, rest on a cohort definition rather than on measured
model quality.

Counterargument, and it has real force: the owner did select "zero
unsuitable-input reports" (`development-protocol.json`,
`criteria.owner_selected: true`), and the photo-set doc marks both multi-dog
cases as "target selection needed", so counting an unselected-target report as
wrong was the design intent. Also, the statue is excluded at >= 0.6 only
because it happens to score 0.5347. One image is not a mechanism, and a
sharper, better-lit dog sculpture would likely score higher. So ResNet's clean
non-dog column is partly luck, and I would not claim it as depiction rejection.

**F5. High. The score floor and the cross-view agreement rule compete for the
same coverage, and the floor is winning.**

`compare()` already blocks a report when leading classes differ across recorded
views ([evidence.py:73-80, 129](../breedframe/evidence.py#L73)). On the existing
corpus that rule is doing the work the score floor is credited with:

| ViT rule on the 7 pairs | Reports | Correct | Wrong | Coverage on 6 labeled dogs |
|---|---:|---:|---:|---:|
| Agreement only, no floors (`paired_evidence`, s=0, m=0) | 3 | 3 | 0 | 50% |
| Agreement plus margin >= 0.15 (s=0, m=0.15) | 1 | 1 | 0 | 17% |
| Current gate (s=0.5) | 0 | 0 | 0 | 0% |

Adding the margin floor on top of agreement cuts coverage from 3 to 1, because
Sully's and Champ's current photos have margins of 0.0485 and 0.1309. The
floors and the agreement rule are alternative mechanisms, and combining them
destroys the only one that reaches the owner's coverage bar.

Correction: make a breed report require at least two classified photos of the
case with an agreeing leading class, and drop the absolute-score floor. Keep
everything else (quality flags, unresolved labels, current-photo requirement).

Counterargument: this is a rule I found by looking at outcome data on 6 dogs,
which is the most dangerous kind of hypothesis. It also cannot be tested for
unsuitable inputs on this corpus, since all of those cases are single images.
And it changes the product: every breed report now needs a second photo. I'd
note that last part cuts both ways, because a second photo is exactly the
request/resume path spec.md requires as its headline outcome.

**F6. Medium. The crop pilot cannot support the conclusions drawn from it.**

`crop-pilot-manifest.json` records the reasoning used to pick all three images
before inference: barney-01, "cropping cannot recover missing face detail";
buddy-01, "Dog occupies most of the frame; small framing change"; bo-01,
"Severe occlusion... breed outside classifier classes". Two were chosen with a
written expectation of no effect and the third has no label.

What the crops actually were: barney-01 99x88 px from a 304x210 source, flagged
`low_resolution`; buddy-01 884x708 from 960x785, a 92% crop and effectively a
no-op (score 0.0658 to 0.0662); bo-01 97x112, flagged `low_resolution`,
unlabeled.

So "raw top-1 correctness fell from 1/2 to 0/2" is one image flipping, in a
denominator of 2 where the other case was a deliberate no-op. And 2 of 3 crops
were upsampled into a 224 px model. Worth noting that barney-01's crop roughly
doubled its score and margin (0.0532/0.0115 to 0.1162/0.0885) while changing
the label to a wrong one.

The pilot also contains no multi-dog image, which is the one case where region
selection has an obvious mechanism. So evidence-comparison.md's "selecting a
rectangle cannot recover an occluded body or missing face" is a mechanism claim
from n=1 about a question the pilot didn't pose.

Correction: stop citing the pilot as evidence about cropping generally. The
untested cases are the interesting ones: conan-01 (1280x853, ResNet's global
top class was "suit of clothes") and multi-02 (1280x853, two dogs). Both are
large enough to crop above 224 px.

**F7. Medium. Region selection currently blocks reports instead of resolving
them, which undercuts the proposed direction.**

`compare()` appends every ranking event's leading class to the parent photo's
`leading_class_ids` ([evidence.py:51](../breedframe/evidence.py#L51)), and any
set larger than one becomes a disagreement blocker
([evidence.py:76-80](../breedframe/evidence.py#L76)). In the crop pilot,
barney-01's region disagreed with its parent frame and the case ended
`relation: disagreement`, with 0 breed reports across all three images.

Consequence: if the plan is "select the subject, then report", then selecting
the subject and getting a different answer than the whole frame is exactly the
case the current semantics refuse to report. spec.md's "A crop shares its
parent photo's vote" prevents double counting, but the side effect is that an
explicit human subject selection cannot override an unselected whole-frame
reading.

Correction: before any subject-selection work, decide that a user-selected
region supersedes its parent frame's vote for the current photo. Small, local
change in `compare()`.

**F8. Medium. No v2 photograph triggers a quality flag, so the request signal
that produced v1's requests was absent from every case.**

All 20 images have `quality_flags: []` (`threshold-replay.json`, every
observation). The flag thresholds are min dimension < 160, mean luminance < 35
or > 225, Laplacian variance < 25
([images.py:45-51](../breedframe/images.py#L45)). barney-01 at 304x210 and
multi-01 at 330x220 both clear the resolution test.

In v1, the two cases where the agent requested a photo were the ones that did
flag: golden-tiny at 48x32 (`low_resolution`) and the dark image
(`exposure`, `low_detail`). v1 also produced 3 invalid `low_resolution` claims
on unflagged images, which v2 correctly eliminated by making `request_reasons`
a schema enum ([policies.py:39](../breedframe/policies.py#L39)).

Consequence: in v2 the only reasons ever on offer were `ambiguous_scores` and
`insufficient_evidence`, both generic. "Qwen3 did not request follow-ups" is
jointly caused by the corpus (no concrete defect to cite) and the gate (no
follow-up could ever produce a report). Under an unreachable gate, declining to
burden the user with a futile request is the better decision, and the one
behavioral difference in the data that favors the model controller (0 requests
vs the rules policy's 11, of which 7 were unsatisfiable) is recorded but never
credited as such.

**F9. Medium-low. Two declared metrics cannot fire.**

`summarize()` in `evaluate_pairs.py` has counters for non-dog, unsupported
breed and multi-dog reports, and none for unknown ancestry. Topper's report
(`mixed-01`, direct: borzoi) lands in no cohort counter at all, because
`live_dog_present` is true and `kind` is `unknown_ancestry`. The plan's declared
"Topper | Unsupported ancestry claims" row is unmeasured by the paired runner.

And it could only ever be zero: the report format has no free text, so the
system cannot express an ancestry claim. The cohort as implemented measures "do
we name a breed for a mixed dog", which is a coverage prohibition, not an error
rate.

**F10. Low. The controller is told the thresholds from a duplicated literal.**

`policy_note` hardcodes "Score >= 0.5 and margin >= 0.15" at
[evidence.py:130](../breedframe/evidence.py#L130), separate from the constants at
lines 5-6. Change the constants and the model gets stale numbers. One f-string
fixes it, and it matters as soon as anyone tries a threshold experiment.

**F11. Low. The proposed 44-image collection cannot answer the questions the app
raises.**

`classifier-screen.md` specifies "One image per subject or scene in this first
study, 44 images total". A single-image-per-subject set can validate a
single-photo reporting threshold and nothing else: no multi-photo agreement, no
follow-up usefulness, no request/resume path. `classifier-screen.md` says as
much in its last paragraph. Collection is the expensive step, so ordering a
single-image collection ahead of a paired one means paying for it twice.

It also drops the gap the photo-set doc correctly named: "a naturally blurred
view followed by a sharp view, and a poorly exposed view followed by a
better-lit view". Those are the only images that would give the request path a
concrete reason to cite (F8).

### Credible risks

- **ResNet-50's confidences may be exposure, not competence.** ImageNet-1k
  training, Stanford Dogs is an ImageNet subset, and these are heavily
  republished archive photographs. Both Millie files carry a
  `source_file_timestamp` of January 2010 (`manifest.json`), so they were public
  on Commons well before this project existed; whether they reached ImageNet is
  unknown and unknowable from here. The screen says training overlap is unknown,
  which is right, and 0.9997 is also what memorization looks like.
- **The ViT/ResNet comparison is confounded by preprocessing geometry.** The
  ViT processor squashes to 224x224. ResNet's own processor resizes the shortest
  edge to 224/0.875 and center-crops (`development-results.json`, `processor`:
  `shortest_edge` 224, `crop_pct` 0.875, bicubic, ImageNet normalization). So
  ResNet gets an uncontrolled center crop for free. Using each model as
  published was the right call, but "ResNet ranks better" currently mixes
  weights with framing.
- **Corpus steering.** 6 dogs, 5 breeds, mostly US government archives, all 20
  images now exposed. The docs say this repeatedly and honestly. The risk is the
  decision pattern: three rounds of work have now been gated on this one set,
  and two of the screens turned on single images inside it. The ViT threshold
  grid's ceiling of 2/12 comes from the sculpture at 0.1808; the ResNet screen's
  failure comes from multi-02 at 0.9998 and Topper at 0.9814.
- **My agreement rule is post hoc.** I derived it from outcome data on the same
  exposed images. It happens to exclude both cases that sank the ResNet screen,
  which is suspicious rather than reassuring. multi-02's exclusion is luck: the
  ViT called it Norwegian Elkhound. Had the ViT been right, agreement would
  report it.

### What each proposed mechanism can actually establish

| Mechanism | Establishes | Does not establish |
|---|---|---|
| 120-class breed ViT | A ranking among 120 dog classes | Whether the subject is a dog, is alive, or is one dog |
| 1000-class ImageNet classifier | Whether the frame's dominant object is one of 118 dog breeds. Rejected cat, horse, bo-01 and conan-01 by global top class | Depictions (statue-01 took a dog class at 0.5347); counting; which dog |
| Object detector | Where dog-shaped regions are, and how many | Whether they are live dogs. The original YOLO paper presents cross-domain generalization to artwork as a strength ([arXiv:1506.02640](https://arxiv.org/abs/1506.02640)), which is the same property that makes a detector fire on a sculpture. I did not run a detector on statue-01, so this is a mechanism argument and not a measurement |
| User-drawn region | Which subject the user means | Whether the region contains a dog; and today it can block the report (F7) |
| Cross-view agreement | That two independent views produce the same class. Blocked Bo, an out-of-class dog | Anything about single-image cases; untested on non-dogs |
| Cross-model label agreement | That two differently trained models concur. On these 20 images: 7 reports, 7 correct, 0 on any unsuitable input except multi-01 | A rate. Requires a 120-to-ImageNet label map, and 7 ViT labels are truncated and unmappable |
| Vision-capable controller | Natural-language visual observations | That it is a better breed classifier; changes the evidence boundary, so it is a different system, not a swap |

Detection, counting, subject choice, liveness and breed identity are five
separate questions. The current proposal names the first four as one goal
("establish a suitable, selected live-dog subject"), and no single added model
answers all of them.

## Model-use opportunities

Configuration changes, using models already exercised. No new evidence source,
no scope change.

| Change | Mechanism | Supporting evidence | Uncertainty | Cost | Falsified by |
|---|---|---|---|---|---|
| Drop `MIN_SCORE`; require two agreeing photos | Agreement across independent views carries signal that this ViT's absolute softmax mass does not | `paired_evidence` s=0/m=0: 3/6 eligible, 3 correct, 0 wrong. Bo blocked by disagreement | 6 dogs; zero evidence on unsuitable inputs; post hoc | 1 constant + 1 condition in `compare()` | Two photos of a cat agreeing on a dog class |
| Surface `current_photo_classified` and put `blockers` first | Two differently trained models skip the same action 16/16 times, so the shared stimulus is the suspect | Forced runs 0/3+0/4 and 0/3+0/4; cli-demo; browser-demo; the `decision_context` trace above | Might be the zero-deliberation output instead | 1 dict key | Both models still skip |
| Classify each new photo deterministically; leave the controller the follow-up and report decisions | `RulesController` already does this at 0.276 s/case against Qwen3's 10.589 s, and classified 4/4 follow-ups against 0/4 | `reserved-policy.json` summary | Shrinks the "model-controlled investigation" spec.md requires as the demo | Small refactor | The demo exposes fewer model-selected actions, reducing what the prototype demonstrates |
| Enable thinking, raise `num_predict` | There are currently no deliberation tokens: `think=false`, `/no_think` twice, grammar-constrained first token, `eval_count` 35-47 | `baseline-probe.json` requests; `controller.py:43-56` | Latency already 10.6 s/case against a 45 s timeout; spec.md discourages hidden reasoning | Zero code, large runtime | Behavior unchanged, or turns exceed the timeout |
| Fix the duplicated threshold literal | The model is told the policy in prose | `evidence.py:130` vs `:5-6` | None | One f-string | n/a |

Added visual evidence. Changes what the models see.

| Change | Mechanism | Supporting evidence | Uncertainty | Cost | Falsified by |
|---|---|---|---|---|---|
| Classify user-selected regions on the 4 badly framed images (conan-01, multi-01, multi-02, bo-01) | Region selection resolves subject ambiguity, which the crop pilot never tested | ResNet put "suit of clothes" on conan-01; multi-02 took German shepherd at 0.9998; both sources are 1280x853, so crops stay above 224 px | multi-01 is only 330x220 and will flag `low_resolution` | Minutes of local inference | Leading class unchanged, or the disagreement blocker (F7) kills the report anyway |
| Bring ResNet-50 in alongside the ViT and report only on mapped label agreement | Two differently trained models disagree on out-of-domain inputs, which is a real OOD signal | On these 20: 7 reports, 7/7 correct; cat, horse, sculpture, Bo, Topper, multi-02 all excluded by disagreement | Derived post hoc; needs a 120-to-ImageNet map; 7 truncated ViT labels are unmappable; costs 2 loaded models | 102 MB already downloaded; 0.041 s/image steady state | A fresh set where agreement is wrong, or where coverage collapses |
| Diagnostic: ResNet with a full-frame squash vs its own center crop | Separates weights from framing (see risks) | `processor` config in `development-results.json` | None; it's a diagnostic | ~1 s of compute on 20 images | Center crop turns out to explain most of the 9/12 |

Product scope changes. No model work.

| Change | Mechanism | Supporting evidence | Uncertainty | Cost | Falsified by |
|---|---|---|---|---|---|
| Require the user to select the subject before any breed report | Turns the multi-dog problem into a UI step. The editor and the forced-region policy already exist (`policies.py:24-29`, `agent.py:57-60`) | 2 of 13 cases are multi-dog; ResNet's gate failed only on multi-dog, Topper and the sculpture | Friction on every case; needs F7 fixed first | UI only | Users skip it and coverage drops |
| Restrict "unsuitable input" to non-dogs | The product promises visual matches and disclaims ancestry (`config.py:22`, `index.html:23`) | ResNet at >= 0.8: 8/12 coverage, 0 wrong, 0/3 non-dog, 0/2 Bo | The owner wrote "zero unsuitable"; this is a definition change and needs the owner | Definition only | Owner disagrees, in which case F4's impossibility result stands and no gate can pass |

## Three next steps, in order

**1. Make the reporting rule attainable, and restate the comparison.**

Resolves: does the app's reporting rule permit any report, and does the
recorded controller comparison carry information?

Do: replace the absolute-score floor with the agreement requirement already in
`compare()` (require `ranked_photo_count >= 2` and `relation == "agreement"`;
set `MIN_SCORE` to 0; leave `MIN_MARGIN` out of the current-photo test, because
m >= 0.15 cuts coverage from 3 to 1). Fix the `policy_note` literal. Then rerun
development policy and forced modes only: 6 cases and 3 pairs, 3 methods. Add
the gated-direct column from cached scores, no inference needed.

Fixed: ViT, Qwen3 4B, prompt, action schema, budgets, corpus, quality flags,
unresolved-label rule. The reserved split stays closed as a matter of form,
though the audit already established all 20 images are development evidence.

Cohorts and denominators: coverage over the 6 supported dogs; errors among
reports; Bo, 2 multi-dog, 3 non-dog and Topper reported separately with their
own denominators, as the plan specifies. Keep abstentions and failures in.

Advance if: the rule produces any reports at all, so the primary metric stops
being a constant. Record correctness as it falls out. A wrong report is
information here, and it is not a reason to retune the rule. Stop and check the
implementation if any single-image case produces a report, which the two-photo
requirement should make arithmetically impossible.

One prediction to register in advance: the agent arm of the forced-pair run
should still report nothing, because F3 blocks it regardless of thresholds. A
zero there confirms the diagnosis instead of refuting step 1.

Label the result honestly: a development-selected rule on fully exposed data,
and not a validated operating point.

**2. Test whether the skipped classification is an input problem.**

Resolves: is the 16/16 skip a legibility failure or a model limitation, and
does the follow-up path work at all?

Do: add `current_photo_classified` to the state dict and move `blockers` to the
front. Change nothing else in the prompt. Rerun the development forced-pair mode
with both pinned controllers.

Fixed: prompt text, schema, budgets, `think=false`, corpus, and the reporting
rule from step 1.

Denominator: 3 development pairs times 2 models, so 6 supplied second photos.
Count classified over supplied, plus requests and completion.

Advance if: 5 or 6 of 6 second photos get classified. Then the follow-up path is
live and cross-view agreement can actually be exercised by the model.

Stop if: both models still skip. Then the controller is not using the state, and
the right move is to classify each new photo deterministically and narrow the
model's role to the follow-up and report decision. Say so in the README rather
than describing the skip as a model property.

Cost: about 3 minutes of inference plus the edits.

**3. Only if step 1 produces reports: four paired unsuitable-input controls.**

Resolves: can the agreement rule reach zero reports on unsuitable inputs, which
is the owner's third criterion and the only one still open?

Do: add a second photograph for each of the cat, the horse, the dog sculpture
and one multi-dog scene. 4 images, through the existing `fetch_photo_set.py`
path with hashes, licenses and source URLs frozen as usual. These are controls,
not accuracy cases, so reusing the existing subjects is fine and correlation
with exposed images does not bias a deterministic classifier.

This is not sample extension to obtain success. The agreement rule currently
has zero measurable evidence on unsuitable inputs, because every such case in
the corpus is a single image. 4 paired controls are the minimum that produces
any observation, and the expected failure mode is concrete: two photos of the
same cat probably do agree on some dog class.

Advance if: none of the cat, horse or sculpture pairs produce cross-view
agreement on a dog class. Then the agreement rule reaches zero reports on
genuine non-dogs, and a fresh identity-disjoint evaluation set becomes worth
collecting, in pairs.

Stop if: any of those three agree. Then agreement does not reject non-dogs, and
subject suitability becomes the justified next problem. That is where the current
proposed direction legitimately re-enters, with a measured reason behind it.

The multi-dog pair is a separate reading. If it agrees, that answers owner
decision 1 rather than testing the rule: two German Shepherds agreeing on
"German shepherd" is the classifier being right, and whether it counts as a
failure depends on what the product promises about subject selection.

Tracing backwards: the expensive question is "should we build subject and
liveness detection". Step 3 decides it for 4 images. Step 3 is only meaningful
after step 1, which is free and uses recorded data. Step 2 is independent, costs
minutes, and unblocks the one path spec.md requires.

### Defer or abandon

- **Abandon** the absolute-score floor as a reporting mechanism for this
  classifier. No observation this project has ever recorded passes it.
- **Abandon** the crop pilot as evidence about cropping. Its 3 images were
  pre-judged as no-ops and 2 crops were upsampled.
- **Defer** automatic subject detection until step 3 shows agreement fails. If
  it does fail, note that detection answers "where are dog shapes", which
  leaves the sculpture unresolved.
- **Defer** the 44-image single-image collection. If collection proceeds,
  collect pairs, and include the blurred/sharp and dark/well-lit pairs the
  photo-set doc already identified.
- **Defer** Qwen3.5 vision, the 9B model and hosted controllers. No currently
  open question needs them, and the question they would address is not yet shown
  to be the binding one.
- **Keep** the existing 20 images as a regression set. Don't redefine any of
  them as a holdout.

## Owner decisions

**1. Does "zero unsuitable-input reports" include a real mixed-breed dog and a
photo of two dogs of the same breed?**

Recommendation: no. Restrict it to non-dogs (cat, horse, sculpture), and handle
multi-dog scenes as a scope statement plus user selection. The product's own
words promise visual resemblance and disclaim ancestry, the report format cannot
express an ancestry claim, and "West Highland white terrier" for a mixed terrier
is the product working.

Tradeoff: the app will name a breed for a dog whose ancestry nobody knows, and
some users will read that as an ancestry claim no matter what the disclaimer
says. If you'd rather keep the stricter reading, then F4's impossibility result
stands: no score/margin gate on any single-image classifier can pass, and the
screen's outcome told you nothing about ResNet-50.

**2. Is the ViT a fixed requirement, or may it be replaced?**

Recommendation: keep it for now, and decide after step 1. The agreement rule
reaches 50% coverage at 0% error with the ViT, so the coverage bar is reachable
without a swap. But the ADR calls it "the requested ViT", so replacing it is
your call, not an implementation detail, and the measured basis is now clear:
ResNet-50 is 9/12 raw against 8/12, its scores actually separate correct from
incorrect calls (0.76-0.9997 against 0.35-0.41), and it rejected 4 hard inputs
by global top class. Against that, its near-1.0 confidences on republished
archive photos may be exposure rather than competence.

Tradeoff: swapping loses the truncated-label honesty feature that spec.md asks
for and changes the README's attribution and the 120-class framing.

**3. Is the spec's required request/resume demonstration still a requirement?**

It is currently not reproducible with defaults: the tiny-beagle demo ends
inconclusive, and no recorded v2 run has the model requesting a photo. If it
still matters for the prototype, steps 1 and 2 are the cheapest route back to
it, because a two-photo reporting rule gives the model an actual reason to ask.
