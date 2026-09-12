import json
import hashlib
import httpx

from .config import CONTROLLER, CONTROLLER_MODELS, CONTROLLER_TIMEOUT, OLLAMA_URL
from .contracts import Decision, DESCRIPTIONS
from .policies import decision_context
from .model_identity import verify_controller

SYSTEM = """Choose one action for a dog-photo case. Return only the JSON decision. /no_think
You are text-only. Numerical observations cannot confirm dog presence or anatomy.
Inspect each photo before other work. Classify when a ranking could be useful.
The comparison contains all observed views. Its candidates combine distinct-photo votes,
not probabilities. Crops are correlated with their source photo; disagreement stays unresolved.
If a user-selected region is available, classification of that region can investigate framing.
Before stopping on weak or conflicting evidence, consider whether another view could help.
Request only a reason in request_reasons. Do not request if followup_unavailable is true.
Finish with visual_matches only using report_eligible_ids. These are heuristic eligibility,
not calibrated confidence or proof of dog presence. Otherwise finish inconclusive with null.
No unsupported claims or repeated completed work. At most six attempts per photo and three photos.
"""


class Controller:
    def __init__(self, model=CONTROLLER):
        if model not in CONTROLLER_MODELS:
            raise ValueError("Unknown controller; choose a reviewed local model.")
        self.model = model
        self.identity = None
        self.last_request = None

    def choose(self, case, remaining, timeout=CONTROLLER_TIMEOUT):
        state, schema = decision_context(case, remaining)
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            if self.identity is None:
                self.identity = verify_controller(self.model, client)
            request = dict(
                model=self.model,
                messages=[
                    dict(role="system", content=SYSTEM + "\nTools: " + json.dumps(DESCRIPTIONS)),
                    dict(role="user", content=json.dumps(state) + "\nReturn one JSON decision. /no_think"),
                ],
                format=schema,
                stream=False,
                think=False,
                options=dict(
                    temperature=0,
                    seed=42,
                    num_ctx=8192,
                    num_predict=500,
                    presence_penalty=0,
                    repeat_penalty=1,
                    top_k=20,
                    top_p=0.95,
                ),
                keep_alive="30m",
            )
            self.last_request = request
            response = client.post(
                OLLAMA_URL + "/api/chat",
                json=request,
            )
            response.raise_for_status()
        payload = response.json()
        if payload.get("model") != self.model:
            raise ValueError("The returned controller identity differs from the requested model.")
        decision = Decision.model_validate_json(payload["message"]["content"]).call
        return (
            decision.tool,
            decision.arguments.model_dump(),
            {
                "model": self.model,
                "returned_model": payload["model"],
                "digest": self.identity["digest"],
                "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
                "image_count": sum(len(m.get("images", [])) for m in request["messages"]),
                "think": request["think"],
                "eval_count": payload.get("eval_count"),
                "prompt_eval_count": payload.get("prompt_eval_count"),
                "load_duration_ns": payload.get("load_duration"),
                "total_duration_ns": payload.get("total_duration"),
            },
        )
