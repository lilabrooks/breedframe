import time
from fastapi.testclient import TestClient
import pytest
from breedframe import app as api
from breedframe.agent import Agent
from breedframe.store import Store
from test_agent import photo, textured_photo, FakeClassifier, ScriptedController


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = Store(tmp_path)
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
    model_dir.mkdir()
    for name in ("model.safetensors", "config.json", "preprocessor_config.json"):
        if name != missing_asset:
            (model_dir / name).touch()
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
