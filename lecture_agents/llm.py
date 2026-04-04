from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from .config import PipelineConfig
from .json_utils import extract_json_object


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def chat_text_json(cfg: PipelineConfig, system: str, user: str) -> dict[str, Any]:
    text = chat_text(cfg, system, user)
    return extract_json_object(text)


def chat_text(cfg: PipelineConfig, system: str, user: str) -> str:
    if cfg.llm_provider == "google":
        return _google_text(cfg, system, user)
    return _openai_text(cfg, system, user)


def chat_vision_json(
    cfg: PipelineConfig,
    system: str,
    user: str,
    image_path: Path,
) -> dict[str, Any]:
    text = chat_vision(cfg, system, user, image_path)
    return extract_json_object(text)


def chat_vision(
    cfg: PipelineConfig,
    system: str,
    user: str,
    image_path: Path,
) -> str:
    if cfg.llm_provider == "google":
        return _google_vision(cfg, system, user, image_path)
    return _openai_vision(cfg, system, user, image_path)


def _openai_text(cfg: PipelineConfig, system: str, user: str) -> str:
    _require(bool(os.environ.get("OPENAI_API_KEY")), "OPENAI_API_KEY is required for OpenAI.")
    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    return (r.choices[0].message.content or "").strip()


def _openai_vision(cfg: PipelineConfig, system: str, user: str, image_path: Path) -> str:
    _require(bool(os.environ.get("OPENAI_API_KEY")), "OPENAI_API_KEY is required for OpenAI.")
    from openai import OpenAI

    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    client = OpenAI()
    r = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{data}"},
                    },
                ],
            },
        ],
        temperature=0.3,
    )
    return (r.choices[0].message.content or "").strip()


def _google_text(cfg: PipelineConfig, system: str, user: str) -> str:
    _require(bool(os.environ.get("GOOGLE_API_KEY")), "GOOGLE_API_KEY is required for Google.")
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(cfg.google_model, system_instruction=system)
    r = model.generate_content(user)
    return _google_response_text(r)


def _google_vision(cfg: PipelineConfig, system: str, user: str, image_path: Path) -> str:
    _require(bool(os.environ.get("GOOGLE_API_KEY")), "GOOGLE_API_KEY is required for Google.")
    import google.generativeai as genai
    from PIL import Image

    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(cfg.google_model, system_instruction=system)
    img = Image.open(image_path)
    r = model.generate_content([user, img])
    return _google_response_text(r)


def _google_response_text(r: Any) -> str:
    try:
        t = getattr(r, "text", None)
        if t:
            return str(t).strip()
    except Exception:
        pass
    parts: list[str] = []
    for cand in getattr(r, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for p in getattr(content, "parts", []) or []:
            if getattr(p, "text", None):
                parts.append(p.text)
    return "\n".join(parts).strip()
