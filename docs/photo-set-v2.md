# Photos for the next BreedFrame experiment

20 downloaded photographs form 13 cases, including 7 pairs of distinct photographs of the same named dog. Selection used source identity, reuse terms and visible conditions. Neither BreedFrame model ran on these images during curation.

Open the [local gallery](../data/photo-set-v2/index.html) or [contact sheet](../data/photo-set-v2/contact-sheet.jpg). The [manifest](evidence/photo-set-v2/manifest.json) records presentation order, source URLs, checksums, labels and split groups. [Attribution](evidence/photo-set-v2/attribution.md) records each photograph's terms separately from the software license.

## Cases

| Case | Photos | What it exercises | Documentary label | Split |
|---|---:|---|---|---|
| Barney | 2 | Small rear-facing subject indoors, then a closer face view | Scottish Terrier | Development |
| Buddy | 2 | Indoor face/body view, then outdoor side profile; age difference is a confound | Labrador Retriever | Development |
| Bo | 2 | Tiny subject at night, then a clear portrait; breed absent from this classifier | Portuguese Water Dog | Development |
| Sully | 2 | Two usable views with a harness and different lighting | Labrador Retriever | Reserved evaluation |
| Champ | 2 | Grass partly obscures the body, then a wider porch view | German Shepherd | Reserved evaluation |
| Millie | 2 | Busy indoor scene with partial occlusion, then outdoor body view | English Springer Spaniel | Reserved evaluation |
| Conan | 2 | Small subject among people, then a front-facing portrait | Belgian Malinois | Reserved evaluation |
| Barney and Miss Beazley | 1 | Multiple small dogs; target selection needed | No single target label | Development |
| Champ and Major | 1 | Multiple dogs indoors; target selection needed | No single target label | Reserved evaluation |
| Socks | 1 | Cat control | No live dog | Development |
| Horse | 1 | Another four-legged animal, partly covered by a rug | No live dog | Reserved evaluation |
| Dog sculptures | 1 | Dog-shaped objects | No live dog | Development |
| Topper | 1 | Source-described mixed-breed terrier | Exact ancestry unknown | Reserved evaluation |

The classifier's exact labels were checked against its local configuration: `scotch_terrier`, `labrador_retriever`, `german_shepherd`, `english_springer` and `malinois`. Bo's breed has no corresponding class. No truncated class name was expanded.

Pair identity comes from captions naming each dog in both files. Breed evidence links are recorded separately. These are source-reported labels, without independent pedigree or genetic verification. Topper's source describes a mixed-breed terrier; it does not establish ancestry percentages.

## Use and verification

From the repository root:

```sh
.venv/bin/python scripts/fetch_photo_set.py --check-only
```

On another checkout, omit `--check-only` to download the pinned files and build the gallery. The downloader checks SHA-256 before accepting a file and stops on HTTP errors. If an upstream rendition changes, review it before changing the recorded hash.

The local images occupy about 6.2 MB (decimal). The `data/` directory remains ignored by git; the manifest, attribution and downloader can be committed. Other than the 2 retained Barney originals, these are Commons renditions at recorded widths of 330–1280 pixels. Those resizing choices are part of the experiment's input conditions. Upstream Commons files may already contain edits or crops.

Each file was visually reviewed and passed the application's image normalization checks. Pixel hashes were checked for exact duplicate images. No classifier or controller results were used to accept, reject or order a case. The verification record is in [validation.json](evidence/photo-set-v2/validation.json).

## Evaluation boundary

Freeze the model, prompt, tools and reporting policy before running the reserved cases. Keep all photographs, crops and derived versions in a `leakage_group` in the same split. The two multi-dog cases share their named dogs' groups; Socks stays with Buddy, and the sculptures stay with Barney. The split has 6 development cases and 7 reserved cases. It is too small to be stratified across all conditions.

Use one initial photograph per case. If a policy requests a follow-up, supply the next listed photograph once. For a comparison against a rules-based policy, expose the same tools and photo budget. A forced two-photo run is a separate experiment: report its acquisition cost even when a policy would have stopped after the first photograph. The listed follow-up is a different view, not a promise to satisfy every possible request.

All 13 cases affect completion, request burden, latency, action errors and abstention metrics. Only the 6 pairs with a supported classifier label affect breed report accuracy. Report accuracy over all eligible cases alongside error rate among completed breed reports and coverage. Only those 6 pairs affect labeled follow-up benefit; count both improvements and regressions, and retain pairs that received no request in the overall policy comparison. Bo affects unsupported-breed reporting, Topper affects unsupported ancestry claims, the 2 multi-dog cases affect target-selection behavior, and the 3 non-dog cases affect false live-dog/breed reports. Report development and reserved results separately.

The existing `scripts/evaluate.py` accepts single-photo cases. Use `scripts/evaluate_pairs.py` for this corpus; passing the v2 manifest to the old runner is unsupported. The [current comparison](evidence-comparison.md) records the completed runs. Three development photos have fixed manual region annotations in `evidence/crop-pilot-manifest.json`; the rest of the corpus has no bounding-box annotations.

## Limits and remaining photos

Most photographs come from US presidential or government archives. This supplies documented identities but creates a strong source bias. Public-image overlap with model training is unknown, so “reserved” refers only to BreedFrame development.

Several pairs span months or years. Buddy is visibly younger in the first photograph. These pairs can test evidence comparison, but they cannot establish the effect of immediately retaking a photo after the app's instructions.

The next collection gap is a small set of owner-supplied, same-session pairs: a naturally blurred view followed by a sharp view, and a poorly exposed view followed by a better-lit view. Verified mixed-breed ancestry is also absent. A resized copy or an AI-generated image would not fill those gaps.

No pair is labeled “conflicting predictions” in advance. Observe disagreement during the fixed evaluation and report whether it occurs; do not keep adding photographs until the classifier disagrees. If a guaranteed disagreement path is needed for software testing, use an explicitly synthetic tool-result fixture outside this photo evaluation.
