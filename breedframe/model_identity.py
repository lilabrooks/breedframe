"""Use an explicitly selected, pinned local model; never substitute on failure."""

import httpx

from .config import CONTROLLER, CONTROLLER_MODELS, OLLAMA_URL


def verify_controller(model=CONTROLLER, client=None):
    if model not in CONTROLLER_MODELS:
        raise ValueError("Unknown controller; choose a reviewed local model.")
    if client is None:
        with httpx.Client(timeout=5, trust_env=False) as connection:
            return verify_controller(model, connection)
    response = client.get(OLLAMA_URL + "/api/tags")
    response.raise_for_status()
    installed = next((m for m in response.json()["models"] if m["name"] == model), None)
    if not installed or installed["digest"] != CONTROLLER_MODELS[model]:
        raise ValueError(f"Pinned controller {model} is unavailable or its digest changed. No substitution.")
    return dict(model=model, digest=installed["digest"], details=installed.get("details", {}))
