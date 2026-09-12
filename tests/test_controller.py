import json

import httpx
import pytest

from breedframe import controller as module
from breedframe.config import CONTROLLER_MODELS
from breedframe.controller import Controller
from breedframe.model_identity import verify_controller
from breedframe.store import Store
from test_agent import textured_photo


def transport_for(model, requests, digest=None, returned=None):
    def handle(request):
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": model, "digest": digest or CONTROLLER_MODELS[model]}]}
            )
        assert request.url.path == "/api/chat"
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": returned or model,
                "message": {
                    "content": json.dumps(
                        {"call": {"tool": "inspect_image", "arguments": {"photo_id": "photo-1"}}}
                    )
                },
            },
        )

    return httpx.MockTransport(handle)


def test_models_get_identical_text_only_payloads(tmp_path, monkeypatch):
    case = Store(tmp_path).create(textured_photo())
    original_client = httpx.Client
    payloads = []
    for model in CONTROLLER_MODELS:
        requests = []
        transport = transport_for(model, requests)
        monkeypatch.setattr(module.httpx, "Client", lambda **kw: original_client(transport=transport, **kw))
        name, args, metrics = Controller(model).choose(case, 6)
        assert name == "inspect_image" and args == {"photo_id": "photo-1"}
        assert metrics["model"] == metrics["returned_model"] == model
        assert metrics["digest"] == CONTROLLER_MODELS[model] and metrics["image_count"] == 0
        request = requests[0]
        assert request.pop("model") == model and request["think"] is False
        assert request["options"]["presence_penalty"] == 0
        assert all(set(m) == {"role", "content"} for m in request["messages"])
        payloads.append(request)
    assert payloads[0] == payloads[1]


def test_wrong_installed_digest_prevents_inference(tmp_path, monkeypatch):
    model, requests = "qwen3.5:4b", []
    original_client = httpx.Client
    transport = transport_for(model, requests, digest="changed")
    monkeypatch.setattr(module.httpx, "Client", lambda **kw: original_client(transport=transport, **kw))
    with pytest.raises(ValueError, match="digest changed"):
        Controller(model).choose(Store(tmp_path).create(textured_photo()), 6)
    assert requests == []


def test_returned_model_mismatch_is_rejected(tmp_path, monkeypatch):
    model, requests = "qwen3.5:4b", []
    original_client = httpx.Client
    transport = transport_for(model, requests, returned="qwen3:4b")
    monkeypatch.setattr(module.httpx, "Client", lambda **kw: original_client(transport=transport, **kw))
    with pytest.raises(ValueError, match="identity differs"):
        Controller(model).choose(Store(tmp_path).create(textured_photo()), 6)


def test_unknown_model_has_no_fallback():
    with pytest.raises(ValueError, match="Unknown controller"):
        verify_controller("unreviewed")
