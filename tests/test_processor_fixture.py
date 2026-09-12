import json

import pytest

from scripts.check_processor import FIXTURE, check_processor


def test_processor_comparison_ignores_json_formatting(tmp_path):
    config = json.loads(FIXTURE.read_text())
    (tmp_path / "preprocessor_config.json").write_text(json.dumps(config, sort_keys=True))
    check_processor(tmp_path)


@pytest.mark.parametrize(
    "key,value",
    [
        ("size", {"height": 384, "width": 384}),
        ("resample", 3),
        ("do_resize", False),
        ("do_rescale", False),
        ("rescale_factor", 1.0),
        ("do_normalize", False),
        ("image_mean", [0.0, 0.0, 0.0]),
        ("image_std", [1.0, 1.0, 1.0]),
        ("image_processor_type", "OtherProcessor"),
    ],
)
def test_processor_drift_names_changed_setting(tmp_path, key, value):
    config = json.loads(FIXTURE.read_text())
    config[key] = value
    (tmp_path / "preprocessor_config.json").write_text(json.dumps(config))
    with pytest.raises(ValueError, match=f"Processor fixture drift.*{key}"):
        check_processor(tmp_path)


def test_processor_missing_field_fails(tmp_path):
    config = json.loads(FIXTURE.read_text())
    del config["image_mean"]
    (tmp_path / "preprocessor_config.json").write_text(json.dumps(config))
    with pytest.raises(ValueError, match="Processor fixture drift.*image_mean"):
        check_processor(tmp_path)
