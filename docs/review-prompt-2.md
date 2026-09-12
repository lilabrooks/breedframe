# Claude review 2: methods, model use and direction

You are conducting a second, independent review of BreedFrame in `/Users/lilabrooks/code/breedframe`. Be critical and adversarial about the reasoning, experimental methods and project direction. Treat the repository's conclusions as claims to examine. Do not manufacture objections or assume that a more complicated system is better.

The central question is: **Are we drawing the right conclusions from these experiments, using the models effectively, and choosing the next work most likely to improve the usefulness of the application?**

## Scope

Review methods, model configuration and use, interpretation of evidence, product requirements, decision criteria and priorities. Read implementation code where it reveals what a model actually receives or what the application permits it to do.

**Exclude the software test suite entirely.** Do not read or run `tests/`, audit test coverage, review CI/linting, propose unit or integration tests, or cite passing checks as evidence that the methods are sound. Existing model evaluations, photo collections, experimental protocols and raw inference records are in scope: they are the evidence for this review.

This is a review, not an implementation task. Do not modify the application, change model settings, rerun inference, download models or consume reserved evaluation data. You may write your review to `docs/review-02-methods-and-direction.md`. Do not overwrite historical evidence. If a previous review is unavailable, say so briefly and make this review self-contained.

## Context to verify

BreedFrame runs locally on an M4 MacBook Air with 16 GB RAM. A text-only controller chooses tools using numerical observations; a separate image classifier supplies breed rankings. The product describes likely visual matches and disclaims genetic ancestry verification. Start with the actual product brief and specification rather than assuming breed identity prediction is the only useful outcome.

Models exercised so far:

- Qwen3 4B Q4_K_M, the default controller, and Qwen3.5 4B Q4_K_M, the comparison controller. Both received text-only evidence with thinking disabled. The comparison held the application prompt and action schema fixed. Neither classified supplied second photos in the forced-pair runs.
- The original 120-class ViT, `wesleyacheng/dog-breeds-multiclass-image-classification-with-vit`. An audit found matching preprocessing and scoring on three development probes. Its outputs did not meet the current score/margin gate of 0.5/0.15 on the expanded corpus.
- `microsoft/resnet-50`, screened separately with its own preprocessing and full 1,000-class scores. Report eligibility required a domestic-dog global top class and score/margin cutoffs. Reported raw correctness was 9/12 labeled photos versus 8/12 for the ViT, but no setting in the 117-cell grid met the reporting criteria across all cohorts.

The two dima806 breed classifiers were screened from metadata and rejected for missing breeds in the current corpus; they were not run. Qwen3.5 vision, the 9B model and hosted controller options have not been evaluated. Do not present them as measured alternatives.

The expanded corpus contains 20 photos, 13 cases and seven same-dog pairs. Twelve breed-labeled photos represent six dogs across five breeds. It includes unsupported breed, non-dog, multiple-dog and unknown-ancestry cohorts. All photos have now been exposed during development. Fresh collection was deferred after the ResNet development exit; a proposed 44-image collection has not been assembled.

The owner explicitly chose: at least 50% coverage on supported breeds, at most 10% wrong breed reports among reports, and zero unsuitable-input reports in the fixed evaluation set. Preserve those preferences. Challenge ambiguous definitions, their operationalization and what the sample could establish; do not quietly replace them with easier criteria.

The current proposed direction is to establish a suitable, selected live-dog subject before reporting breed matches. **Audit that recommendation independently. You are not being asked to endorse it.**

## Read the evidence in this order

1. `docs/spec.md`, `README.md`, `docs/adr/001-local-inference.md` for intended behavior and constraints.
2. `docs/evidence-comparison.md`, `docs/model-comparison-plan.md`, `docs/model-comparison-results.md`, `docs/classifier-audit.md`, `docs/classifier-screen.md` for methods, claims and decisions. Skip their software-verification sections.
3. Relevant raw records under `docs/evidence/`: the photo-set-v2 manifest, paired runs, crop pilot, controller-comparison protocols and results, classifier-audit protocol/replay/probes, and classifier-screen protocol/results. Inspect targeted records rather than dumping entire score arrays.
4. Relevant implementation: `breedframe/controller.py`, `policies.py`, `agent.py`, `evidence.py`, `classifier.py`, `images.py`, `contracts.py`, `config.py`; `scripts/evaluate_pairs.py`, `evaluate_crops.py`, `audit_classifier.py`, `screen_classifier.py`. Inspect saved model configuration, processor and package metadata when it bears on a finding.

Trace at least one initial-photo case and one skipped-follow-up case from available evidence through the actual prompt/schema, allowed action, observation, eligibility decision and report. Distinguish a controller choice from a tool/schema restriction, orchestration defect or reporting-policy consequence.

## Questions to investigate

### 1. Are the experiments answering the right questions?

Separate the value of breed ranking, selective reporting, subject selection, evidence acquisition and natural-language orchestration. Identify outcomes that were structurally impossible under the fixed policy. Which null results reveal a model limitation, and which reveal the particular configuration or workflow?

Assess direct/rules/agent comparability, forced versus requested follow-ups, user-style closures, initial versus final outcomes, correlated photos and denominators. Check whether the three-image crop pilot supports the conclusions drawn about cropping. Distinguish an observed result from a broader recommendation.

### 2. Are the models being used effectively?

Inspect the actual text-controller inputs, prompts, schema, tool descriptions, memory of prior observations, budgets, generation settings and stopping options. Is skipping the second classification explained by those inputs? Is “finish inconclusive” rational under an unattainable reporting gate? Could a small prompt, context or action-policy change extract more useful behavior from either controller? Would that retain meaningful model discretion or simply encode the desired workflow in rules?

Distinguish a fair frozen-configuration model swap from a comparison of each model's best practical configuration. Assess thinking mode, output limits and model-specific prompting only where relevant; do not assume enabling them helps. Compare the value of model-led orchestration with deterministic evidence collection and a narrower model role, or no controller.

For the classifiers, assess global top-one selection, full score distributions, margins, preprocessing, crops, class mapping and multi-photo evidence. Does failure of the ResNet gate justify rejecting the classifier, or only that complete reporting policy? Are complementary uses of the already measured ViT and ResNet worth investigating? Consider ensembles, staged use or user-selected regions only with a specific mechanism and a cheap way to distinguish benefit from extra complexity. Do not propose arbitrary averaging of incompatible score scales.

### 3. Do the reporting requirements fit the product?

Examine whether visual resemblance, source-reported breed, pedigree identity and ancestry have been conflated. Is every report on an unknown-ancestry dog necessarily wrong under the stated product contract? Can ancestry uncertainty be determined from pixels? Is a scene containing two dogs of the same breed unsuitable for every possible report, or for an unselected-subject report specifically?

Distinguish species classification, detecting/counting dogs, choosing a subject, recognizing depictions and verifying breed identity. What can each proposed mechanism actually establish? Do not assume a detector solves statues, mixtures or out-of-class rejection.

### 4. Are selection and stopping decisions defensible?

Audit candidate rejection based on missing current-corpus breeds, the narrow candidate shortlist, the added “at least 8/12 raw correct” exit, the finite threshold grids and the interpretation of zero qualifying settings. Which requirements came from the owner and which were introduced during implementation?

Assess whether repeatedly using this archive-heavy corpus is steering decisions toward its peculiarities. Was deferring fresh collection justified, or does it risk requiring success on an unrepresentative development set before learning anything new? Is the proposed collection suited to the next decision, including follow-up usefulness? Examine the resolution of the coverage/error criteria at its sample size, source-label uncertainty and unknown training overlap.

Respect fixed stopping rules, but assess whether those rules were well chosen. Do not recommend extending a sample just to obtain success. Do not silently redefine cohorts or turn previously exposed cases into a holdout.

### 5. What should happen next?

Compare practical improvements using the models already exercised against adding a subject detector, using Qwen3.5 vision, changing the product interaction, collecting better data or pausing model work. New capabilities remain proposals, not authorized experiments. Favor the smallest intervention that resolves the most consequential uncertainty.

Check primary model documentation when a recommendation depends on an external capability or supported setting. Cite what you verified, and label unverified ideas as hypotheses. Local runtime and user effort matter; more process, instrumentation or model capacity needs a concrete benefit.

## Deliverable

Lead with your verdict on the current direction. State what the evidence establishes, what it cannot establish, and which decision, if any, should change now.

Then provide:

1. **Prioritized findings.** For each: severity, specific evidence with file/line or JSON-path references, the inferential or design problem, its practical consequence, and a proportionate correction. Separate demonstrated flaws, credible risks and unresolved questions. Include the strongest counterargument to consequential findings.
2. **Model-use opportunities.** A compact comparison of plausible changes to the already exercised models: expected mechanism, supporting evidence, uncertainty, cost and what would falsify the idea. Clearly separate configuration changes from added visual evidence or changed product scope.
3. **At most three ordered next steps.** Each must identify the decision it resolves, the smallest useful experiment or non-model change, what stays fixed, relevant cohorts and denominators, and explicit advance/stop conditions. Trace the final decision backward to the earliest cheap evidence. State what should be deferred or abandoned.
4. **Owner decisions, only if necessary.** Ask only questions that materially change the direction and cannot be resolved from existing instructions. Give a recommended answer with its tradeoff.

Do not include software test findings, check counts, a generic best-practices checklist or a large unranked backlog. A strong review may recommend keeping the current direction, changing it substantially, or simplifying the application. Make the recommendation earn its place through evidence.
