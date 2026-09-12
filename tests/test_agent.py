import io
from PIL import Image, ImageDraw
import pytest
from breedframe.agent import Agent
from breedframe.store import Store
from breedframe.images import normalize_image


def photo(color="gray", size=(320, 240)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, "PNG")
    return out.getvalue()


def textured_photo(seed=0):
    image = Image.new("RGB", (320, 240), "gray")
    draw = ImageDraw.Draw(image)
    for x in range(0, 320, 12):
        draw.line((x, 0, (x + 80 + seed) % 320, 240), fill=(20 + seed, 35, 45), width=4)
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


class FakeClassifier:
    timeout = 60

    def classify(self, path):
        return {"candidates": [{"class_id": 30, "label": "beagle", "score": 0.8}], "margin": 0.6}


class ScriptedController:
    """Tests only. Never used in the app or real demo."""

    def __init__(self, calls):
        self.calls = iter(calls)

    def choose(self, *args):
        item = next(self.calls)
        if isinstance(item, Exception):
            raise item
        return *item, {}


def test_pause_resume_retains_evidence_and_resets_budget(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo(size=(48, 32)))
    agent = Agent(
        store,
        ScriptedController(
            [
                ("inspect_image", {"photo_id": "photo-1"}),
                ("request_another_photo", {"reason": "low_resolution", "view": "well_lit_full_body"}),
            ]
        ),
        FakeClassifier(),
    )
    agent.run(case)
    assert case["status"] == "awaiting_photo" and case["report"] is None
    restored = Store(tmp_path).load(case["id"])
    store.add_photo(restored, textured_photo())
    agent.controller = ScriptedController(
        [
            ("inspect_image", {"photo_id": "photo-2"}),
            ("classify_breed", {"photo_id": "photo-2"}),
            ("finish_assessment", {"outcome": "visual_matches", "selected_result_id": 4}),
        ]
    )
    agent.run(restored)
    assert restored["status"] == "complete"
    assert restored["events"][:2] == case["events"]
    assert restored["attempts"] == {"photo-1": 2, "photo-2": 3}
    assert restored["report"]["candidates"][0]["label"] == "beagle"


def test_invalid_and_duplicate_actions_spend_budget(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    calls = [("inspect_image", {"photo_id": "photo-1"})] * 6
    Agent(store, ScriptedController(calls), FakeClassifier()).run(case)
    assert case["status"] == "incomplete"
    assert case["attempts"]["photo-1"] == 6
    assert len([e for e in case["events"] if e["status"] == "ok"]) == 1
    assert case["report"] is None


def test_fabricated_evidence_rejected(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    agent = Agent(store, None, FakeClassifier())
    with pytest.raises(ValueError):
        agent.execute(case, "finish_assessment", {"outcome": "visual_matches", "selected_result_id": 999})
    with pytest.raises(ValueError):
        agent.execute(case, "classify_breed", {"photo_id": "../../secret"})
    with pytest.raises(ValueError):
        agent.execute(case, "inspect_image", {"photo_id": "photo-1", "arbitrary": True})


def test_controller_failure_preserves_inspection(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    Agent(
        store,
        ScriptedController(
            [
                ("inspect_image", {"photo_id": "photo-1"}),
                RuntimeError("unavailable"),
                RuntimeError("unavailable"),
            ]
        ),
        FakeClassifier(),
    ).run(case)
    assert case["status"] == "incomplete"
    assert case["events"][0]["status"] == "ok"
    assert case["events"][1]["kind"] == "controller_error"


def test_restart_recovery_and_duplicate_upload(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    store.recover()
    restored = store.load(case["id"])
    assert restored["status"] == "incomplete"
    with pytest.raises(ValueError, match="same image"):
        store.add_photo(restored, photo())
    assert len(restored["photos"]) == 1


def test_untrusted_images_and_identifiers(tmp_path):
    with pytest.raises(ValueError):
        normalize_image(b"not an image")
    with pytest.raises(ValueError):
        Store(tmp_path).load("../private")
    raw, meta = normalize_image(photo())
    assert Image.open(io.BytesIO(raw)).info == {}
    assert meta["width"] == 320


def test_deadline_no_fabricated_tool_event(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    Agent(store, None, FakeClassifier(), seconds=0).run(case)
    assert case["status"] == "incomplete" and case["events"] == []


def test_request_reason_must_exist_and_photo_limit(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    Agent(
        store,
        ScriptedController(
            [
                ("inspect_image", {"photo_id": "photo-1"}),
                ("request_another_photo", {"reason": "low_resolution", "view": "closer_full_body"}),
            ]
        ),
        FakeClassifier(),
        budget=2,
    ).run(case)
    assert case["status"] == "incomplete"
    assert case["events"][1]["status"] == "error"
    for color in ("red", "blue"):
        store.add_photo(case, photo(color))
        case["status"] = "incomplete"
        store.save(case)
    with pytest.raises(ValueError, match="three photos"):
        store.add_photo(case, photo("green"))


def test_baseline_restart_clears_running_state(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    case["status"] = "complete"
    case["baseline"] = {"status": "running"}
    store.save(case)
    store.recover()
    restored = store.load(case["id"])
    assert restored["status"] == "complete"
    assert restored["baseline"]["status"] == "failed"


def test_recovery_marks_inflight_tool_interrupted(tmp_path):
    store = Store(tmp_path)
    case = store.create(photo())
    case["status"] = "running"
    case["events"] = [{"id": 1, "kind": "tool", "tool": "classify_breed", "status": "running", "output": {}}]
    store.save(case)
    store.recover()
    recovered = store.load(case["id"])
    assert recovered["status"] == "incomplete"
    assert recovered["events"][0]["status"] == "error"
    assert "result not recorded" in recovered["events"][0]["output"]["error"]
