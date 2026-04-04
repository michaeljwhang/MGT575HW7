from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .llm import chat_vision_json


NARRATION_SYSTEM = """You write spoken lecture narration for a single slide.
Return ONLY valid JSON: {"slide_index": <int>, "narration": "<string>"}.

Rules:
- Match the instructor voice described in style.json (tone, fillers sparingly but authentically, framing).
- Stay faithful to the slide image and the slide's description; do not contradict premise.json or arc.json.
- Spoken English; short paragraphs ok; no stage directions like *laughs*.
- Slide 1 ONLY: the speaker introduces themselves by first-person as the course instructor and gives a short summary of the lecture topic (in addition to covering the title slide content).
- Other slides: no lengthy re-introduction; focus on that slide.

Keep each narration roughly suitable for TTS (avoid exotic Unicode)."""


def run_narrations(
    cfg: PipelineConfig,
    style_path: Path,
    premise_path: Path,
    arc_path: Path,
    slide_description_path: Path,
    slide_paths: list[Path],
    out_path: Path,
) -> dict:
    style = json.loads(style_path.read_text(encoding="utf-8"))
    premise = json.loads(premise_path.read_text(encoding="utf-8"))
    arc = json.loads(arc_path.read_text(encoding="utf-8"))
    slide_desc_doc = json.loads(slide_description_path.read_text(encoding="utf-8"))
    by_idx = {s["slide_index"]: s["description"] for s in slide_desc_doc["slides"]}

    combined_slides: list[dict] = []
    prior_narrations: list[str] = []

    for path in slide_paths:
        idx = len(combined_slides) + 1
        desc = by_idx.get(idx)
        if not desc:
            raise KeyError(f"Missing description for slide {idx}")

        prior_block = ""
        if prior_narrations:
            prior_block = (
                "Prior slide narrations (in order):\n"
                + "\n".join(f"Slide {i+1}: {t}" for i, t in enumerate(prior_narrations))
                + "\n\n"
            )

        context = {
            "style": style,
            "premise": premise,
            "arc": arc,
            "current_slide_index": idx,
            "current_slide_description": desc,
        }
        user = (
            f"{prior_block}"
            "Context JSON (style, premise, arc, current slide):\n"
            + json.dumps(context, ensure_ascii=False)
            + "\n\nWrite narration for this slide only. Image attached."
        )
        raw = chat_vision_json(cfg, NARRATION_SYSTEM, user, path)
        narr = str(raw.get("narration", "")).strip()
        if not narr:
            raise RuntimeError(f"Empty narration for slide {idx}")
        combined_slides.append(
            {"slide_index": idx, "description": desc, "narration": narr}
        )
        prior_narrations.append(narr)

    payload = {"slides": combined_slides, "metadata": {"slide_count": len(combined_slides)}}
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
