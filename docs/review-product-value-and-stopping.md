# Review 03: product value, direction, and stopping

Historical review. The [final findings](findings.md#reading-the-final-review-accurately) qualify several claims below and record the adopted stopping decision. Source links for subsequently formatted runners point to their measured versions.

Third independent review, 2026-09-12. I read the specification, README, ADR, the
methods review and its response, the three studies completed since that
response, and the application source. I ran no inference, downloaded nothing,
changed no setting, and touched no file outside this one. Software tests were
out of scope and I did not read them.

The arithmetic below comes from the saved records under `docs/evidence/` and
from file metadata. Where I recompute a number the repository already states, I
say so.

## Verdict

**Stop model work. Run no further experiments, including the crop study.**

The prototype has produced a real engineering result, and it is finished. Every
question still open either needs data this project cannot collect and publish,
or has an answer that changes nothing about what ships.

Two assessments, kept apart on purpose.

**Prototype: nearly ready, and nothing left to measure.** The
engineering is sound and unusually honest. Four gaps remain, all of them
documentation or presentation, none needing a model. The largest is that the
repository has zero commits. `git log` returns "your current branch 'main' does
not have any commits yet". For a prototype intended to document experimentation,
that leaves its development history unrecorded.

**Breed reporting: failed, and well evidenced.** No configuration this project
has built meets all three of the owner's criteria on data it had not already
seen. That is the finding. Write it down and stop trying to repair it.

One thing to be blunt about. The shipped app has produced **zero breed reports
on every image it has ever processed**. I counted 645 serialized ViT
leading-class observations under `docs/evidence/`. Number at or above the 0.5
floor: zero. Highest ever: 0.476691, the v1 pug. Any documentation that
describes BreedFrame as a breed identifier is describing something that has
never happened.

## What works, what worked once, and what is unknown

| Capability | Status | Evidence | Claim you can make | Limit |
|---|---|---|---|---|
| Local-only execution with pinned weights | Current | `evidence/offline-smoke.json`; digest check in [config.py:9-14](../breedframe/config.py#L9) | Runs on one Mac with outbound networking denied except loopback; controller digest and classifier revision are enforced at startup | Verified on this Mac. Unified-memory counters are separate accounting views and are not additive |
| Schema-constrained action loop | Current | [contracts.py:90](../breedframe/contracts.py#L90), [policies.py:30-44](../breedframe/policies.py#L30), [agent.py:95-169](../breedframe/agent.py#L95) | Illegal actions are removed from the decision grammar each turn rather than discouraged in prose; invalid attempts consume budget and stay in the trace | When nothing is eligible, [policies.py:43-44](../breedframe/policies.py#L43) pins `outcome` to the constant `inconclusive`. "The agent decided to abstain" overstates what the model was allowed to do |
| Persistence, pause, resume, cancel, retry, partial close | Current | `evidence/demo-paused.json`, `demo-resumed.json`, `browser-partial-v2.json`, `browser-cancelled-v2.json` | A request pauses a persisted case and a new photo resumes it with prior observations and a fresh budget | Qwen3 4B triggered a request in 0 of 13 v2 cases. All 34 requests across the four Qwen3 paired records belong to the deterministic `rules` arm |
| User-marked region selection | Current | [policies.py:24-29](../breedframe/policies.py#L24), [agent.py:57-60](../breedframe/agent.py#L57), `browser-comparison-v2.json` events 6-7 | Users can mark a region and force a classifier call on those pixels, with bounds and provenance recorded | No evidence it improves ranking. The one controlled test regressed a correct call (below, F5) |
| Uncertainty presentation | Current | [app.js:127-143](../breedframe/static/app.js#L127), `docs/screenshots/comparison-v2.png` | Every raw per-event ranking stays visible next to an explicit refusal to report, with the blocking reasons named | Good design. It does not make the underlying numbers useful |
| A breed report from the shipped app | Current, never fires | 645 ViT leading observations, 0 at or above `MIN_SCORE` = 0.5 ([evidence.py:5](../breedframe/evidence.py#L5)) | The current configuration abstains on everything | Abstaining on a non-dog is the same event as abstaining on a dog. It shows nothing about rejection or calibration |
| Correct report after request and resume | Historical, v1 only | `evidence/browser-resumed.json`: inspect 48x32, request, resume, classify, report `visual_matches` with beagle leading | The v1 configuration demonstrated the full spec-required path and got the breed right | Score 0.1755, margin 0.0631. Blocked twice over by the current gate. The same near-floorless policy also reported a checkerboard as a pug |
| Raw ViT top-1 ranking | Current, measured | 8/12 on the exposed v2 photos; **1/12** on the new identity set (`identity-comparison/summary.json`, `raw_vit_correct_photos`) | It ranks plausibly on some modern press photographs and poorly on the archival set | Two convenience archives. No operating envelope is established, and "works on clear dog photos" is not a claim the evidence supports |
| ResNet-50 with its native dog-class rule | Experimental, unadopted | 9/12 correct on exposed photos, all at 0.7618 or above, wrong calls at 0.3964-0.4107; **1/6** correct on new initial photos | On the exposed set its score separated correct from wrong cleanly | That separation collapsed on new identities: Blanco wrong at 0.7486, Rob Roy taking "book jacket" at 0.8070 |
| Two-photo ViT leading-label agreement | Experimental replay only | 3/6 exposed cases, all correct, 0 wrong, 0 non-dog; **0/6** new, with 13/13 pairs disagreeing | It cleared all three owner bars once, on fully exposed development data | The replay patches both floors to 0 ([evaluate_suitability.py:301](evidence/frozen-sources/scripts/evaluate_suitability.py#L301)) and synthesizes a both-photos-classified trajectory the deployed controller has never produced (F3) |
| Controller accuracy benefit over direct classification | Failed | `docs/evaluation.md`, `docs/evidence-comparison.md` | None. The orchestration costs 10.589 s/case against 0.276 s for the deterministic policy and produced no accuracy gain | The report-count comparison was also confounded, as the repository already states |
| Controller use of supplied follow-up photos | Failed | 0 of 16 supplied second photos classified; I verified 14 directly across both controllers' forced runs | Two differently trained controllers inspect a supplied photo and then finish or request, without classifying it | Cause unresolved. One context intervention was tested and rejected |
| Non-dog rejection by any reporting rule | Unknown | Zero reports on every cohort in every gated arm | Nothing | Zero false reports alongside zero reports is arithmetic |
| Vision-based suitability screening | Unmeasured | `paired-suitability-results.md`: registered trigger was false, runner refused to execute | Nothing | Under a fixed reporting rule, a rejection-only screen cannot lift coverage above zero |
| Individual-subject versus scene report scope | Unimplemented | [contracts.py:37-39](../breedframe/contracts.py#L37) has `outcome` and `selected_result_id` only | Nothing | Accepted as direction, never built. Under an abstention-only gate it would be dead code |

## Findings

### F1. The project's real result is a clean, publishable trade, and it is already complete

This is the most useful thing in the repository, and no document states it
plainly.

The v1 configuration had effectively no numerical floor. It reported the golden
retriever correctly at score 0.084443, the pug correctly at 0.476691, and the
checkerboard control as a pug at score 0.013304 with margin 0.000057
(`evidence/evaluation-results.json`). Three reports, two right, one absurd.

The v2 gate of 0.5 and 0.15 was introduced to stop exactly that. It worked. It
also blocked all 645 recorded ViT observations, including both correct v1
reports.

So the finding is: **this classifier's absolute softmax mass carries so little
signal that any floor permissive enough to report a real dog is permissive
enough to report a checkerboard.** That statement is supported by the numbers
above, it is interesting, and a reader who understands why it happened has
learned something. It needs no further inference.

Counterargument: some middle floor might work. Rank the 20 v2 observations in
`classifier-audit/threshold-replay.json` by leading score and the idea dies.
The dog sculpture, a non-dog control, takes `scotch_terrier` at 0.180789 and
lands 4th of 20. Five correct dog calls sit below it: millie-01 at 0.122199,
conan-02 at 0.118288, sully-02 at 0.083061, sully-01 at 0.055967 and barney-01
at 0.053181.

So any score floor that keeps the sculpture out keeps 5 of the 8 correct calls
out with it. What survives covers 2 supported cases of 6, which is 33% against
the owner's 50% bar, and that is before the margin test cuts further. I derived
this from the saved observations; the repository states the ResNet form of the
same argument and reaches a stronger conditional result there.

### F2. Nobody needs to decide anything about scope before this can be called done

The owner's clarified rules (cautious matches for unknown ancestry, labeled
scene matches for same-breed groups, a selected subject for individual reports)
change how two cohorts are interpreted. They change no measured outcome,
because both group cases and the unknown-ancestry case abstained under both
candidates in the identity comparison, and the shipped app abstains on
everything.

The report contract has no scope field. Adding one would ship a branch that
cannot execute. Leave it unimplemented and say why.

### F3. Replay results have been read as if they described the app. They do not

`pair_report` in [evaluate_suitability.py:289-309](evidence/frozen-sources/scripts/evaluate_suitability.py#L289)
builds a case dict containing an inspection and a whole-photo classification for
*both* photos, then calls `compare` and `build_report` with `MIN_SCORE` and
`MIN_MARGIN` patched to 0 and `completed_by="registered_pair_replay"`. No
controller runs. No budget, no request, no resume.

The trajectory it assumes is the one the deployed controller has never
produced. Across the four forced-pair runs I counted 14 supplied second photos
(7 Qwen3, 7 Qwen3.5). Every one shows `relation: "single_photo"` and a photo-2
event list of `inspect_image` followed by `finish_assessment` or
`request_another_photo`. Zero classifications. Add the CLI and browser demos and
the repository's 0/16 figure holds.

Consequence: the 3/6 agreement result was never a candidate the app could
adopt. Adopting it needed three unbuilt changes at once, which is why it sat
unadopted through two more studies.

### F4. The investigation is self-perpetuating, and the file timestamps prove it

Last change to any file under `breedframe/`: `controller.py` at 09-11 22:00.
The methods review was written at 22:59. Since then the project has produced
three complete studies, three new runners
(`probe_current_photo_context.py`, `evaluate_suitability.py`,
`evaluate_new_identities.py`, 1,084 lines together), and five new or rewritten
documents.

Lines of application code changed in that window: zero.

The apparatus has outgrown the thing it measures. `scripts/` is 2,458 lines
against 1,504 lines of `breedframe/` plus 294 lines of browser assets.
`docs/*.md` runs to roughly 28,900 words. `docs/evidence/` is 9.3 MB.

The mechanism is visible in the documents themselves. `paired-suitability-results.md`
ends with a section titled "Best next step" that commissions the identity
comparison. `identity-comparison-results.md` ends with "Direction from here"
that commissions the crop study. `current-photo-context.md` closes a registered
null result and then opens a new comparison in its final paragraph. Every
results document ends by ordering its successor, and none contains a condition
under which no further study happens.

The fork is identifiable. Review 02's step 1 was a product change: drop the
score floor, require agreement, rerun. The response converted it into a
documentation task and declined the change outright ("Do not change app
thresholds from this reanalysis"). What followed executed the two steps that
could not change the product and skipped the one that could.

I am not saying the response was wrong to decline. Promoting a rule selected
post hoc on exposed data would have been worse. But once that step was
declined, every study after it was measuring a system the project had already
decided not to change, and that is the condition under which studies multiply.

### F5. The crop study should not happen, and the arithmetic is decisive

Work backward from the product decision it is supposed to serve.

**The feature already exists.** Region selection is built, wired through the
classifier, persisted with provenance, and exercised in a recorded browser run.
A positive result would add no capability. It would only supply evidence for
one the app already ships.

**The demanded effect is implausible.** For two-photo ViT agreement to reach
the owner's 50% coverage, both photos of 3 pairs must lead with the correct
label, which is 6 correct crops out of 12. ViT is currently correct on 1 of
those 12. Cropping would have to take raw top-1 from 8.3% to 50%.

For ResNet's frozen rule to reach 3 reports with zero wrong, crops must fix the
leading label on at least 2 more cases, push 3 above the 0.8 floor, and leave
wrongly labeled Blanco below it. Blanco already sits at 0.7486 with the wrong
breed. A tighter crop on a prominent white collie is a realistic way to push a
*wrong* label over 0.8, which fails the error criterion outright. The study has
a plausible path to a result that is worse than doing nothing.

**The only controlled crop test in the repository went the wrong way.**
From `evidence/crop-pilot-results.json`: barney-01 whole photo gives
`scotch_terrier 0.0532`, which is correct; the crop gives `schipperke 0.1162`,
which is wrong. buddy-01 is `weimaraner 0.0658` whole and `weimaraner 0.0662`
cropped, wrong both ways and effectively unchanged. The repository correctly
limits what this pilot establishes, but it is still the only evidence there is,
and it is weakly negative.

**The study set is the wrong photographs.** ResNet's top class for robroy-02 is
"book jacket, dust cover, dust jacket, dust wrapper" at 0.8070. That is a
framed archival print being read as a printed object. hachiko-statue-05 returns
"binoculars" at 0.3316. The supported cohort includes native sources of 272x336,
317x326 and 434x570, several described in the manifest as dark archival images
with the dog small among people. Improving a crop of a 1920s press photograph
tells the owner nothing about a phone photo of their own dog.

**Neither branch terminates.** The results document says so itself: a positive
result still leaves automatic selection, post-crop non-dog rejection, and
multi-dog report scope needing their own evidence, plus a threshold decision
the owner has already declined once. A negative result routes to "reconsider
classifier suitability and the intended photo distribution", which is another
stage.

Strongest counterargument: framing is the one mechanism with a plausible causal
story for the 8/12 to 1/12 collapse, and 39 classifier calls cost minutes. True
on both counts. The compute is free. What costs is the cycle around it: a
protocol, a registration, a results document, and the next question that
document generates. Three of those have run since the methods review with no
product change to show for them.

### F6. The new-identity comparison changed four variables at once, so its drop cannot be attributed

The comparison was designed to test identity disjointness. It also changed the
photographic era, the medium, the subject scale, and the native resolution.
Manifest descriptions include "dark archival image, dog partially obscured by
arms", "small native source", and dogs at a distance among people; native widths
run from 272 to 2000 pixels.

So the 8/12 to 1/12 ViT drop and the ResNet confidence collapse have at least
two live explanations that the design cannot separate: training exposure on the
widely republished modern press photos, and the new set simply being harder.

The useful reading is about the sampling frame. Public archive availability was
never a stand-in for the photographs this app is meant to take, and four rounds
of results drawn from it have carried more weight than they can bear. Stop
drawing distributional conclusions from archives, in either direction. A
tidier version of the same study would inherit the same problem.

### F7. The demo narrative promises a path the shipped controller does not take

`spec.md` requires "a case that asks for another photo and resumes with its
prior evidence". The README's step 4 tells the reader what to do "if the agent
requests another photo".

Qwen3 4B requested a follow-up in 0 of 13 v2 cases. Across the four Qwen3
paired records the `rules` arm issued 34 requests and the agent arm issued none.
The recorded request/resume runs are all v1 (`demo-paused.json`,
`demo-resumed.json`, `browser-resumed.json`) or deterministic. The README does disclose the
skipped follow-ups, but the walkthrough still presents a branch the default
configuration has not taken in any recorded v2 run.

### F8. The region result in the hero screenshot is about resolution

Worth flagging before someone cites it as crop evidence. In
`browser-comparison-v2.json`, photo-1 classifies as `english_foxhound 0.1206`
and the photo-2 region classifies as `beagle 0.1897`, correct. Photo-1 is the
deliberately degraded 48x32 derivative and photo-2 is 600x480. Two different
photographs, a 12x resolution difference, and the region feature demonstrated
cleanly. Framing is uncontrolled throughout.

## The recommended path to completion

Four actions, in order. All of them are writing or version control. None
involves a model.

1. **Commit the repository.** Every file is untracked right now. Make an initial
   commit, or a short series that separates the application, the evidence, and
   the reviews. A reader needs the experimentation history, and none is recorded in Git.
2. **Write one findings page** and link it from the top of the README. Outline
   below.
3. **Correct the README lede and the two demo claims** named in F7 and in the
   documentation section below.
4. **Close the ADR's open threads.** Record that the score floor, the agreement
   rule, ResNet, the vision screen, the report-scope field and the crop study
   are all abandoned for this prototype, with the reopening condition stated
   once.

**Definition of done.** A reader who opens the repository cold reaches the
finding in one hop. Every number in the README matches a saved record. No
document ends by commissioning another study. The repository has a commit
history. That is the whole list, and when it is met the prototype is finished.

**Explicitly abandoned, not deferred:** the crop study, Qwen3.5 vision
screening, the report-scope field, any threshold change, and any further photo
collection from public archives. "Deferred" is what the last three rounds
called work they then did. Call these abandoned.

**What would justify reopening model work.** An external event. A new
hypothesis does not count, and the last three rounds are why. Two things
qualify. First, the owner decides they want a working tool for
their own photographs rather than a completed prototype, in which case the
first thing to run is the experiment described below and the follow-on stages
become the project. Second, a dog-breed classifier trained on contemporary
consumer photographs ships with published per-class calibration, which would
make the reporting gate a solvable problem instead of an unsolvable one.
Neither is something this project can cause by thinking harder.

### The alternative I am rejecting, and why

One experiment has a better case than the crop study, and it is the question
this project has skipped for four rounds: **does the classifier work on the
photographs the app is actually for?** Every number in this repository, all of
8/12, 9/12, 3/6, 1/12, 0/6, comes from public archives. The intended input is a
person's phone photo of their own dog, and that distribution has never been
tested once. A cohort of 12 contemporary photos across 6 dogs with owner-known
breeds, plus 2 non-dog controls, would settle it in one afternoon of classifier
calls.

I find it genuinely interesting. I am still rejecting it, on branch
structure.

A negative result confirms today's conclusion and changes nothing. A positive
result means the classifier is fine and the gate is the whole problem, and then
the owner still has to choose a new floor (a decision already declined once),
fix the 0/16 follow-up skip, add the scope field, and run a fresh evaluation.
That is four more stages, which is the same shape as everything since the
methods review.

There is also a practical block. Personal photographs of friends' dogs cannot
be licensed into `docs/evidence/`, so the result could not be cited in the
prototype it would be run to improve.

If the owner's answer to "experimentation prototype or working tool" is ever "working
tool", this experiment goes first and the four stages become the plan. As long
as the answer is the one `spec.md` states, it loses.

## The documentation decision

Yes, worth doing now, and it is small. One page, not a suite.

Suggested file: `docs/findings.md`, linked from the README's first section.

**Outline**

1. What was built, in five lines.
2. The trade. v1 reported 2 of 3 labeled inputs correctly and also reported a
   checkerboard as a pug at 0.013304. v2's gate stopped that and stopped
   everything else: 645 recorded observations, zero above the floor.
3. What this says about the classifier. Raw top-1 of 8/12 on modern press
   photos and 1/12 on archival ones, with a maximum score of 0.476691 anywhere.
   Ranking without calibration.
4. What was tried and rejected, one line each: context probe (12 decisions, no
   change), paired non-dog controls (registered trigger false), new-identity
   comparison (0/6 both candidates), crop pilot (regressed one correct call),
   ResNet (separation held on exposed data, collapsed on new identities).
5. What is unknown and will stay unknown: performance on contemporary phone
   photographs, non-dog rejection, and whether the exposed-set results reflect
   training overlap.
6. What the engineering demonstrates regardless: bounded local agent loop,
   grammar-level action constraints, evidence-forward uncertainty display,
   pre-registered protocols with advance criteria, and studies closed on a false
   trigger rather than rerun.

**Key claims to make, phrased carefully**

- "The measured configuration abstains on every photograph we have processed."
- "The v1 configuration produced correct reports and one false report from the
  same near-floorless policy."
- "We could not find a reporting rule meeting all three criteria on data it had
  not already seen."
- "We stopped because the remaining questions do not change what ships."

**Claims to remove or qualify**

- README line 3: "decides whether to report likely visual breed matches or ask
  for another photo." Under the measured configuration the controller did
  neither: it emitted no reports and requested no follow-ups in 13 v2 cases. Say
  what it did.
- README step 4's request/resume walkthrough. Attribute it to v1 and to the
  deterministic policy.
- `index.html` line 11, "A more considered match." The page's own footer,
  "Local inference. Bounded actions. Honest uncertainty", is accurate and
  already better. Consider promoting it.
- Anywhere "the agent concluded" or "the agent declined" appears next to a
  finish. When nothing is eligible the schema pins `outcome` to a constant, so
  the model had one legal choice.

One optional tidy: `policy_note` at [evidence.py:130](../breedframe/evidence.py#L130)
hard-codes "0.5" and "0.15" as prose while `MIN_SCORE` and `MIN_MARGIN` sit at
lines 5-6. That string goes into the controller's context. It is correct today
and would silently lie after any threshold change. One f-string. Skip it if the
thresholds are now frozen forever, which is the recommendation.

## Owner decisions

None required. `spec.md` states the purpose, and the owner has already settled
report scope, the three numeric criteria, and the treatment of unknown ancestry
and same-breed scenes. Nothing in this recommendation needs a new ruling.

The one contingency worth naming is not a question I need answered to finish
this review: if BreedFrame is ever meant to become a tool the owner uses rather
than a prototype for experimentation, the rejected experiment above goes first. As a prototype, it is done once the four actions land.

## Next action

Commit the repository. Right now 9.3 MB of evidence, roughly 29,000 words of
documentation, and the entire application exist only as untracked files, and the
experimentation history has not yet been recorded in Git. It takes
minutes and blocks nothing. The findings page comes second.
