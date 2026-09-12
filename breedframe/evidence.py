"""Mechanical comparisons of recorded observations. No generated visual claims."""

from .config import MAX_PHOTOS

MIN_SCORE = 0.5
MIN_MARGIN = 0.15
RANK_TOOLS = {"classify_breed", "classify_region"}


def successful(case, tool=None):
    return [
        e
        for e in case["events"]
        if e.get("kind") == "tool" and e["status"] == "ok" and (tool is None or e["tool"] == tool)
    ]


def weak(output):
    return output["candidates"][0]["score"] < MIN_SCORE or output["margin"] < MIN_MARGIN


def compare(case):
    events = successful(case)
    views, blockers, eligible = [], [], []
    votes = {}
    for photo in case["photos"]:
        inspection = next(
            (e for e in events if e["photo_id"] == photo["id"] and e["tool"] == "inspect_image"), None
        )
        ranks = [e for e in events if e["photo_id"] == photo["id"] and e["tool"] in RANK_TOOLS]
        flags = inspection["output"]["quality_flags"] if inspection else []
        view = dict(
            photo_id=photo["id"],
            inspection_event_id=inspection["id"] if inspection else None,
            quality_flags=flags,
            rankings=[],
            leading_class_ids=[],
        )
        for event in ranks:
            output = event["output"]
            own_flags = output.get("quality_flags", flags)
            row = dict(
                event_id=event["id"],
                region_id=event.get("input", {}).get("region_id"),
                candidates=output["candidates"],
                weak_scores=weak(output),
                quality_flags=own_flags,
            )
            view["rankings"].append(row)
            top = output["candidates"][0]
            view["leading_class_ids"].append(top["class_id"])
            if inspection and not own_flags and not weak(output) and not top.get("unresolved_label", False):
                eligible.append(event["id"])
            for rank, candidate in enumerate(output["candidates"], 1):
                entry = votes.setdefault(
                    candidate["class_id"],
                    dict(
                        class_id=candidate["class_id"],
                        label=candidate["label"],
                        unresolved_label=candidate.get("unresolved_label", False),
                        observations=[],
                    ),
                )
                entry["observations"].append(
                    dict(
                        photo_id=photo["id"],
                        event_id=event["id"],
                        region_id=row["region_id"],
                        rank=rank,
                        score=candidate["score"],
                    )
                )
        view["leading_class_ids"] = sorted(set(view["leading_class_ids"]))
        views.append(view)
    ranked_views = [v for v in views if v["rankings"]]
    leaders = {i for v in ranked_views for i in v["leading_class_ids"]}
    relation = "no_ranking" if not ranked_views else "single_photo"
    if len(leaders) > 1:
        relation = "disagreement"
        blockers.append("Recorded rankings disagree on the leading class, including any region comparisons.")
    elif len(ranked_views) > 1:
        relation = "agreement"
    current = views[-1]
    current_ids = {r["event_id"] for r in current["rankings"]}
    eligible = [i for i in eligible if i in current_ids]
    if not current["inspection_event_id"]:
        blockers.append("The current photo has not been inspected.")
    if not current["rankings"]:
        blockers.append("The current photo has no classifier result.")
    elif not eligible:
        blockers.append(
            "Current results have quality concerns, weak scores, or an unresolved published label."
        )
    # A new unclassified user region is evidence still awaiting investigation.
    region_ids = {r["region_id"] for r in current["rankings"]}
    if any(r["id"] not in region_ids for r in case["photos"][-1].get("regions", [])):
        blockers.append("The selected region has not been classified.")
    candidates = []
    for entry in votes.values():
        observations = entry["observations"]
        entry["supporting_photo_ids"] = sorted({o["photo_id"] for o in observations if o["rank"] == 1})
        entry["top5_photo_ids"] = sorted({o["photo_id"] for o in observations})
        entry["rank_sum"] = sum(
            min(o["rank"] for o in observations if o["photo_id"] == p) for p in entry["top5_photo_ids"]
        )
        candidates.append(entry)
    candidates.sort(
        key=lambda c: (
            -len(c["supporting_photo_ids"]),
            -len(c["top5_photo_ids"]),
            c["rank_sum"],
            c["class_id"],
        )
    )
    messages = {
        "no_ranking": "No classifier ranking is available yet.",
        "single_photo": "One photo has classifier evidence; agreement across photographs is untested.",
        "agreement": f"The leading class agrees across {len(ranked_views)} photographs. This does not verify breed identity.",
        "disagreement": "The leading class changes across recorded views. The assessment remains inconclusive.",
    }
    return dict(
        version=2,
        relation=relation,
        summary=messages[relation],
        views=views,
        ranked_photo_count=len(ranked_views),
        candidates=candidates[:5],
        blockers=blockers,
        report_eligible_ids=eligible if not blockers else [],
        policy_note="Score ≥ 0.5 and margin ≥ 0.15 are conservative, uncalibrated reporting heuristics. They do not detect dogs.",
        aggregation="Order by distinct-photo leading votes, then top-five appearances, then summed best ranks. Never average raw scores. Crops share their parent photo's vote.",
    )


def request_reasons(case):
    if len(case["photos"]) >= MAX_PHOTOS or case.get("followup_unavailable"):
        return []
    current = case["photos"][-1]["id"]
    events = [e for e in successful(case) if e["photo_id"] == current]
    inspection = next((e for e in events if e["tool"] == "inspect_image"), None)
    if not inspection:
        return []
    reasons = list(inspection["output"]["quality_flags"])
    ranks = [e for e in events if e["tool"] in RANK_TOOLS]
    if any(weak(e["output"]) for e in ranks):
        reasons.append("ambiguous_scores")
    if compare(case)["relation"] == "disagreement":
        reasons.append("conflicting_views")
    return reasons + ["insufficient_evidence"]


def build_report(case, outcome="inconclusive", selected_result_id=None, completed_by="agent"):
    from .config import LIMITATIONS

    comparison = compare(case)
    if outcome == "visual_matches" and selected_result_id not in comparison["report_eligible_ids"]:
        raise ValueError(
            "A visual report requires an eligible current result and no unresolved disagreement."
        )
    if outcome == "inconclusive" and selected_result_id is not None:
        raise ValueError("An inconclusive report must have selected_result_id=null.")
    ids = [e["id"] for e in successful(case) if e["tool"] in RANK_TOOLS | {"inspect_image"}]
    return dict(
        version=2,
        outcome=outcome,
        selected_result_id=selected_result_id,
        completed_by=completed_by,
        evidence_ids=ids,
        candidates=comparison["candidates"] if outcome == "visual_matches" else [],
        comparison=comparison,
        change=comparison["summary"],
        limitations=LIMITATIONS,
        quality_flags=comparison["views"][-1]["quality_flags"],
        uncertainty="Breed identity and dog presence remain unverified by independent evidence.",
    )
