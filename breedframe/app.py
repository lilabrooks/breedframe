import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import Agent
from .classifier import Classifier
from .config import CONTROLLER, LIMITATIONS, MAX_UPLOAD, MODEL_DIR, ROOT
from .controller import Controller
from .contracts import RegionSelection
from .evidence import compare
from .presentation import describe_assessment
from .store import Store
from .model_identity import verify_controller

store = Store()
classifier = Classifier()
agent = Agent(store, Controller(), classifier)
busy = threading.Lock()
executor = ThreadPoolExecutor(max_workers=1)
cancel_requested = threading.Event()
active_job = {"id": None, "baseline": False}


@asynccontextmanager
async def lifespan(app):
    store.recover()
    yield
    executor.shutdown(wait=True)
    classifier.close()


app = FastAPI(title="BreedFrame", docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.method not in {"GET", "HEAD"}:
        origin = request.headers.get("origin")
        if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
            return JSONResponse({"detail": "Same-origin requests only."}, status_code=403)
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Invalid content length."}, status_code=400)
        if length > MAX_UPLOAD + 1024 * 1024:
            return JSONResponse({"detail": "Upload exceeds 12 MiB plus form overhead."}, status_code=413)
        if "content-length" not in request.headers:
            return JSONResponse({"detail": "Content-Length required."}, status_code=411)
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ValueError)
async def value_error(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.exception_handler(FileNotFoundError)
async def missing(request, exc):
    return JSONResponse({"detail": "Case or local asset not found."}, status_code=404)


def acquire():
    if not busy.acquire(blocking=False):
        raise HTTPException(409, "Another local inference operation is active. Wait for it to finish.")


def run_background(case, baseline=False):
    try:
        if baseline:
            started = time.monotonic()
            try:
                output = classifier.classify(store.photo_path(case, case["photos"][-1]["id"]))
                case["baseline"] = dict(
                    status="complete",
                    photo_id=case["photos"][-1]["id"],
                    seconds=round(time.monotonic() - started, 3),
                    **output,
                )
            except Exception as exc:
                case["baseline"] = dict(status="failed", error=str(exc)[:500])
            store.save(case)
        else:
            agent.run(case, cancelled=cancel_requested.is_set)
    except Exception as exc:
        case["status"] = "incomplete"
        case["stop_reason"] = f"Application error: {type(exc).__name__}. Earlier evidence retained."
        store.save(case)
    finally:
        active_job["id"] = None
        busy.release()


def queue(case, baseline=False):
    cancel_requested.clear()
    active_job.update(id=case["id"], baseline=baseline)
    executor.submit(run_background, case, baseline)
    return JSONResponse(present_case(case), status_code=202)


def present_case(case):
    comparison = compare(case)
    return {**case, "comparison": comparison, "assessment": describe_assessment(case, comparison)}


@app.get("/api/health")
def health():
    controller_ready = False
    controller_status = "offline"
    detail = "Ollama is not reachable. Start BreedFrame with sh scripts/start.sh."
    try:
        with httpx.Client(timeout=2, trust_env=False) as client:
            verify_controller(CONTROLLER, client)
            controller_ready = True
            controller_status = "ready"
            detail = f"Pinned local controller ready: {CONTROLLER}."
    except (ValueError, KeyError, TypeError) as exc:
        controller_status = "unavailable"
        detail = str(exc)
    except httpx.HTTPError:
        pass
    missing_assets = []
    for name in ("model.safetensors", "config.json", "preprocessor_config.json"):
        try:
            path = MODEL_DIR / name
            available = path.is_file() and path.stat().st_size > 0
        except OSError:
            available = False
        if not available:
            missing_assets.append(name)
    vit_ready = not missing_assets
    classifier_detail = "Required vision model files are available."
    if missing_assets:
        classifier_detail = "Missing or empty vision model files: " + ", ".join(missing_assets)
    else:
        try:
            config = json.loads((MODEL_DIR / "config.json").read_text())
            processor = json.loads((MODEL_DIR / "preprocessor_config.json").read_text())
            if len(config["id2label"]) != 120 or not isinstance(processor, dict) or not processor:
                raise ValueError("Invalid vision model configuration")
        except (OSError, ValueError, KeyError, TypeError):
            vit_ready = False
            classifier_detail = "The vision model configuration is incomplete or unreadable. Run setup again."
    return dict(
        ready=controller_ready and vit_ready,
        controller=CONTROLLER,
        controller_ready=controller_ready,
        controller_status=controller_status,
        classifier_ready=vit_ready,
        classifier_detail=classifier_detail,
        missing_classifier_files=missing_assets,
        detail=detail,
        busy=busy.locked(),
        limitations=LIMITATIONS,
    )


def require_models():
    if not health()["ready"]:
        raise HTTPException(
            503,
            "Scout’s local models aren’t ready yet. Follow the setup instructions, then choose Check again. Your saved cases are still available.",
        )


@app.get("/api/cases")
def list_cases():
    result = []
    for path in sorted(store.root.glob("*/case.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:40]:
        case = json.loads(path.read_text())
        result.append({k: case[k] for k in ("id", "status", "photos")})
    return result


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    case = present_case(store.load(case_id))
    case["cancel_pending"] = active_job["id"] == case_id and cancel_requested.is_set()
    return case


@app.post("/api/cases/{case_id}/cancel")
def cancel(case_id: str):
    store.directory(case_id)
    if active_job["id"] != case_id or active_job["baseline"]:
        raise ValueError("This case has no active agent operation to cancel.")
    cancel_requested.set()
    return {
        "status": "cancel_requested",
        "detail": "The current bounded call may finish before cancellation.",
    }


@app.post("/api/cases/{case_id}/finish-partial")
def finish_partial(case_id: str):
    acquire()
    try:
        return present_case(store.finish_partial(store.load(case_id)))
    finally:
        busy.release()


@app.post("/api/cases/{case_id}/retry")
def retry(case_id: str):
    acquire()
    try:
        require_models()
        return queue(store.retry(store.load(case_id)))
    except Exception:
        busy.release()
        raise


@app.post("/api/cases/{case_id}/regions")
def add_region(case_id: str, selection: RegionSelection):
    acquire()
    try:
        require_models()
        case = store.add_region(store.load(case_id), selection.model_dump())
        case.pop("baseline", None)
        return queue(case)
    except Exception:
        busy.release()
        raise


@app.get("/api/cases/{case_id}/photos/{photo_id}/regions/{region_id}")
def region_image(case_id: str, photo_id: str, region_id: str):
    return FileResponse(store.region_path(store.load(case_id), photo_id, region_id), media_type="image/png")


@app.delete("/api/cases")
def clear_cases():
    acquire()
    try:
        return {"deleted_count": store.clear()}
    finally:
        busy.release()


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    acquire()
    try:
        store.delete(store.load(case_id))
        return {"deleted": case_id}
    finally:
        busy.release()


@app.get("/api/cases/{case_id}/report")
def export_report(case_id: str):
    case = store.load(case_id)
    comparison = compare(case)
    assessment = describe_assessment(case, comparison)
    report = case.get("report")
    text = [
        "# BreedFrame assessment",
        "",
        f"## {assessment['title']}",
        "",
        assessment["detail"],
        assessment["context"],
        f"Source: {assessment['source']}" if assessment["source"] else "",
        assessment["score_note"],
        "",
    ]
    if assessment["candidates"]:
        text += ["### Visual matches for this result", ""]
        text.extend(
            f"- {c['display_label']}: {c['score_text']} model score" for c in assessment["candidates"]
        )
        text.append("")
    text += ["## Evidence by photo", ""]
    for view in comparison["views"]:
        text += [
            f"## {view['photo_id']}",
            f"Quality flags: {', '.join(view['quality_flags']) or 'none recorded'}",
        ]
        for rank in view["rankings"]:
            text.append(f"Event {rank['event_id']} / {rank['region_id'] or 'whole photo'}:")
            text.extend(f"- {c['label']}: raw score {c['score']:.6f}" for c in rank["candidates"])
        text.append("")
    text += [
        "## Notes and assessment details",
        f"Case: {case_id}",
        f"Status: {case['status']}",
        f"Recorded outcome: {report['outcome'] if report else 'No final assessment'}",
        "Saved as a partial assessment." if report and report.get("completed_by") == "user" else "",
        *comparison["blockers"],
        comparison["policy_note"],
        comparison["aggregation"],
        *LIMITATIONS,
    ]
    return Response(
        "\n".join(text) + "\n",
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="breedframe-{case_id[:8]}.md"'},
    )


@app.post("/api/cases")
async def create_case(photo: UploadFile = File(...)):
    acquire()
    try:
        await run_in_threadpool(require_models)
        case = store.create(await photo.read(MAX_UPLOAD + 1))
        return queue(case)
    except Exception:
        busy.release()
        raise
    finally:
        await photo.close()


@app.post("/api/cases/{case_id}/photos")
async def resume_case(case_id: str, photo: UploadFile = File(...)):
    acquire()
    try:
        await run_in_threadpool(require_models)
        case = store.add_photo(store.load(case_id), await photo.read(MAX_UPLOAD + 1))
        case.pop("baseline", None)
        return queue(case)
    except Exception:
        busy.release()
        raise
    finally:
        await photo.close()


@app.post("/api/cases/{case_id}/baseline")
def baseline(case_id: str):
    acquire()
    try:
        require_models()
        case = store.load(case_id)
        if case["status"] in {"ready", "running"}:
            raise ValueError("Wait for the agent to pause or finish.")
        case["baseline"] = {"status": "running"}
        store.save(case)
        return queue(case, baseline=True)
    except Exception:
        busy.release()
        raise


@app.post("/api/demo/{scenario}")
def demo(scenario: str):
    choices = {"clear": "beagle.jpg", "small": "beagle-tiny.png"}
    if scenario not in choices:
        raise HTTPException(404, "Unknown demo")
    acquire()
    try:
        require_models()
        case = store.create((ROOT / "data/demo" / choices[scenario]).read_bytes())
        case["demo"] = True
        store.save(case)
        return queue(case)
    except Exception:
        busy.release()
        raise


@app.post("/api/cases/{case_id}/demo-resume")
def demo_resume(case_id: str):
    acquire()
    try:
        require_models()
        case = store.load(case_id)
        if not case.get("demo"):
            raise ValueError("Upload your own follow-up photo for this case.")
        store.add_photo(case, (ROOT / "data/demo/beagle.jpg").read_bytes())
        case.pop("baseline", None)
        return queue(case)
    except Exception:
        busy.release()
        raise


@app.get("/api/cases/{case_id}/photos/{photo_id}")
def image(case_id: str, photo_id: str):
    return FileResponse(store.photo_path(store.load(case_id), photo_id), media_type="image/png")


@app.get("/api/demo-image")
def demo_image():
    return FileResponse(ROOT / "data/demo/beagle.jpg", media_type="image/jpeg")


@app.get("/")
def index():
    return FileResponse(ROOT / "breedframe/static/index.html")


app.mount("/static", StaticFiles(directory=ROOT / "breedframe/static"), name="static")
