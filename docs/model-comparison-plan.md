# Local and hosted model comparison plan

**Closeout, 2026-09-12:** model work is closed for this prototype. Any next-step proposals below are historical and are superseded by the [final findings and stopping decision](findings.md). They are not an active work queue.

Recorded 2026-09-11. Status: option B completed after the baseline was preserved. The candidate was not promoted; Qwen3 4B remains the default. See [results and decision](model-comparison-results.md). That controller round authorized neither paid calls nor image inputs. The owner subsequently authorized a separate [conditional local vision protocol](paired-suitability-protocol.md); its [paired-control stage completed without triggering vision](paired-suitability-results.md). Hosted trials remain proposals without spending authorization.

## Decision and starting point

Wait for **Build BreedFrame agentic app** to finish its current work. Preserve its final code, configuration and raw evaluation results before trying **Qwen3.5 4B Q4_K_M** as a replacement for the Qwen3 4B controller. Keep the existing ViT classifier throughout this controller comparison.

The inspected machine is an M4 MacBook Air with 16 GB unified memory. The current controller receives numerical observations without image input. The first comparison asks whether changing the controller improves decisions within that same evidence boundary. Better breed accuracy is an open question.

| Option | Controller | Purpose |
|---|---|---|
| A: local baseline | Qwen3 4B | Preserve the completed app's measured behavior |
| B: local candidate | Qwen3.5 4B Q4_K_M | Test a newer model within the Mac's memory constraints |
| C: hosted candidate | OpenAI GPT-5.6 Terra | Test whether a hosted controller earns its API cost and network dependency |

All three initially use the same local ViT and text-only evidence. Option C is an experiment; better performance is unproven. It does not require hosting the app or classifier.

## 1. Preserve the completed baseline

Once the build task finishes, identify its final evaluation runner and results. Record the code revision (or a source snapshot if uncommitted), model digests, classifier revision, prompts, runtime version, inference settings and input-manifest hash. Save the original results separately so a later run cannot overwrite them.

Use the completed implementation as the baseline. Earlier README measurements describe earlier code and must not stand in for the final run. Follow the case groups and metric definitions in [the photo-set protocol](photo-set-v2.md), reconciling any changes made by the build task before starting.

## 2. Compare the text controllers

Run Qwen3.5 4B through the completed flow with image input disabled. Keep the same classifier, normalized photos, tools, prompts, reporting rules, action budgets, follow-up availability and context/output limits. Record any necessary model compatibility changes explicitly; these become part of the comparison.

Trace one development case through model selection and startup verification, the controller request, tool execution, saved observation and final report. Update model identity checks and memory attribution together when implementing the candidate option. Confirm the saved trace names the model actually used and that the request contains no images.

Use development cases for compatibility fixes, then freeze the candidate before running the reserved cases. Those cases have already been evaluated by the baseline task; they remain a fixed comparison set, with that exposure disclosed. Do not tune against their results or describe them as a fresh blind test.

Run inference sequentially with comparable loading conditions. Record whether each timing includes model loading. Keep direct-classifier and rules-policy results as controls where the final runner includes them. Keep any forced two-photo experiment separate from the normal request-driven flow.

### Hosted comparison

Apply the same fixed comparison to option C after the baseline is preserved. Use the provider API through a controller adapter, keeping the existing action envelope, local validators and tool execution. Disable provider web search and other additional tools. Send only the same numerical case observations and instructions; exclude photos, filenames and source captions from this text comparison.

GPT-5.6 Terra supports structured outputs, image input and a `none` reasoning setting. Start with reasoning disabled to match the local trial's intent. Verify schema compatibility on development cases, record unsupported settings and any adapter changes, and freeze them before evaluation. Pin a dated snapshot if available; otherwise record the requested and returned model IDs and run date, acknowledging that an alias cannot guarantee a frozen hosted backend. [Model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-terra)

The current launcher blocks outbound traffic. Implement an explicitly selected hosted mode with provider access while retaining the existing local mode's offline behavior. Trace one development case from provider selection and credential loading through the outbound payload, response validation, local tool result and saved report. Do not silently switch providers after a failure.

Before execution, confirm API access and the trial budget. Proposed ceiling: US$5, with an application-side check of accrued cost plus the next request's maximum estimated cost. Include retries in that accounting and retain failures if the ceiling or normal time limits stop the run. Record actual token usage, total cost and cost per completed case. The model's published standard text rates are US$2 per million input tokens and US$12 per million output tokens; verify applicable cache charges and prices when running. This is a budget proposal, not spending authorization. [Pricing](https://developers.openai.com/api/docs/models/gpt-5.6-terra)

Record the selected API data settings. Use `store=false` where supported, without treating that as zero retention: provider abuse-monitoring and other retention rules still apply. Private photos would need an explicit cloud-upload choice in the later vision experiment. [Data controls](https://developers.openai.com/api/docs/guides/your-data)

## 3. Judge the result

Retain every scheduled case, including failures, abstentions and cases that request no follow-up. Preserve the existing denominators:

| Cases | Outcomes to compare |
|---|---|
| All 13 cases | Completion, abstentions, requests, action errors, latency and memory |
| 6 pairs with a supported breed label | Correct reports over all eligible cases, report coverage, errors among reports, and follow-up improvements and regressions |
| Bo | Unsupported-breed reports |
| Topper | Unsupported ancestry claims |
| 2 multi-dog cases | Target-selection behavior |
| 3 non-dog cases | False live-dog or breed reports |

Report development and reserved results separately. Memory counters have different accounting rules; do not add Ollama residency to process RSS or footprint as if they were disjoint allocations.

For option C, also report API cost, network failures and complete request latency. Local memory still includes the app and ViT; remote model memory is unmeasured. Unload local controllers for the hosted measurement and disclose that condition. A lower local footprint does not measure total cloud resource use.

Keep Qwen3 4B as the default if the candidate shows no useful improvement. Consider promotion only when the recorded cases show a useful decision or reporting improvement without additional unsupported claims, and the measured latency and memory cost are acceptable. Mixed results should remain explicit rather than being reduced to a claim that the newer model is better.

Judge hosted adoption separately: useful gains must also justify recurring cost, data transfer and dependence on a working connection. A favorable result can justify an optional hosted mode while the local default remains available. A null result supports keeping the current setup; it cannot prove that every hosted model would fail to help.

Complete the fixed comparison even if it shows no improvement. Stop a run on its existing resource or failure limits and retain the failure. Do not extend the sample or rerun cases merely to obtain a favorable result. Qwen3.5 9B is an optional later candidate if the 4B result leaves a specific unresolved problem worth its extra resource cost.

## 4. Investigate classifier quality and reporting thresholds

Status: the [numerical audit and development threshold replay](classifier-audit.md) and [replacement classifier screen](classifier-screen.md) are complete. The [methods review and owner clarification](review-02-response.md) reopened ResNet's rejection and deferred subject detection. A subsequent [current-photo context probe](current-photo-context.md) found no classification choices with either context; the prominence change was not adopted. The [paired-control experiment](paired-suitability-results.md) then observed no non-dog reports from either fixed candidate. The subsequent [new-identity comparison](identity-comparison-results.md) missed the coverage target with both candidates, each reporting on 0/6 supported cases. Input framing, breed ranking and explicit report scope remain unresolved. No threshold was promoted. The procedure below still governs any later classifier comparison.

Follow the controller comparison with a separate investigation of actual breed-report usefulness, regardless of whether a controller candidate improves orchestration. The [measured v2 comparison](evidence-comparison.md) produced no breed reports from either rules or Qwen3. The reporting conditions include a top score of at least 0.5 and a margin of at least 0.15; these uncalibrated thresholds were too restrictive for that sample. Direct classification returned some correct labels, but also reported breeds for non-dogs and an unsupported breed. A controller swap alone does not establish better classifier quality or suitable reporting thresholds.

Start by preserving the current classifier outputs and complete reporting policy. Check the pinned processor, input normalization and class mapping before attributing failures to model capacity. Trace one development image through preprocessing, classifier loading, raw scores, the report eligibility decision and the saved user-facing assessment. Record which condition prevented a report, including quality flags, unresolved labels or disagreement, so the score threshold does not absorb unrelated failures.

Investigate changes separately:

| Comparison | Fixed conditions | Question |
|---|---|---|
| Reporting policy | Current classifier outputs, controller and photo availability | Can a development-selected reporting threshold improve useful coverage at an acceptable error rate? |
| Classifier | Controller, normalized source photos and evidence budget | Does a candidate improve breed ranking and separation of supported cases from unsuitable inputs? |

Use cached outputs for exploratory threshold comparisons, then run the frozen policy through the complete workflow. A replay of cached scores cannot measure changes in follow-up requests, completion or latency caused by the new reporting policy.

Choose any classifier candidate after checking its label coverage, preprocessing, license and local runtime requirements. Record required processor differences. Raw score scales may differ between models: compare ranking quality first, then select each model's reporting policy on development data and compare error rates at comparable coverage. Do not carry a numeric threshold across models and assume it means the same thing. Treat calibration as a separate development step if the available labeled data supports it.

Define acceptable report error and minimum useful coverage before examining new evaluation results. The existing corpus is small and already exposed; retain it as a regression set. Freeze any additional collection and identity-group split before tuning, including supported breeds, unsupported breeds, non-dogs and unknown ancestry. Do not expand the set merely to obtain an improvement.

Keep the cohort-specific denominators from section 3. Report correct breed reports over all eligible dogs, coverage and errors among reports together; retain failures and abstentions. Also report false breed reports on non-dogs, unsupported-breed reports, unsupported ancestry claims and target-selection failures separately. If a candidate changes label coverage, preserve the original cohorts for comparison and report newly supported classes separately. Include follow-up burden, latency and memory for the resulting workflow.

Promote a change only if it meets the predeclared usefulness and resource criteria on evaluation data without concealing regressions in the other cohorts. Otherwise retain the baseline and record the unresolved limitation. No universal threshold or classifier replacement is selected by this plan.

## 5. Evaluate vision separately

Current status: a [photo-only Qwen3.5 suitability screen](paired-suitability-protocol.md) was registered as a conditional second stage. Neither candidate reported on the fixed non-dog controls, so that stage did not run. The model's image capability remains unmeasured here. The experiment used a no-image grounding control in its proposed schedule, not a controller-performance ablation; its narrower question and division of work are explicit in the protocol.

Keep a later vision experiment separate from the classifier and threshold investigation. Consider passing photos to the vision-capable controller to investigate dog presence, multiple subjects and subject visibility. This requires explicit image input and corresponding evidence and reporting rules. Merely changing the model name does not enable vision in BreedFrame.

Record this as a separate experiment because it changes the available evidence. Hold the classifier and reporting policy selected in the preceding round fixed while testing whether visual observations improve the workflow; do not assume a general vision model is a better breed classifier. Define the protocol before running it and disclose prior exposure to the comparison cases.

Use the same selected model with and without image input to measure the effect of vision. Comparing a local text-only controller directly with a hosted vision controller changes both model and evidence, so report that only as a comparison of complete systems. For hosted vision, identify which photos leave the Mac and include image-input charges.

## Candidate sources

Checked during the model discussion on 2026-09-11:

- [Ollama Qwen3.5 4B](https://ollama.com/library/qwen3.5:4b): Q4_K_M, approximately 3.4 GB download, image and tool support.
- [Ollama Qwen3.5 9B](https://ollama.com/library/qwen3.5:9b): Q4_K_M, approximately 6.6 GB download.
- [Qwen3.5 4B model card](https://huggingface.co/Qwen/Qwen3.5-4B): model capabilities, inference guidance and published comparisons with 9B.

Download sizes are not runtime memory estimates. The 4B candidate has now been measured on this Mac; see the [completed results](model-comparison-results.md). The 9B candidate remains untested here. Pin the actual downloaded model digest for any later comparison.

## Current round boundary

The pinned Qwen3.5 digest is `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`. Explicit sampling settings match the baseline's effective values, including presence penalty zero; the downloaded candidate package otherwise defaults that penalty to 1.5. Model-native templates and stop tokens remain part of the recorded packages. The application prompt, tool schema, classifier, image processing and reporting rules are unchanged.

Separate probes verify identity, text-only requests, persistence and cold memory accounting. The main comparison retains the original warm timing procedure without memory sampling. Both memory probes use the same preselected development photo; their repetition measures resource use and does not supply another accuracy estimate.

The classifier investigation began after the controller comparison closed. Its [audit results](classifier-audit.md) preserve that boundary. Numerical checks, cached threshold replay and a [small new-identity comparison](identity-comparison-results.md) are complete. That archive-heavy comparison failed the coverage target; evidence representative of the intended photo distribution remains limited. Neither the app's controller nor its reporting thresholds changed.
