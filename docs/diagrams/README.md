# Architecture diagrams

[Open the editable draw.io file](breedframe-architecture.drawio). It contains two pages with native shapes, grouped labels and icons, and attached flow connectors. The SVG previews also contain the editable diagram data. Open the `.drawio` file in draw.io / diagrams.net to edit it, then export each page as SVG to refresh the README previews.

| Page | Preview | What it explains |
|---|---|---|
| Runtime architecture | [breedframe-architecture.svg](breedframe-architecture.svg) | Browser requests, FastAPI/Uvicorn, Scout, the Ollama service, the classifier subprocess, shared Python tools, and local storage. The dashed path is optional direct classification, which bypasses Scout. |
| AI and ML inference | [breedframe-inference.svg](breedframe-inference.svg) | Qwen3's numerical context and structured response; photo normalization, ViT preprocessing and inference; raw scores, eligibility, and assessment presentation. |

Blue identifies the browser/API path, purple identifies Scout and text inference, teal identifies image inference and evidence handling, and amber identifies storage. Labels name the libraries and services, so color isn't needed to follow the diagram. The icons are simple editable vector drawings, not third-party brand artwork.

## Scope and process boundaries

The diagrams describe the current default local application as inspected on 2026-09-12. FastAPI/Uvicorn and Ollama are loopback services. Scout, HTTPX, Pydantic, Pillow, NumPy, the evidence rules, and presentation code are application components or libraries. The ViT has its own persistent Python subprocess and communicates with the parent through a multiprocessing Pipe, carrying a file path in and classifier results out.

Setup downloads the runtime and model assets. The normal macOS launcher applies the outbound-network policy to processes it starts; an already running Ollama server retains its own process policy. The diagrams show local inference paths, not a guarantee about every independently launched process.

Qwen3.5, ResNet, and other comparison policies are omitted because they aren't the default runtime. CLI and experiment runners also aren't shown as separate entry points. The [development guide](../development.md) covers those workflows and controller selection. The diagram's budgets are defaults, and its reporting thresholds are uncalibrated heuristics.

## Source references

| Diagram claim | Repository source |
|---|---|
| Browser uploads, polling, Scout activity and assessment | [app.js](../../breedframe/static/app.js), [agent-flow.js](../../breedframe/static/agent-flow.js), [index.html](../../breedframe/static/index.html) |
| API routes, single background job, direct classifier path and shared summaries | [app.py](../../breedframe/app.py) |
| Agent execution, validation, limits and evidence context | [agent.py](../../breedframe/agent.py), [policies.py](../../breedframe/policies.py), [contracts.py](../../breedframe/contracts.py) |
| HTTPX/Ollama request, structured JSON, text-only input and model verification | [controller.py](../../breedframe/controller.py), [model_identity.py](../../breedframe/model_identity.py), [config.py](../../breedframe/config.py) |
| Image normalization and numerical quality checks | [images.py](../../breedframe/images.py) |
| Persistent worker, Pipe, Transformers/PyTorch, MPS fallback and top-five scoring | [classifier.py](../../breedframe/classifier.py) |
| Reviewed processor settings | [processor fixture](../../tests/fixtures/vit/preprocessor_config.json), [model verification record](../evidence/model-verification.json) |
| Reporting eligibility and current-photo summary | [evidence.py](../../breedframe/evidence.py), [presentation.py](../../breedframe/presentation.py) |
| Atomic local case storage | [store.py](../../breedframe/store.py) |
| Runtime services, local assets and network policy | [start.sh](../../scripts/start.sh), [setup.sh](../../scripts/setup.sh), [offline.sb](../../scripts/offline.sb) |

These diagrams describe implementation, not measured model accuracy. The [findings](../findings.md) retain the experiment results and limits.
