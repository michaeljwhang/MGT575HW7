from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import requests

from .config import PipelineConfig

# OpenAI speech API input limit (characters)
_OPENAI_TTS_MAX = 4096


def _split_for_tts(text: str, max_len: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for s in sentences:
        if not s:
            continue
        if len(s) > max_len:
            for i in range(0, len(s), max_len):
                chunk = s[i : i + max_len]
                if size + len(chunk) + 1 > max_len and buf:
                    parts.append(" ".join(buf))
                    buf = []
                    size = 0
                buf.append(chunk)
                size += len(chunk) + 1
            continue
        if size + len(s) + 1 > max_len and buf:
            parts.append(" ".join(buf))
            buf = []
            size = 0
        buf.append(s)
        size += len(s) + 1
    if buf:
        parts.append(" ".join(buf))
    return [p for p in parts if p.strip()]


def synthesize_slide_mp3(cfg: PipelineConfig, text: str, out_mp3: Path) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    if cfg.tts_provider == "elevenlabs":
        _elevenlabs_to_mp3(cfg, text, out_mp3)
        return
    _openai_tts_to_mp3(cfg, text, out_mp3)


def _openai_tts_to_mp3(cfg: PipelineConfig, text: str, out_mp3: Path) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI TTS.")
    from openai import OpenAI
    from pydub import AudioSegment

    chunks = _split_for_tts(text, _OPENAI_TTS_MAX)
    client = OpenAI()
    if len(chunks) == 1:
        speech = client.audio.speech.create(
            model=cfg.openai_tts_model,
            voice=cfg.openai_tts_voice,
            input=chunks[0],
        )
        speech.stream_to_file(out_mp3.as_posix())
        return

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        segs: list[AudioSegment] = []
        for i, ch in enumerate(chunks):
            part = td_path / f"part_{i:03d}.mp3"
            speech = client.audio.speech.create(
                model=cfg.openai_tts_model,
                voice=cfg.openai_tts_voice,
                input=ch,
            )
            speech.stream_to_file(part.as_posix())
            segs.append(AudioSegment.from_mp3(part.as_posix()))
        merged = sum(segs[1:], segs[0])
        merged.export(out_mp3.as_posix(), format="mp3")


def _elevenlabs_to_mp3(cfg: PipelineConfig, text: str, out_mp3: Path) -> None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is required for ElevenLabs TTS.")
    vid = cfg.elevenlabs_voice_id or os.environ.get("ELEVENLABS_VOICE_ID")
    if not vid:
        raise RuntimeError("Set ELEVENLABS_VOICE_ID for ElevenLabs TTS.")

    # ElevenLabs also benefits from chunking for very long inputs
    chunks = _split_for_tts(text, 2500)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
    headers = {"xi-api-key": key, "Content-Type": "application/json"}
    if len(chunks) == 1:
        r = requests.post(
            url,
            headers=headers,
            json={
                "text": chunks[0],
                "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
            },
            timeout=120,
        )
        r.raise_for_status()
        out_mp3.write_bytes(r.content)
        return

    from pydub import AudioSegment

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        segs: list[AudioSegment] = []
        for i, ch in enumerate(chunks):
            part = td_path / f"part_{i:03d}.mp3"
            r = requests.post(
                url,
                headers=headers,
                json={
                    "text": ch,
                    "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
                },
                timeout=120,
            )
            r.raise_for_status()
            part.write_bytes(r.content)
            segs.append(AudioSegment.from_mp3(part.as_posix()))
        merged = sum(segs[1:], segs[0])
        merged.export(out_mp3.as_posix(), format="mp3")
