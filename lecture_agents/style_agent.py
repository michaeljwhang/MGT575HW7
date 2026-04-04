from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .llm import chat_text_json


STYLE_SYSTEM = """You are an expert in linguistics and instructional communication.
Return ONLY valid JSON (no markdown) matching this shape:
{
  "tone": "string — e.g. conversational, energetic, informal-academic",
  "pacing": "string — how fast ideas move, use of digressions",
  "fillers_and_verbal_habits": ["array of recurring phrases like um, you know, right?"],
  "framing_patterns": "string — how the speaker sets up examples, questions, and punchlines",
  "audience_address": "string — how they talk to students (direct address, chat metaphors, etc.)",
  "humor_and_asides": "string",
  "vocabulary_register": "string — casual vs technical balance",
  "rhythm_and_emphasis": "string — short punchy lines vs longer explanations",
  "narration_guidance": "string — concise instructions another writer should follow to imitate this voice"
}
Base every field on evidence from the transcript."""


def build_style_json(cfg: PipelineConfig, transcript_path: Path, out_path: Path) -> dict:
    text = transcript_path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise FileNotFoundError(
            f"Transcript is empty: {transcript_path}. Save your lecture transcript before running."
        )
    max_chars = 240_000
    if len(text) > max_chars:
        head = text[: max_chars // 2]
        tail = text[-max_chars // 2 :]
        text = head + "\n\n[... middle omitted for length ...]\n\n" + tail
    user = (
        "Analyze this instructor transcript and fill the JSON schema.\n\n"
        f"--- TRANSCRIPT ---\n{text}\n--- END ---"
    )
    data = chat_text_json(cfg, STYLE_SYSTEM, user)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
