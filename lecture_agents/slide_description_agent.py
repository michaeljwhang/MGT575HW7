from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .llm import chat_vision_json


SLIDE_DESC_SYSTEM = """You describe presentation slides for a narration pipeline.
Return ONLY valid JSON: {"slide_index": <int>, "description": "<string>"}.
The description should capture visible text, layout, diagrams, and the slide's purpose in the deck.
Do not invent content that is not reasonably visible on the slide."""


def run_slide_descriptions(
    cfg: PipelineConfig,
    slide_paths: list[Path],
    out_path: Path,
) -> dict:
    slides_out: list[dict] = []
    prior_summaries: list[str] = []

    for path in slide_paths:
        idx = len(slides_out) + 1
        prev_block = ""
        if prior_summaries:
            prev_block = (
                "Previous slide descriptions (in order):\n"
                + "\n".join(f"{i+1}. {s}" for i, s in enumerate(prior_summaries))
                + "\n\n"
            )
        user = (
            f"{prev_block}Describe slide {idx} (PNG attached). "
            "Stay consistent with how earlier slides were summarized."
        )
        raw = chat_vision_json(cfg, SLIDE_DESC_SYSTEM, user, path)
        desc = str(raw.get("description", "")).strip()
        if not desc:
            raise RuntimeError(f"Empty description for slide {idx}")
        slides_out.append({"slide_index": idx, "description": desc})
        prior_summaries.append(desc)

    payload = {
        "slides": slides_out,
        "metadata": {"slide_count": len(slides_out)},
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
