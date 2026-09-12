# Screenshots

## Current Scout interface

These captures show the running application on 2026-09-12, using the public full-resolution Beagle demo with real Qwen3 4B and ViT calls. Both use a 1280 × 720 browser viewport. The screenshot instance used a separate temporary case store, leaving the user's saved cases untouched.

| Capture | Purpose |
|---|---|
| [scout-working.png](scout-working.png) | README overview: the vision-model call in progress, with Scout's step cards, live banner, and photo evidence. |
| [scout-assessment.png](scout-assessment.png) | Usage guide: the completed demo's top visual match, 17.5% model score, alternative rankings, and tentative-match explanation. |

Both images come from the same local demo case, `820aa93206c64d5abdae181a2f4ed332`. The recorded path was image inspection, breed classification, then assessment. The captures show real UI states and results, with no fabricated progress or scores. This documentation run isn't an accuracy evaluation and doesn't alter the saved experiment results.

Keep current product documentation to these two views. Capture replacements from the running app when the relevant flow changes, using a separate temporary store and public demo input. Record the capture date and context here; don't overwrite historical evidence with a newer interface. A screenshot alone doesn't verify the whole workflow or mobile accessibility.

## Historical evidence

The files below preserve earlier interfaces. They are retained for experiment and verification provenance, and aren't current product screenshots. Their bytes are listed in the [baseline-preservation record](../evidence/controller-comparison/baseline-preservation.json).

| Capture | Historical role |
|---|---|
| [comparison-v2.png](comparison-v2.png) | Desktop evidence and region comparison referenced by the v2 results and product review. |
| [comparison-mobile-v2.png](comparison-mobile-v2.png) | The 390-pixel mobile view from the same v2 browser verification. |
| [paused.png](paused.png) | Earlier desktop request for a follow-up photo. Retired from current usage documentation. |
| [resumed.png](resumed.png) | Earlier desktop request/resume demonstration. Retired from current usage documentation. |
| [mobile.png](mobile.png) | The earlier paused state at 390 pixels. Retired from current usage documentation. |

The earlier desktop captures used a 1280-pixel viewport. The [original verification record](../evidence/verification.json) maps the paused, resumed, and mobile images to their recorded cases. Historical screenshots and model experiment records remain unchanged.

## Photo attribution and license

The beagle photograph is by [sannse](https://commons.wikimedia.org/wiki/File:Beagle_600.jpg), licensed [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). It is displayed at a different size inside the application. The low-resolution demo resizes it to 48×32 pixels.

The screenshot PNGs in this directory are distributed under CC BY-SA 3.0. Application code is licensed separately under MIT.
