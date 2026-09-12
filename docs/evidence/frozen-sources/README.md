# Measured sources

These files preserve the exact bytes used by the paired-suitability and new-identity experiments. Their SHA-256 values match the original registrations listed in [manifest.json](manifest.json). The experiment protocols and saved predictions have not been edited.

The two runners were copied before publication formatting. The original HTML was recovered by reversing the final headline and introductory-text changes, then checked against both registered hashes. The maintained runners have the same Python syntax trees as these copies. The archived files are evidence; the application continues to use its current files.

## Checking the historical sources without inference

The original runners deliberately reject changed sources. Do not bypass their guards or replace a registered hash. Restore the archived files over a disposable copy of the repository when checking those experiments:

```sh
experiment_copy=$(mktemp -d /tmp/breedframe-historical.XXXXXX)
git archive HEAD | tar -x -C "$experiment_copy"
cp -R docs/evidence/frozen-sources/scripts "$experiment_copy/"
cp -R docs/evidence/frozen-sources/breedframe "$experiment_copy/"
ln -s "$PWD/data" "$experiment_copy/data"
ln -s "$PWD/models" "$experiment_copy/models"
experiment_python="$PWD/.venv/bin/python"
cd "$experiment_copy"
PYTHONPATH=. "$experiment_python" - <<'PY'
import json
from pathlib import Path
from scripts import evaluate_new_identities as identities
from scripts import evaluate_suitability as suitability

suitability.verify_inputs()
identities.verify_inputs()
root = Path.cwd() / "docs/evidence/identity-comparison"
manifest = json.loads((root / "manifest.json").read_text())
results = json.loads((root / "results.json").read_text())
assert identities.evaluate(manifest, results["calls"]) == results["evaluation"]
print("Registered inputs match; saved case outcomes reproduced without inference.")
PY
```

Run from a committed repository with the original local data, weights and pinned Python environment available. The symlinks expose those local inputs to the disposable copy; they do not download anything. A fresh public clone lacks the ignored inputs and cannot run this check unaided. The check reads inputs and recomputes reports from stored predictions; it does not call models or overwrite historical verification records. It leaves the temporary copy available for inspection.

## Excluded page captures

Three full third-party HTML captures were excluded from the public tree. Their previous paths and hashes are recorded in [excluded-page-captures.json](excluded-page-captures.json); the original bytes remain in ignored local storage. Photo metadata, source URLs and attribution remain in the experiment directory. None of these HTML captures is a registered source-hash input for the two experiments.

The original local Git history contains these pages. Initial publication used the separate parentless `public-main` snapshot (`38f6038`). It includes this archive and the original experiment registrations and results. Future maintenance branches must start from the current remote `main`; the private historical branch must remain outside that ancestry.
