# Milestone-1 setup and check verification

Software-maintenance validation on 2026-09-12, based on `190acb7` plus this PR's
changes. Host: Apple Silicon M4, macOS; uv 0.12.13 and Node.js 26.8.2. The historical model experiments and their
saved evidence were preserved.

## Dependency candidate

The manifest now pins torch **2.14.0** and torchvision **0.29.0** together.
Installed torchvision metadata requires `torch (==2.14.0)`. A representative
Transformers patch update, **5.10.1 → 5.10.4**, was resolved with:

```sh
uv lock --python 3.11 --upgrade-package transformers==5.10.4
```

The resolved graph contains 71 packages; the Mac environment installs 49.
Transformers is the only resolved package version changed. The following checks
use 5.10.4; future dependency proposals still need their own validation.

## Environment selection

A source snapshot and disposable environments were created under
`/private/tmp/breedframe-m1-1g68paxw`. Python 3.11.16, 3.12.13 and 3.13.12 were
available, alongside a PATH default of Python 3.14.7.

| Route | Actual executable relative to that temporary root | Observed Python |
|---|---|---|
| Custom checks, starting with a 3.13 environment | `check-env/bin/python` | 3.11.16 |
| Fresh checks after the missing-asset fix | `fixed-env/bin/python` | 3.11.16 |
| Setup-first environment | `repo/.venv/bin/python` | 3.11.16 |

Each route ran with `UV_NO_CONFIG=1` and `UV_PYTHON=3.13`; explicit `--python`
selection won. Custom checks used `UV_PROJECT_ENVIRONMENT` and separate fresh uv
caches. Setup ran with that override unset and created `.venv` from scratch.
It reused copied trained ViT assets, the bundled Ollama binary, the existing
reviewed Ollama server and a dependency cache. This setup run verifies selection
and the new processor comparison; the earlier isolated onboarding run remains
the evidence for downloading all models from scratch.

Setup completed and the processor comparison passed. A custom setup-environment
override failed immediately with an instruction to unset it. The startup script
was then exercised in the temporary checkout with only its port changed from
8765 to 18765. Shell tracing showed `.venv/bin/python` and `.venv/bin/uvicorn`,
and the live process used Homebrew's CPython 3.11.16. This held even with
`UV_PROJECT_ENVIRONMENT` pointing at the separate check environment.

## Required checks and the startup failure

The first fresh check, before the targeted classifier fix, failed with
**86 passed, 1 failed** in 54.81 seconds. As in the earlier onboarding run, the
empty-model test hit its 20-second worker deadline before reporting missing
assets. No phase profiling established which heavy initialization step was slow.
The failure was retained, without a retry to replace it.

The fix checks required, nonempty files before spawning. Tests reject each absent
or empty asset without allowing multiprocessing initialization. A separate real
stalled worker still exercises the deadline and cleanup. This resolves the narrow
startup failure from [#13](https://github.com/lilabrooks/breedframe/issues/13);
its warning, shared-helper and optional coverage work remains open.

The next run used a new environment and new package cache: **92 Python tests
passed**, with the two existing upstream deprecation warnings, plus **17 Node
tests**, Ruff and JavaScript syntax checks. It loaded the real processor and
generated-weight worker with model downloads disabled. Drift tests changed
resize, rescaling, normalization, processor type and a missing field. The final
setup-environment gate passed **92 Python tests** in 28.62 seconds, the same two
warnings, and **17 Node tests**, plus Ruff and syntax checks. That run includes
the CPU-only seed refinement that avoids changing accelerator RNG state.

## Installed models and repository settings

A real Scout demo completed through the temporary FastAPI app using Qwen3 and
the trained ViT on MPS. Its recorded tools inspected the photo, classified it,
and finished the assessment. The leading visual match was Beagle, score
`0.175492`; the report remained inconclusive under the existing evidence gate.
This is integration evidence, with reused assets and prior library activity,
and provides no new accuracy or cold-start benchmark.

The temporary app was stopped. The original site remained ready, and both files
in its existing case store retained their hashes. No browser-hardening scenarios
were claimed by this run.

Both workflow and Dependabot YAML parsed; shell syntax and repository hygiene
checks passed. GitHub reported security updates enabled and unpaused, and the
vulnerability-alert endpoint returned 204. The new weekly uv and Actions schedule
and paired torch groups take effect after merging the configuration onto `main`.
