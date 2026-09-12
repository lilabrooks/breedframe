from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PhotoArgs(StrictModel):
    photo_id: str = Field(min_length=1, max_length=40)


class RegionArgs(PhotoArgs):
    region_id: str = Field(min_length=1, max_length=40)


class RegionSelection(StrictModel):
    photo_id: str
    left: float = Field(ge=0, lt=1)
    top: float = Field(ge=0, lt=1)
    right: float = Field(gt=0, le=1)
    bottom: float = Field(gt=0, le=1)


class RequestArgs(StrictModel):
    reason: Literal[
        "low_resolution",
        "exposure",
        "low_detail",
        "ambiguous_scores",
        "insufficient_evidence",
        "conflicting_views",
    ]
    view: Literal["well_lit_full_body", "sharp_face_and_body", "closer_full_body"]


class FinishArgs(StrictModel):
    outcome: Literal["visual_matches", "inconclusive"]
    selected_result_id: int | None


ARGUMENTS = {
    "inspect_image": PhotoArgs,
    "classify_breed": PhotoArgs,
    "classify_region": RegionArgs,
    "request_another_photo": RequestArgs,
    "finish_assessment": FinishArgs,
}
DESCRIPTIONS = {
    "inspect_image": "Measure image dimensions, brightness and pixel detail. Cannot detect a dog or describe anatomy.",
    "classify_breed": "Run the local 120-class ViT on the current photo. Returns top-five raw scores, not confidence.",
    "classify_region": "Classify an existing user-selected region; coordinates come from the user. It is not an independent photograph.",
    "request_another_photo": "Pause this case for a useful new view. Cite actual observation event IDs and a supported reason.",
    "finish_assessment": "Finish using the comparison of all recorded views. A visual report needs a report_eligible_id; otherwise conclude inconclusive with null.",
}
TOOLS = [
    {
        "type": "function",
        "function": {"name": name, "description": DESCRIPTIONS[name], "parameters": args.model_json_schema()},
    }
    for name, args in ARGUMENTS.items()
]


class InspectCall(StrictModel):
    tool: Literal["inspect_image"]
    arguments: PhotoArgs


class ClassifyCall(StrictModel):
    tool: Literal["classify_breed"]
    arguments: PhotoArgs


class RegionCall(StrictModel):
    tool: Literal["classify_region"]
    arguments: RegionArgs


class RequestCall(StrictModel):
    tool: Literal["request_another_photo"]
    arguments: RequestArgs


class FinishCall(StrictModel):
    tool: Literal["finish_assessment"]
    arguments: FinishArgs


class Decision(StrictModel):
    call: InspectCall | ClassifyCall | RegionCall | RequestCall | FinishCall
