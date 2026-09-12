"""RSS sampler; summed RSS is not unique physical unified memory."""

import threading
import time
import httpx
import psutil
from .footprint import physical_footprint
from .config import CONTROLLER


class MemorySampler:
    def __init__(self, controller=CONTROLLER):
        self.controller = controller
        self.peak_rss = 0
        self.samples = 0
        self.peak_footprint = 0
        self.footprint_pids = {}
        self.stop_event = threading.Event()
        self.errors = []
        self.controller_resident = 0
        self.resident_models = []

    def sample(self):
        try:
            processes = {p.pid: p for p in [psutil.Process(), *psutil.Process().children(recursive=True)]}
            for proc in psutil.process_iter(["name", "exe"]):
                if proc.info["name"] == "ollama" and "/breedframe/.runtime/" in (proc.info["exe"] or ""):
                    for p in [proc, *proc.children(recursive=True)]:
                        processes[p.pid] = p
            total = 0
            footprint_total = 0
            for p in processes.values():
                try:
                    total += p.memory_info().rss
                    footprint = physical_footprint(p.pid)
                    if footprint is not None:
                        footprint_total += footprint
                        self.footprint_pids[str(p.pid)] = p.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    pass
            self.peak_rss = max(self.peak_rss, total)
            self.peak_footprint = max(self.peak_footprint, footprint_total)
            self.samples += 1
        except psutil.Error as exc:
            self.errors.append(str(exc))

    def _loop(self):
        while not self.stop_event.wait(0.2):
            self.sample()

    def __enter__(self):
        self.sample()
        self.started = time.monotonic()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop_event.set()
        self.thread.join(timeout=2)
        self.sample()
        try:
            with httpx.Client(trust_env=False, timeout=3) as client:
                models = client.get("http://127.0.0.1:11434/api/ps").json()["models"]
            self.resident_models = models
            self.controller_resident = sum(m["size"] for m in models if m["name"] == self.controller)
        except Exception as exc:
            self.errors.append(str(exc))

    def result(self):
        return dict(
            controller=self.controller,
            peak_combined_rss_bytes=self.peak_rss,
            peak_process_footprint_bytes=self.peak_footprint,
            footprint_pids=self.footprint_pids,
            samples=self.samples,
            ollama_reported_resident_bytes=self.controller_resident,
            resident_models=self.resident_models,
            errors=self.errors,
            method="200ms RSS sampling: evaluation process, classifier child, project-local Ollama and its children, deduplicated by PID. macOS physical footprint uses proc_pid_rusage v0 physical-memory ledger. Per-process totals are an estimate, not a whole-system memory delta. RSS includes shared pages; not a unique physical-memory measurement. Ollama residency and MPS allocation reported separately, never added to RSS.",
        )
