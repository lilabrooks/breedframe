"""One killable, persistent inference process. No network during inference."""

import multiprocessing as mp
import os
from pathlib import Path
import threading
import time

from .config import CLASSIFIER_TIMEOUT, MODEL_DIR

TRUNCATED = {29, 57, 59, 85, 87, 90, 113}


def _load_processor(model_dir):
    from transformers import AutoImageProcessor

    return AutoImageProcessor.from_pretrained(model_dir, local_files_only=True, backend="pil")


def _worker(conn, model_dir, preference):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    try:
        import torch
        from PIL import Image
        from transformers import AutoModelForImageClassification

        torch.set_num_threads(4)
        device = "mps" if preference != "cpu" and torch.backends.mps.is_available() else "cpu"
        processor = _load_processor(model_dir)
        model = (
            AutoModelForImageClassification.from_pretrained(
                model_dir, local_files_only=True, use_safetensors=True
            )
            .eval()
            .to(device)
        )
        if len(model.config.id2label) != 120:
            raise ValueError("Classifier requires a 120-class label mapping.")
        while True:
            path = conn.recv()
            if path is None:
                break
            start = time.monotonic()
            fallback = None
            with Image.open(path) as image:
                inputs = processor(images=image.convert("RGB"), return_tensors="pt")
            try:
                with torch.inference_mode():
                    logits = model(**{k: v.to(device) for k, v in inputs.items()}).logits
            except RuntimeError as exc:
                if device != "mps":
                    raise
                fallback = str(exc)[:240]
                model.to("cpu")
                torch.mps.empty_cache()
                device = "cpu"
                with torch.inference_mode():
                    logits = model(**inputs).logits
            scores = logits.float().softmax(-1)[0].cpu()
            values, indices = scores.topk(5)
            result = dict(
                candidates=[
                    dict(
                        class_id=int(i),
                        label=model.config.id2label[int(i)],
                        score=round(float(s), 6),
                        unresolved_label=int(i) in TRUNCATED,
                    )
                    for s, i in zip(values, indices)
                ],
                margin=round(float(values[0] - values[1]), 6),
                device=device,
                inference_seconds=round(time.monotonic() - start, 4),
                fallback=fallback,
                mps_allocated_bytes=torch.mps.current_allocated_memory() if device == "mps" else 0,
                mps_driver_bytes=torch.mps.driver_allocated_memory() if device == "mps" else 0,
            )
            conn.send({"ok": result})
    except Exception as exc:
        conn.send({"error": f"{type(exc).__name__}: {exc}"[:500]})
    finally:
        conn.close()


class Classifier:
    def __init__(self, model_dir=MODEL_DIR, device="auto", timeout=CLASSIFIER_TIMEOUT):
        self.model_dir, self.device, self.timeout = str(model_dir), device, timeout
        self.process = None
        self.conn = None
        self.lock = threading.Lock()

    def classify(self, path):
        with self.lock:
            if self.process is None or not self.process.is_alive():
                self.close()
                # Missing assets should fail before process startup or heavy ML imports.
                try:
                    for name in ("config.json", "preprocessor_config.json", "model.safetensors"):
                        asset = Path(self.model_dir) / name
                        if not asset.is_file() or asset.stat().st_size == 0:
                            raise OSError(f"Missing or empty classifier file: {asset}. Run scripts/setup.sh.")
                except OSError as exc:
                    raise RuntimeError(f"OSError: {exc}") from exc
                self.conn, child = mp.get_context("spawn").Pipe()
                self.process = mp.get_context("spawn").Process(
                    target=_worker, args=(child, self.model_dir, self.device), daemon=True
                )
                self.process.start()
                child.close()
            try:
                self.conn.send(str(path))
                if not self.conn.poll(self.timeout):
                    raise TimeoutError("Classifier time limit exceeded; worker terminated.")
                result = self.conn.recv()
                if "error" in result:
                    raise RuntimeError(result["error"])
                return result["ok"]
            except Exception:
                self.close()
                raise

    def close(self):
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()
            self.process.join(timeout=3)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=3)
        if self.conn is not None:
            self.conn.close()
        self.process = self.conn = None
