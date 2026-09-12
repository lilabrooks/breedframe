# Set up the local models

BreedFrame needs **both** models before Scout can investigate: Qwen3 4B for choosing actions and a 120-class dog-breed Vision Transformer for reading photos. Neither model is included in a Git checkout.

## First run

Use an Apple Silicon Mac with Python 3.11 and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed. The prototype was exercised on an M4 MacBook Air with 16 GB memory. Allow several GB of free disk space and an internet connection for setup.

From the repository root, run:

```sh
sh scripts/setup.sh
```

Wait for **Setup complete** before continuing. Setup installs locked Python dependencies, the pinned Ollama 0.34.0 runtime, `qwen3:4b` (Q4_K_M, about 2.5 GB), the pinned ViT checkpoint (about 344 MB), and the attributed demo/evaluation photos. It verifies the controller's reviewed digest, classifier label configuration, and downloaded processor against the committed test fixture.

Setup selects Python **3.11** from [`.python-version`](../.python-version) and installs into **`.venv/`**. Startup, demo, evaluation and Python helper commands use that environment explicitly. If you previously set `UV_PROJECT_ENVIRONMENT` for checks, run `unset UV_PROJECT_ENVIRONMENT` before setup; setup rejects a different environment path before downloading anything. A successful custom-environment test run does not install the app's dependencies into `.venv/`.

| Local path | Contents |
|---|---|
| `.runtime/ollama/` | Bundled Ollama runtime |
| `models/ollama/` | Project-local Qwen3 weights |
| `models/vit/` | `model.safetensors`, `config.json`, and `preprocessor_config.json` for the ViT |
| `.venv/` | Locked Python environment |

Then start the app:

```sh
sh scripts/start.sh
```

Keep that terminal running. Open [BreedFrame](http://127.0.0.1:8765) and wait for **LOCAL MODELS READY**. Choose your own photo or an explicit demo to start Scout. The first real classification loads the ViT into its worker, so it can take longer than later classifications.

## Later sessions

Run `sh scripts/start.sh` from the repository root. Startup verifies the configured controller and classifier configuration; it does not download missing weights. If startup fails, the website may not open. Follow the terminal error and rerun setup when assets are missing.

Ctrl-C stops processes launched by the startup script. Saved cases remain in `data/cases/`. Newly launched Ollama and the app run under the macOS offline policy; a pre-existing Ollama process keeps its own policy. [Storage and offline verification](development.md).

## When Scout is unavailable

If the app is reachable but its models are unavailable, a setup panel identifies the affected component. Upload, demo, retry, region analysis, and direct classification stay disabled. Existing saved cases and reports remain accessible while the app itself is reachable. The page rechecks every 10 seconds, on window focus, and before a new inference request. **Check again** retries immediately; repairing setup does not start an investigation automatically.

| Message or symptom | What to do |
|---|---|
| Ollama is not running or reachable | Keep the startup terminal open. If it exited, run `sh scripts/start.sh` and inspect any terminal error. |
| Model missing or version does not match | An Ollama server already on port 11434 may use a different model directory. Stop that server from its own terminal, then rerun `sh scripts/setup.sh` and `sh scripts/start.sh` so BreedFrame can use its project-local store. |
| Vision files missing, incomplete, or unreadable | Rerun `sh scripts/setup.sh` online and let it finish. The required files belong in `models/vit/`. Preserve the terminal error if setup still fails. |
| Scout can’t reach the local app | Restart with `sh scripts/start.sh`, reopen the local page, then choose **Check again**. Cases remain on disk, but browsing them requires the app server. |
| Setup download fails | Restore internet access and check available disk space, then rerun setup. Readiness checks never pull models themselves. |
| Processor fixture drift | Keep the reported field names. Check that the pinned model revision and repository fixture belong to the same checkout; follow the [fixture review procedure](../tests/fixtures/vit/README.md) before changing either. |

To explicitly repair the default controller download after the bundled runtime has been installed:

```sh
sh scripts/download_controller.sh qwen3:4b
sh scripts/start.sh
```

The download helper uses a temporary server on port 11435 and the project's `models/ollama/` directory. It checks the reviewed digest and stops its own server afterward. Stop an existing BreedFrame app before starting another instance. Downloading into a separate system Ollama store does not set up this repository.

The website's readiness check verifies the available Ollama model identity, nonempty required ViT files, and readable basic classifier configuration. It does **not** load the full checkpoint or run a test inference: a damaged weights file, insufficient memory, or a later runtime failure can still stop an investigation. Recorded failures and completed evidence remain in the case. [Model identities and limitations](../README.md#accuracy-models-and-data).

The default remains `qwen3:4b`; selecting the separately reviewed Qwen3.5 candidate is an [explicit development operation](development.md#explicit-local-controller-selection).
