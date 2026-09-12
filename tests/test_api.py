import time
import json
import httpx
from fastapi.testclient import TestClient
import pytest
from breedframe import app as api
from breedframe.agent import Agent
from breedframe.store import Store
from test_agent import photo, textured_photo, FakeClassifier, ScriptedController


def model_files(directory):
    directory.mkdir()
    (directory / "model.safetensors").write_bytes(b"fake weights; API tests use FakeClassifier")
    (directory / "config.json").write_text(json.dumps({"id2label": {str(i): str(i) for i in range(120)}}))
    (directory / "preprocessor_config.json").write_text('{"size": 224}')


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(tmp_path / "cases")
    model_dir = tmp_path / "ready-model"
    model_files(model_dir)
    monkeypatch.setattr(api, "MODEL_DIR", model_dir)
    monkeypatch.setattr(api, "verify_controller", lambda *args: None)
    fake = FakeClassifier()
    controller = ScriptedController(
        [
            ("inspect_image", {"photo_id": "photo-1"}),
            ("request_another_photo", {"reason": "low_resolution", "view": "closer_full_body"}),
            ("inspect_image", {"photo_id": "photo-2"}),
            ("classify_breed", {"photo_id": "photo-2"}),
            ("finish_assessment", {"outcome": "visual_matches", "selected_result_id": 4}),
        ]
    )
    monkeypatch.setattr(api, "store", store)
    monkeypatch.setattr(api, "classifier", fake)
    monkeypatch.setattr(api, "agent", Agent(store, controller, fake))
    yield TestClient(api.app)
    deadline = time.monotonic() + 5
    while api.busy.locked() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not api.busy.locked()


def terminal(client, case_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        case = client.get(f"/api/cases/{case_id}").json()
        if case["status"] not in {"ready", "running"} and not api.busy.locked():
            return case
        time.sleep(0.01)
    raise AssertionError("Case did not stop")


def test_http_upload_pause_resume_and_pixels(client):
    response = client.post(
        "/api/cases", files={"photo": ("private-beagle.jpg", photo(size=(48, 32)), "image/png")}
    )
    assert response.status_code == 202
    case_id = response.json()["id"]
    paused = terminal(client, case_id)
    assert paused["status"] == "awaiting_photo"
    assert "private-beagle" not in str(paused)
    response = client.post(
        f"/api/cases/{case_id}/photos", files={"photo": ("another.png", textured_photo(), "image/png")}
    )
    assert response.status_code == 202
    resumed = terminal(client, case_id)
    assert resumed["status"] == "complete"
    assert len(resumed["photos"]) == 2
    assert resumed["events"][:2] == paused["events"]
    image = client.get(f"/api/cases/{case_id}/photos/photo-2")
    assert image.status_code == 200 and image.headers["content-type"] == "image/png"
    assert "no-store" in image.headers["cache-control"]


def test_same_origin_and_upload_validation(client):
    response = client.post(
        "/api/cases",
        headers={"origin": "https://example.com"},
        files={"photo": ("x.png", photo(), "image/png")},
    )
    assert response.status_code == 403
    response = client.post("/api/cases", files={"photo": ("x.png", b"junk", "image/png")})
    assert response.status_code == 422
    assert not api.busy.locked()
    assert client.get("/api/cases/not-an-id").status_code == 422


def test_concurrent_work_is_rejected(client):
    api.busy.acquire()
    try:
        response = client.post("/api/cases", files={"photo": ("x.png", photo(), "image/png")})
        assert response.status_code == 409
    finally:
        api.busy.release()


@pytest.mark.parametrize(
    ("length", "status", "detail"),
    [
        ("invalid", 400, "Invalid content length."),
        (str(api.MAX_UPLOAD + 1024 * 1024 + 1), 413, "Upload exceeds 12 MiB plus form overhead."),
        (None, 411, "Content-Length required."),
    ],
)
def test_content_length_rejected_before_creating_case(client, length, status, detail):
    request = client.build_request("POST", "/api/cases", files={"photo": ("x.png", photo(), "image/png")})
    if length is None:
        del request.headers["content-length"]
    else:
        request.headers["content-length"] = length
    response = client.send(request)
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert not list(api.store.root.iterdir())
    assert not api.busy.locked()


def test_untrusted_host_is_rejected(client):
    response = client.get("/api/cases", headers={"host": "example.com"})
    assert response.status_code == 400
    assert response.text == "Invalid host header"


@pytest.mark.parametrize("controller_ready", [True, False])
@pytest.mark.parametrize(
    "missing_asset", [None, "model.safetensors", "config.json", "preprocessor_config.json"]
)
def test_health_reports_controller_and_asset_availability(
    client, monkeypatch, tmp_path, controller_ready, missing_asset
):
    model_dir = tmp_path / "model"
    model_files(model_dir)
    if missing_asset:
        (model_dir / missing_asset).unlink()
    monkeypatch.setattr(api, "MODEL_DIR", model_dir)

    def verify(*args):
        if not controller_ready:
            raise ValueError("Controller identity mismatch.")

    monkeypatch.setattr(api, "verify_controller", verify)
    response = client.get("/api/health")
    assert response.status_code == 200
    health = response.json()
    assert health["classifier_ready"] is (missing_asset is None)
    assert health["ready"] is (controller_ready and missing_asset is None)
    if not controller_ready:
        assert health["detail"] == "Controller identity mismatch."


def test_background_error_retains_evidence_and_releases_job(client, monkeypatch):
    def fail_after_evidence(case, **kwargs):
        case["events"].append({"id": 1, "kind": "test_evidence", "status": "ok"})
        raise RuntimeError("Unexpected application failure")

    monkeypatch.setattr(api.agent, "run", fail_after_evidence)
    response = client.post("/api/cases", files={"photo": ("x.png", photo(), "image/png")})
    assert response.status_code == 202
    case = terminal(client, response.json()["id"])
    assert case["status"] == "incomplete"
    assert case["stop_reason"] == "Application error: RuntimeError. Earlier evidence retained."
    assert case["events"] == [{"id": 1, "kind": "test_evidence", "status": "ok"}]
    assert api.active_job["id"] is None
    assert not api.busy.locked()


def test_partial_followup_region_export_and_delete(client):
    from breedframe.policies import RulesController

    response = client.post("/api/cases", files={"photo": ("tiny.png", photo(size=(48, 32)), "image/png")})
    case_id = response.json()["id"]
    assert terminal(client, case_id)["status"] == "awaiting_photo"
    partial = client.post(f"/api/cases/{case_id}/finish-partial").json()
    assert partial["report"]["completed_by"] == "user"
    assert partial["report"]["outcome"] == "inconclusive"
    api.agent.controller = RulesController()
    response = client.post(
        f"/api/cases/{case_id}/photos", files={"photo": ("new.png", textured_photo(), "image/png")}
    )
    assert response.status_code == 202
    finished = terminal(client, case_id)
    assert finished["report"]["outcome"] == "visual_matches"
    assert finished["report_history"][0]["completed_by"] == "user"
    response = client.post(
        f"/api/cases/{case_id}/regions",
        json=dict(photo_id="photo-2", left=0.0, top=0.0, right=0.8, bottom=1.0),
    )
    assert response.status_code == 202
    region_case = terminal(client, case_id)
    assert region_case["attempts"]["photo-2"] == 5
    assert region_case["report"]["comparison"]["ranked_photo_count"] == 1
    assert client.get(f"/api/cases/{case_id}/photos/photo-2/regions/region-1").status_code == 200
    report = client.get(f"/api/cases/{case_id}/report")
    assert report.status_code == 200 and "attachment" in report.headers["content-disposition"]
    assert "region-1" in report.text and "raw score" in report.text
    assert client.request("DELETE", f"/api/cases/{case_id}", json={}).status_code == 200
    assert client.get(f"/api/cases/{case_id}").status_code == 404
    assert not api.store.directory(case_id).exists()


def test_saved_tentative_match_uses_same_summary_in_api_and_report(client):
    from test_presentation import case_with_rankings

    case = api.store.create(textured_photo())
    case.update(events=case_with_rankings()["events"], status="complete")
    case["report"] = {"outcome": "inconclusive", "candidates": []}
    api.store.save(case)
    response = client.get(f"/api/cases/{case['id']}")
    summary = response.json()["assessment"]
    assert summary["title"] == "Top visual match: Beagle"
    assert summary["detail"] == "Model score: 17.5%"
    report = client.get(f"/api/cases/{case['id']}/report").text
    assert summary["title"] in report
    assert summary["detail"] in report
    assert "Beagle: 17.5% model score" in report
    assert report.index("Top visual match") < report.index("Recorded outcome: inconclusive")
    assert "raw score 0.175000" in report
    assert api.store.load(case["id"])["report"]["outcome"] == "inconclusive"


def test_clear_cases_removes_photos_reports_and_cases_beyond_recent_list(client):
    case_ids = []
    for index in range(41):
        case = api.store.create(photo())
        case["status"] = ["complete", "awaiting_photo", "incomplete"][index % 3]
        case["report"] = {"outcome": "inconclusive", "candidates": []}
        api.store.save(case)
        case_ids.append(case["id"])
    unrelated = api.store.root / "notes.txt"
    unrelated.write_text("Keep unrelated files.")
    assert len(client.get("/api/cases").json()) == 40
    response = client.request("DELETE", "/api/cases", json={})
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 41}
    assert client.get("/api/cases").json() == []
    assert all(not api.store.directory(case_id).exists() for case_id in case_ids)
    assert unrelated.read_text() == "Keep unrelated files."
    assert client.request("DELETE", "/api/cases", json={}).json() == {"deleted_count": 0}
    assert not api.busy.locked()


@pytest.mark.parametrize("operation", ["ready", "running", "baseline"])
def test_clear_cases_checks_all_operations_before_deleting_any(client, operation):
    completed = api.store.create(photo())
    completed["status"] = "complete"
    api.store.save(completed)
    active = api.store.create(photo())
    active["status"] = operation if operation != "baseline" else "complete"
    if operation == "baseline":
        active["baseline"] = {"status": "running"}
    api.store.save(active)
    response = client.request("DELETE", "/api/cases", json={})
    assert response.status_code == 422
    assert api.store.load(completed["id"]) == completed
    assert api.store.load(active["id"]) == active
    assert not api.busy.locked()


def test_clear_cases_rejects_busy_and_cross_origin_requests(client):
    case = api.store.create(photo())
    case["status"] = "complete"
    api.store.save(case)
    api.busy.acquire()
    try:
        assert client.request("DELETE", "/api/cases", json={}).status_code == 409
    finally:
        api.busy.release()
    response = client.request("DELETE", "/api/cases", json={}, headers={"origin": "https://example.com"})
    assert response.status_code == 403
    assert api.store.load(case["id"]) == case


def test_clear_cases_rejects_mismatched_saved_identifiers_before_deleting(client):
    import json

    case = api.store.create(photo())
    case["status"] = "complete"
    api.store.save(case)
    other = api.store.create(photo())
    other.update(status="complete", id=case["id"])
    other_path = next(p for p in api.store.root.glob("*/case.json") if p.parent.name != case["id"])
    other_path.write_text(json.dumps(other))
    assert client.request("DELETE", "/api/cases", json={}).status_code == 422
    assert api.store.load(case["id"]) == case
    assert other_path.exists()
    assert not api.busy.locked()


@pytest.mark.parametrize(
    "failure", [httpx.ConnectError("offline"), httpx.ReadTimeout("slow"), ValueError("wrong digest")]
)
def test_health_controller_failure_and_recovery(client, monkeypatch, failure):
    def fail(*args):
        raise failure

    monkeypatch.setattr(api, "verify_controller", fail)
    health = client.get("/api/health").json()
    assert not health["ready"] and not health["controller_ready"]
    assert health["classifier_ready"]
    assert health["controller_status"] == ("unavailable" if isinstance(failure, ValueError) else "offline")
    monkeypatch.setattr(api, "verify_controller", lambda *args: None)
    assert client.get("/api/health").json()["ready"]


@pytest.mark.parametrize(
    "asset,content",
    [
        ("model.safetensors", b""),
        ("config.json", b"broken"),
        ("config.json", b"{}"),
        ("preprocessor_config.json", b"null"),
    ],
)
def test_health_rejects_incomplete_classifier(client, asset, content):
    (api.MODEL_DIR / asset).write_bytes(content)
    health = client.get("/api/health").json()
    assert not health["ready"] and not health["classifier_ready"]
    assert health["controller_ready"]


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/cases",
        "/api/demo/clear",
        "/api/demo/small",
        "/api/cases/{id}/photos",
        "/api/cases/{id}/retry",
        "/api/cases/{id}/regions",
        "/api/cases/{id}/baseline",
        "/api/cases/{id}/demo-resume",
    ],
)
def test_unavailable_models_reject_inference_before_mutation(client, monkeypatch, endpoint):
    response = client.post("/api/cases", files={"photo": ("x.png", photo(size=(48, 32)), "image/png")})
    case_id = response.json()["id"]
    terminal(client, case_id)
    before = {
        str(p.relative_to(api.store.root)): p.read_bytes() for p in api.store.root.rglob("*") if p.is_file()
    }
    monkeypatch.setattr(api, "health", lambda: {"ready": False})
    url = endpoint.format(id=case_id)
    kwargs = {}
    if endpoint == "/api/cases" or endpoint.endswith("/photos"):
        kwargs["files"] = {"photo": ("x.png", textured_photo(), "image/png")}
    elif endpoint.endswith("/regions"):
        kwargs["json"] = {"photo_id": "photo-1", "left": 0, "top": 0, "right": 1, "bottom": 1}
    response = client.post(url, **kwargs)
    assert response.status_code == 503
    assert "Scout" in response.json()["detail"]
    assert not api.busy.locked()
    after = {
        str(p.relative_to(api.store.root)): p.read_bytes() for p in api.store.root.rglob("*") if p.is_file()
    }
    assert before == after
    assert client.get(f"/api/cases/{case_id}").status_code == 200
    assert client.get("/api/cases").status_code == 200
    assert client.post(f"/api/cases/{case_id}/finish-partial").status_code == 200
    assert client.get(f"/api/cases/{case_id}/report").status_code == 200
