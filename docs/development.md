# Development and reproducibility

## Layout

| Path | Responsibility |
|---|---|
| `breedframe/controller.py` | Frozen prompt, compact observation context, legal action schema and loopback Ollama call |
| `breedframe/evidence.py` | Deterministic multi-photo comparison and report eligibility |
| `breedframe/presentation.py` | Current-photo visual-match summary shared by the API and readable export |
| `breedframe/policies.py` | Shared legal actions and deterministic evaluation controller |
| `breedframe/agent.py` | Budget, validation, execution, terminal states, evidence-grounded report |
| `breedframe/classifier.py` | Persistent, killable PyTorch worker; MPS and CPU paths |
| `breedframe/images.py` | Safe decoding, metadata removal and pixel diagnostics |
| `breedframe/store.py` | Generated IDs, private files, atomic JSON writes and restart recovery |
| `breedframe/app.py` | Loopback FastAPI, one active operation, upload and case endpoints |
| `breedframe/static/` | Scout workspace, live step display, recorded timeline, assessments and saved-case controls |
| `scripts/` | Explicit online setup, offline startup, demo, evaluation and probes |
| `tests/` | Deterministic orchestration and HTTP-boundary tests |

## Checks

`make check` first synchronizes the project environment with `uv sync --locked`, then runs Ruff, pytest, JavaScript syntax checks and the Node agent-flow state tests. It fails if the manifest and lock disagree. Local checks and CI use this same command; `UV_PROJECT_ENVIRONMENT` can select a different project environment.

The required classifier tests load the reviewed ViT processor configuration from `tests/fixtures/vit/preprocessor_config.json` and check image normalization. They also generate tiny, untrained ViT weights in a temporary directory and exercise the production worker on CPU, including repeated inference and rejection of an invalid class count. These tests require the real Transformers, torch and torchvision packages, run without downloaded model weights, and never skip when trained assets are absent. Orchestration and HTTP tests use fakes.

Generated weights verify software compatibility. They provide no evidence about breed accuracy or compatibility with the trained checkpoint. After classifier or dependency changes, also run the installed classifier on the demo photograph with the synchronized environment; `make demo` covers the wider local integration when Ollama and the reviewed model assets are available. Keep those smoke checks separate from the closed model experiments and their saved measurements.

## Model readiness

[Local setup and troubleshooting](setup.md) documents the two required models and startup commands. `/api/health` checks the pinned Ollama identity, nonempty required classifier assets, and basic JSON configuration. It does not warm the model or validate the entire weights file. The browser fails closed while checking or disconnected, rechecks every 10 seconds and on focus, and checks before submitting inference. The API independently rejects new inference with HTTP 503 before mutating case state when readiness fails. Reads, exports, cancellation, partial completion, and deletion do not require models.

API tests cover unavailable controllers, missing or incomplete classifier files, recovery, and rejected inference leaving the store unchanged. Node tests cover readiness messaging and its distinction from actual investigation activity. Rendered recovery, disabled controls, and accessibility scenarios are tracked in the [UI hardening milestone](https://github.com/lilabrooks/breedframe/milestone/2).

## Local state

Browser cases are in `data/cases/`; CLI, scripted demo, offline verification and evaluation use separate case directories. Each case includes re-encoded images and `case.json`. Uploaded filenames and metadata are excluded from controller input. Model weights are under `models/`; downloaded runtimes and caches are under `.runtime/` and `.venv/`.

`BREEDFRAME_DATA` can set the browser store root before startup. It is intended for trusted local use. Do not point two app instances at one directory. Only one process should serve each app instance; multi-worker deployment is unsupported. No external storage exists.

The browser opens empty. **Clear all** and **Start a separate case** reset the workspace while retaining cases. **Saved cases** reopens local history. **Delete this case** removes one inactive case; **Clear saved cases** removes every case in that store, including cases outside the recent-list limit. Both deletion actions require confirmation. The server rejects clearing during active work and validates that all saved cases can be cleared before deleting any. Use a dedicated temporary `BREEDFRAME_DATA` directory for destructive browser checks, never a user's normal store.

The server rejects cross-origin mutations and untrusted Host headers, limits uploads to 12 MiB and decoded images to 20 million pixels, and accepts single-frame JPEG, PNG and WebP. This does not make it a hardened multi-user service. Keep it on loopback.

## Scout and assessment presentation

[Using Scout](usage.md) describes the current browser controls. Scout is the agent's display name; the configured controller remains `qwen3:4b` by default. The language model chooses tools from numerical observations, the ViT reads pixels, and deterministic code assembles the assessment. The UI's **How this works** section explains these roles and shows the configured controller identity.

`agent-flow.js` derives the visible step from case state and recorded events. The UI distinguishes choosing, running a tool, returned evidence, cancellation, direct classification, connection loss, and terminal states. It shows attempts and actual activity rather than a fabricated completion percentage. Earlier-photo events don't stand in for work on an unclassified follow-up.

`presentation.py` derives the top visual match from the latest classification of the current photo, including region and event provenance. The browser and readable export share that summary. It formats raw scores as percentages with an explicit calibration caveat; it doesn't change `evidence.py` or the stored report outcome. Tentative matches can therefore appear while the underlying outcome remains `inconclusive`. Earlier photo and region rankings remain available for comparison, and report history stays in the saved case.

The [UI hardening milestone](https://github.com/lilabrooks/breedframe/milestone/2) tracks rendered-browser coverage for the core flow, deletion safeguards, and responsive/accessibility checks. Those browser checks are planned work; the current Node state tests don't establish rendered behavior. New documentation screenshots belong alongside the [current capture notes](screenshots/README.md), with historical screenshots preserved separately in the index.

## Runtime limits

Six attempts per photo, three photos per case, 240 seconds per photo, 45 seconds per controller request and 60 seconds per classifier request. Invalid controller responses consume attempts, and two controller failures stop the run. Tool failures become real error observations. Duplicate tool work is blocked. Timeouts preserve completed observations and produce an incomplete state.

The current controller schema removes already completed photo tools and disallows another photo past the case limit. Finish and request require a current-photo inspection. A visual report must reference an eligible actual current-photo classifier event and satisfy the multi-photo comparison boundary. Region selection requires a real region-classification attempt before the controller may request or finish. Inconclusive reports select no classifier event. Every final report attaches actual observed evidence IDs. The user may close a stopped case with an explicitly user-completed, inconclusive partial report.

A requested case accepts a new photo and gets a fresh six-attempt budget while retaining all previous observations. An identical decoded image is rejected without consuming the photo allowance. An incomplete case can accept a new photo too. A completed case can accept another photo: its earlier report is archived in `report_history`, and the new assessment uses all available observations. User-selected regions and retries share their parent photo's existing action and cumulative time budgets.

Automatic MPS fallback is implemented for an unavailable device or a runtime error. The explicit CPU path was exercised on the beagle demo and checked against MPS. Simulating every possible driver failure is outside the test scope.

## Repeat the offline check

Stop BreedFrame before starting a separate controller if it already owns port 11434. Run the local server under the same macOS network policy used during verification:

```sh
/usr/bin/sandbox-exec -f scripts/offline.sb sh scripts/serve_ollama.sh
```

In another terminal at the repository root:

```sh
PYTHONPATH=. /usr/bin/sandbox-exec -f scripts/offline.sb .venv/bin/python scripts/offline_smoke.py
```

This verifies blocked external HTTPS and a completed local assessment, then writes `docs/evidence/offline-smoke.json`. It replaces that measurement file. The test must run with both processes under the policy; a separately running unconfined Ollama server is not sufficient evidence of network denial.

## Reproduce a comparison

`make evaluate` uses the fixed manifest and retains all five cases. The output includes per-case statuses, exact events, elapsed time, method order, input hashes, prompt source hash, memory-accounting method and aggregate counts. Model weights, library versions, device, model warmness, background load and controller prompt can affect results. The committed `uv.lock` pins the Python environment.

Do not use these five inputs to tune thresholds and then claim held-out accuracy. The two source photographs also may overlap training material. A larger labeled study would require new data and a separate protocol; the current result is a weekend smoke evaluation.

## Known rough edges

- Unsupported request reasons are removed from the current schema and still rejected at execution. No rejected calls occurred in the v2 fixed evaluation.
- Low leading scores are common. The stricter policy withheld all breed reports in the v2 sample. Thresholds are uncalibrated; zero coverage is a limitation.
- The controller cannot detect a dog or propose a grounded crop. The optional region editor records user-provided coordinates. Breed-reference retrieval is omitted because it would not validate the depicted dog.
- The required CPU classifier tests use real libraries and generated weights. `make demo` and browser testing cover integration with the trained local models and Ollama. CI does not verify MPS or the macOS launcher and network policy.
- The current FastAPI/Starlette test client emits two dependency deprecation warnings. Tests pass with the locked versions.
- Browser state updates arrive by polling, roughly once per second. Cancellation waits for the current bounded call to return, then retains completed observations. Retry preserves consumed attempts and cumulative per-photo inference time.

## Expanded evidence runs

The current protocol and results are in [Evidence comparison](evidence-comparison.md). `scripts/evaluate_pairs.py` accepts `--split development` or `--split reserved_evaluation`, and `--mode policy` or `--mode forced_pair`. `--output` must name a new file. `scripts/evaluate_crops.py --output data/my-crop-results.json` runs the fixed three-photo exploratory crop pilot. Both runners retain actual events and source hashes. Their fake-model unit tests verify metric denominators separately from real local-model measurements.

The frozen paired outputs predate the explicit selected-region action guard and cumulative retry-time correction. Those runs used neither regions nor retries. Their hashes are retained as measured; the crop and browser integration records exercise the later code. A new run on the reserved photographs after policy tuning would be reuse, not a fresh holdout.

## Explicit local controller selection

The default is `qwen3:4b`. After ordinary setup, the reviewed candidate can be downloaded explicitly:

```sh
sh scripts/download_controller.sh qwen3.5:4b
BREEDFRAME_CONTROLLER=qwen3.5:4b sh scripts/start.sh
```

The download script uses a temporary loopback server on port 11435 and verifies the downloaded digest. It stops if that port is occupied. It does not change the inference server's network policy. The application then runs under the existing offline policy on port 8765. Stop an existing app before starting another instance. Omit `BREEDFRAME_CONTROLLER` to use the baseline again; there is no automatic fallback.

The launcher, health endpoint and controller verify the selected model's pinned identity. Saved model events include the requested/returned name, digest, text-only request hash, token counts and loading duration. The memory sampler attributes residency to the selected model and retains the full loaded-model inventory. Raw requests are saved only by the explicit public-development probe.

For the fixed candidate comparison, set the same environment variable before `scripts/evaluate_pairs.py`. Each output must be a new path. The comparison's committed protocol and source snapshots are in `docs/evidence/controller-comparison/`. These public fixtures have already been observed; they are not a fresh holdout for future tuning.
