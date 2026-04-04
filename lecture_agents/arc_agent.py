from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .llm import chat_text_json


ARC_SYSTEM = """You design a lecture arc consistent with the premise and slide descriptions.
Return ONLY valid JSON:
{
  "flow_summary": "string — one paragraph",
  "phases": [
    {"name": "string", "slide_range_hint": "string", "goal": "string", "beats": ["string"]}
  ],
  "idea_progression": ["string — how concepts build slide to slide"],
  "transitions_guidance": "string — how narrators should connect slides",
  "pacing_notes": "string"
}
Use the premise as the backbone; slide descriptions for ordering and detail."""


def run_arc_agent(
    cfg: PipelineConfig,
    premise_path: Path,
    slide_description_path: Path,
    out_path: Path,
) -> dict:
    premise = json.loads(premise_path.read_text(encoding="utf-8"))
    slides = json.loads(slide_description_path.read_text(encoding="utf-8"))
    user = (
        "premise.json:\n"
        + json.dumps(premise, ensure_ascii=False)
        + "\n\nslide_description.json:\n"
        + json.dumps(slides, ensure_ascii=False)
    )
    data = chat_text_json(cfg, ARC_SYSTEM, user)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
