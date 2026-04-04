from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .llm import chat_text_json


PREMISE_SYSTEM = """You extract the lecture premise from slide descriptions.
Return ONLY valid JSON with these keys:
{
  "thesis": "string",
  "scope": "string — what is in / out of scope",
  "learning_objectives": ["string", "..."],
  "audience": "string",
  "key_themes": ["string"],
  "constraints_for_narration": "string — tone and accuracy constraints"
}
Ground claims in the slide descriptions only."""


def run_premise_agent(
    cfg: PipelineConfig,
    slide_description_path: Path,
    out_path: Path,
) -> dict:
    sd = json.loads(slide_description_path.read_text(encoding="utf-8"))
    user = "Slide descriptions JSON:\n" + json.dumps(sd, ensure_ascii=False)
    data = chat_text_json(cfg, PREMISE_SYSTEM, user)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
