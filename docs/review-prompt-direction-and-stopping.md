# Claude follow-up review: product value, direction and stopping

You are conducting an independent, critical and adversarial review of BreedFrame in `/Users/lilabrooks/code/breedframe`. Follow the methods-and-direction scope of `docs/review-prompt-2.md`, but use the current evidence and the mandate below. The earlier review and its response are inputs to challenge, not authority to inherit.

**Decide whether further model experimentation is worth doing now, or whether the best outcome is to close this prototype phase, document its demonstrated strengths and limits, and move on.** The owner is concerned that each completed evaluation generates another evaluation with no end in sight. Your job is to recommend a finite course of action, not supply more hypotheses merely because unanswered questions remain.

## Scope and boundaries

Review product value, experimental methods, interpretation, use of existing models, opportunity cost and project direction. Read implementation where necessary to establish actual behavior. Examine the reasoning behind the latest recommendation as critically as the models themselves.

**Exclude software tests entirely.** Do not read or run `tests/`, assess test coverage, review CI/linting, propose unit or integration tests, or treat passing checks as evidence of useful model behavior. Existing photo evaluations, frozen protocols and inference records ARE in scope. Those are the empirical evidence, not the excluded software test suite.

This is a review only. Do not run inference, collect photos, download models, sweep thresholds, change code or settings, or start the proposed crop study. Write only `docs/review-product-value-and-stopping.md`; preserve earlier reviews and experimental evidence. Targeted arithmetic from saved outputs is allowed. Avoid a comprehensive re-audit when a few decisive records settle the question.

## Start with the purpose

`docs/spec.md` describes a local dog-photo assessment prototype for experimentation with model-controlled workflows. Its required outcome includes a visible, model-controlled investigation and a request/resume case. Later work adopted stricter criteria for useful breed reporting. Evaluate those objectives separately:

- Is this a credible, honestly presented prototype today?
- Is it a useful breed-photo assessment tool today?

Do not quietly substitute one goal for the other. An experimental finding can be valuable even when the breed-report hypothesis failed. Conversely, documenting a limitation does not repair it or establish that a user-facing feature works. Assess whether the owner needs any scope decision before declaring the work complete.

The owner selected at least 50% supported-breed coverage, at most 10% wrong breed reports among emitted reports, and zero unsuitable-input reports in a fixed evaluation set. Preserve these criteria when judging the breed-report objective; do not reinterpret them as established population guarantees.

The owner subsequently allowed cautious visual matches for real dogs of unknown ancestry and clearly labeled scene-level matches when multiple dogs share a breed. Individual-dog reports in multi-dog scenes require a selected subject. The current report contract does not express this scope distinction. Do not reopen these settled preferences as questions or count every unknown-ancestry or multi-dog report as prohibited. A whole-frame breed prediction alone cannot establish that every dog shares that breed.

## Current evidence to verify

These are navigation aids and claims to check, not conclusions you must endorse:

- The app still uses the original ViT, Qwen3 4B text controller and score/margin gate of 0.5/0.15. Every recorded v2 ViT result falls below the score floor. Experimental ResNet and zero-floor agreement policies have not been adopted. Historical v1 reporting and request/resume demonstrations used a different configuration.
- Qwen3.5 4B did not earn promotion as a text controller. A later 12-decision probe made missing current-photo classification more explicit; both controllers still chose classification in 0/3 states under each context. This rejects that intervention, not all possible controller configurations.
- On six previously exposed supported identities, two-photo ViT agreement and single-photo ResNet each emitted three correct case reports. ResNet's separate 8/12 photo result is a different denominator. Paired controls yielded no ViT reports on three non-dog pairs and no ResNet reports on eight non-dog photos. The conditional Qwen3.5 vision stage therefore did not run. Vision remains unmeasured.
- The subsequent new-identity comparison used 26 photos across 13 cases and 39 classifier calls. Both fixed policies emitted zero reports on all cohorts, including 0/6 supported cases. Error among reports is undefined. Each classifier's raw leading label was correct on only 1/6 supported initial photos; all 13 ViT pairs disagreed. Threshold changes cannot meet the target within the evaluated ResNet top-one reporting family on those six outputs.
- The new identities still come from a narrow convenience collection: five supported dogs are historical US presidential pets, two are white collies, and training overlap is unknown. These results do not estimate performance on contemporary phone photographs. Earlier successes are also convenience evidence, not a validated deployment niche.
- The latest recommendation is full-frame versus manually marked dog-region inference. Inspection of processor inputs showed framing concerns, but did not establish that framing caused errors or that crops would help. **Decide whether this study deserves to happen at all. It is not the default next step.**

## Reading route

1. `docs/spec.md`, `README.md`, `docs/adr/001-local-inference.md`: original purpose, current claims and constraints. Skip software-verification sections.
2. `docs/review-prompt-2.md`, `docs/review-02-methods-and-direction.md`, `docs/review-02-response.md`: earlier critique, corrections and the sequence it created.
3. `docs/current-photo-context.md`, `docs/paired-suitability-results.md`, `docs/identity-comparison-results.md`, with their protocols and targeted records under `docs/evidence/`: current decision evidence.
4. Consult `docs/model-comparison-results.md`, `docs/classifier-audit.md`, `docs/classifier-screen.md`, `docs/evidence-comparison.md` and `docs/evaluation.md` only where they support or contradict a material claim. Keep historical and current configurations distinct.
5. Trace one representative current-app path through classifier output, controller decision, eligibility gate and user-visible report. Trace one experimental candidate outcome through its runner and report construction. Use relevant implementation in `breedframe/` and `scripts/` to establish the difference; do not assume replay results describe the deployed interaction.

Cite decisive file/line or JSON-path evidence. Check official primary documentation only if a recommendation depends on an external model capability. Label anything unverified as a hypothesis.

## Questions the review must resolve

### What is worth keeping, and what can we honestly claim?

Separate engineering capability, controller usefulness, raw breed ranking and useful emitted reports. Identify what works under the current configuration, what worked only historically, what works only in experimental replay, what failed, and what remains unknown.

Evaluate whether visible evidence, local execution, persistence, region selection and uncertainty presentation support the experimentation purpose. Do not infer correctness or practical value merely from feature existence. Do not describe the system as working well on “clear dog photos” or another broad category without evidence. Name concrete successful cases and their limits where a general operating envelope cannot be established.

Would a concise strengths-and-limits document plus an honest demo narrative be enough to close the prototype now? Specify what it should say, misleading claims to remove or qualify, and any minimal presentation correction needed. Distinguish completing the prototype from promoting a breed-report policy. Documentation must not disguise an abstention-only measured configuration as a useful breed identifier.

### Has the investigation become self-perpetuating?

Which completed studies changed a real decision? Which mostly generated another question? Have assistant-added requirements, source-selection constraints or validation stages expanded the original weekend scope? Distinguish sound individual protocols from a research program with no terminal condition.

Audit the latest crop proposal backward from its intended product decision. Even if manual crops improve rankings, would that settle enough to adopt a useful behavior, or merely open separate studies of selection, non-dog rejection, scope and generalization? If neither outcome leads to a practical decision within a reasonable effort cap, reject the study for now.

Explain how archive bias limits negative conclusions without making “collect more representative data” an automatic escape from every failure. Do not expand a quiet sample to obtain a positive result. Account for both additional owner effort and the opportunity cost of spending another iteration here. Do not invent an hours estimate for past work.

### Are the existing models being used in a way worth improving?

Consider only opportunities with a plausible mechanism and a concrete user benefit: deterministic evidence collection, a narrower controller role, explicit user region selection, a carefully framed raw-ranking explorer, or existing classifier policies. Changing the division of work or exposing ungated rankings changes the product and its risks; it is not a free accuracy fix.

Assess whether any such change is justified now, should remain documented as a hypothesis, or should be dropped. A rejection-only vision screen cannot increase zero coverage under a fixed reporting rule. A controller swap has no demonstrated remedy for the stored ranking failures. Neither point rules out every other model role, but an untested capability is not itself a reason to fund another study. Do not produce a shopping list of models, ensembles, prompts or datasets.

### What is the best finite path from here?

Compare closing the prototype with documented limits, making a small bounded product/presentation improvement, performing one decisive experiment, and pausing or changing the breed-report objective. Recommend one primary path and explain why the strongest alternative loses now. No new work is also a valid recommendation.

If you recommend further inference, permit **at most one experiment** in this recommendation. Specify the decision it changes, why existing evidence cannot settle it, the minimum cohort and evidence budget, what remains fixed, and a hard effort cap. Map every cohort to the metrics it affects. Give concrete actions for positive, negative and ambiguous outcomes, including a terminal stop. “Run another experiment” is not an acceptable default branch. Do not invent a budget approval; distinguish your proposed cap from owner authorization.

## Deliverable

Write a self-contained review with:

1. **Verdict first:** stop model work now or continue for one stated reason; separately assess prototype completion and breed-report usefulness.
2. **A compact capability/limits table:** current, historical or experimental status; supporting evidence; allowed claim; limitation. Where “works well” is unestablished, say so.
3. **Only material prioritized findings:** evidence, practical consequence, correction and strongest counterargument. Include flaws in our direction-setting process where supported. Do not repeat the prior review wholesale.
4. **One recommended path to completion:** a short ordered list of necessary actions, concrete definition of done, work explicitly deferred or abandoned, and the external event or evidence that would justify reopening model work later. A failed final step must not silently create another stage.
5. **The documentation decision:** whether documenting limits is worthwhile now, a concise outline and suggested key claims, and any mismatch between the current demo narrative and measured behavior. Do not write an entire documentation suite.
6. **Owner decisions only if indispensable:** use already stated preferences; ask only about choices that materially change the recommendation and cannot be inferred from them.

End with the single next action you would take. A strong review can conclude that the prototype has taught us enough. It can also justify one more intervention, but it must show why the expected decision value exceeds the cost and where the work ends.
