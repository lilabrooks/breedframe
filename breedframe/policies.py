"""Shared action boundary and an explicitly deterministic comparison policy."""

from .contracts import Decision
from .evidence import compare, request_reasons, successful


def decision_context(case, remaining):
    current = case["photos"][-1]
    events = successful(case)
    done = {e["tool"] for e in events if e["photo_id"] == current["id"]}
    comparison = compare(case)
    reasons = request_reasons(case)
    regions = [r["id"] for r in current.get("regions", [])]
    allowed = {"finish_assessment"}
    if "inspect_image" not in done:
        allowed = {"inspect_image"}
    else:
        if "classify_breed" not in done:
            allowed.add("classify_breed")
        if regions and "classify_region" not in done:
            allowed.add("classify_region")
        if reasons:
            allowed.add("request_another_photo")
        # Selecting a region is an explicit user request, not an autonomous proposal.
        region_attempted = any(
            e.get("tool") == "classify_region" and e["photo_id"] == current["id"] for e in case["events"]
        )
        if regions and not region_attempted:
            allowed = {"classify_region"}
    schema = Decision.model_json_schema()
    schema["properties"]["call"]["anyOf"] = [
        ref
        for ref in schema["properties"]["call"]["anyOf"]
        if schema["$defs"][ref["$ref"].split("/")[-1]]["properties"]["tool"]["const"] in allowed
    ]
    schema["$defs"]["PhotoArgs"]["properties"]["photo_id"] = {"enum": [current["id"]]}
    schema["$defs"]["RegionArgs"]["properties"]["photo_id"] = {"enum": [current["id"]]}
    schema["$defs"]["RegionArgs"]["properties"]["region_id"] = {"enum": regions or ["unavailable"]}
    schema["$defs"]["RequestArgs"]["properties"]["reason"] = {"enum": reasons or ["insufficient_evidence"]}
    schema["$defs"]["FinishArgs"]["properties"]["selected_result_id"] = {
        "enum": comparison["report_eligible_ids"] + [None]
    }
    if not comparison["report_eligible_ids"]:
        schema["$defs"]["FinishArgs"]["properties"]["outcome"] = {"const": "inconclusive", "type": "string"}
    state = dict(
        current_photo_id=current["id"],
        photo_count=len(case["photos"]),
        actions_remaining=remaining,
        allowed_tools=sorted(allowed),
        available_region_ids=regions,
        request_reasons=reasons,
        followup_unavailable=bool(case.get("followup_unavailable")),
        comparison=comparison,
        recent_errors=[e["output"] for e in case["events"] if e["status"] == "error"][-2:],
    )
    return state, schema


class RulesController:
    def choose(self, case, remaining, timeout=45):
        state, _ = decision_context(case, remaining)
        allowed = state["allowed_tools"]
        photo = {"photo_id": state["current_photo_id"]}
        if "inspect_image" in allowed:
            action = "inspect_image", photo
        elif "classify_region" in allowed:
            action = "classify_region", dict(**photo, region_id=state["available_region_ids"][0])
        elif "classify_breed" in allowed:
            # Same evidence opportunity even when inspection predicts an inadequate image.
            action = "classify_breed", photo
        elif state["comparison"]["report_eligible_ids"]:
            action = (
                "finish_assessment",
                dict(
                    outcome="visual_matches",
                    selected_result_id=state["comparison"]["report_eligible_ids"][-1],
                ),
            )
        elif "request_another_photo" in allowed and remaining > 1:
            reason = state["request_reasons"][0]
            view = "well_lit_full_body" if reason == "exposure" else "sharp_face_and_body"
            action = "request_another_photo", dict(reason=reason, view=view)
        else:
            action = "finish_assessment", dict(outcome="inconclusive", selected_result_id=None)
        return *action, {"model": "deterministic-policy-v2", "generated": False}
