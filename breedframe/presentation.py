"""Reader-facing summaries of recorded rankings; no changes to reporting policy."""

from .evidence import compare

SCORE_NOTE = (
    "Model scores describe visual matches among 120 breeds. "
    "They are not calibrated probabilities of breed identity or ancestry percentages."
)


def describe_assessment(case, comparison=None):
    comparison = comparison if comparison is not None else compare(case)
    view = comparison["views"][-1]
    summary = dict(
        title="No breed match yet",
        detail="The current photo has no classification result. Earlier results, if any, are listed below.",
        source=None,
        candidates=[],
        context="",
        score_note=SCORE_NOTE,
    )
    if not view["rankings"]:
        return summary
    ranking = view["rankings"][-1]
    candidates = [
        dict(
            **candidate,
            display_label=candidate["label"].replace("_", " ").capitalize()
            + (" (label incomplete)" if candidate.get("unresolved_label") else ""),
            score_text=f"{candidate['score'] * 100:.1f}%",
        )
        for candidate in ranking["candidates"]
    ]
    top = candidates[0]
    tied = [c for c in candidates if c["score"] == top["score"]]
    title = (
        "Joint top visual matches: " + ", ".join(c["display_label"] for c in tied)
        if len(tied) > 1
        else f"Top visual match: {top['display_label']}"
    )
    source = f"{view['photo_id']} · {ranking['region_id'] or 'whole photo'} · event {ranking['event_id']}"
    context = {
        "single_photo": "This match is based on one photo. Another clear view may help compare the result.",
        "agreement": "The same breed leads across the classified photos.",
        "disagreement": "Different views suggest different breeds. This is the latest result; compare the views below.",
    }.get(comparison["relation"], "")
    if ranking["weak_scores"]:
        context += " The scores are low or closely ranked, so treat this match as tentative."
    summary.update(
        title=title,
        detail=f"Model score: {top['score_text']}",
        source=source,
        candidates=candidates,
        context=context,
    )
    return summary
