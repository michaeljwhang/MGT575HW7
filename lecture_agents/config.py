from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PipelineConfig:
    repo_root: Path
    llm_provider: str  # "openai" | "google"
    openai_model: str
    google_model: str
    tts_provider: str  # "openai" | "elevenlabs" | "gemini"
    openai_tts_model: str
    openai_tts_voice: str
    elevenlabs_voice_id: str | None
    gemini_tts_model: str
    gemini_tts_voice: str
    pdf_dpi: int

    @classmethod
    def from_env(cls, repo_root: Path) -> PipelineConfig:
        return cls(
            repo_root=repo_root.resolve(),
            llm_provider=os.environ.get("PIPELINE_LLM_PROVIDER", "openai").lower(),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            google_model=os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash"),
            tts_provider=os.environ.get("PIPELINE_TTS_PROVIDER", "openai").lower(),
            openai_tts_model=os.environ.get("OPENAI_TTS_MODEL", "tts-1"),
            openai_tts_voice=os.environ.get("OPENAI_TTS_VOICE", "alloy"),
            elevenlabs_voice_id=os.environ.get("ELEVENLABS_VOICE_ID"),
            gemini_tts_model=os.environ.get(
                "GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"
            ),
            gemini_tts_voice=os.environ.get("GEMINI_TTS_VOICE", "Kore"),
            pdf_dpi=int(os.environ.get("PDF_RASTER_DPI", "150")),
        )
