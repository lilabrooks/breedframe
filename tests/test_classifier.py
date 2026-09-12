import time
import pytest
from breedframe.classifier import Classifier


def test_missing_model_fails_without_download(tmp_path):
    classifier = Classifier(model_dir=tmp_path, timeout=20)
    try:
        with pytest.raises(RuntimeError):
            classifier.classify(tmp_path / "missing.png")
        assert classifier.process is None
    finally:
        classifier.close()


def test_classifier_deadline_kills_worker(tmp_path):
    classifier = Classifier(model_dir=tmp_path, timeout=0.001)
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        classifier.classify(tmp_path / "missing.png")
    assert classifier.process is None
    assert time.monotonic() - started < 5
