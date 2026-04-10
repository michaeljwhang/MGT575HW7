#!/usr/bin/env python3
"""Entrypoint: PDF → style.json + project artifacts → per-slide audio → one MP4."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from lecture_agents.arc_agent import run_arc_agent
from lecture_agents.config import PipelineConfig
from lecture_agents.narration_agent import run_narrations
from lecture_agents.pdf_rasterize import rasterize_pdf
from lecture_agents.premise_agent import run_premise_agent
from lecture_agents.slide_description_agent import run_slide_descriptions
from lecture_agents.style_agent import build_style_json
from lecture_agents.tts import synthesize_slide_mp3
from lecture_agents.video_assembly import assemble_lecture_video


def _bootstrap_env_from_dotenv_aliases() -> None:
    """Map common key names (e.g. React/Vite) and pick sensible provider defaults."""
    if not os.environ.get("GOOGLE_API_KEY"):
        for alt in (
            "GEMINI_API_KEY",
            "REACT_APP_GEMINI_API_KEY",
            "VITE_GEMINI_API_KEY",
            "GOOGLE_GENERATIVE_AI_API_KEY",
        ):
            v = os.environ.get(alt)
            if v:
                os.environ["GOOGLE_API_KEY"] = v
                break
    has_openai = bool((os.environ.get("OPENAI_API_KEY") or "").strip())
    has_google = bool((os.environ.get("GOOGLE_API_KEY") or "").strip())
    if not has_openai and has_google:
        os.environ.setdefault("PIPELINE_LLM_PROVIDER", "google")
        os.environ.setdefault("PIPELINE_TTS_PROVIDER", "gemini")
    # If .env asked for OpenAI but no key, fall back when Google key exists.
    if (
        not (os.environ.get("OPENAI_API_KEY") or "").strip()
        and (os.environ.get("GOOGLE_API_KEY") or "").strip()
        and os.environ.get("PIPELINE_LLM_PROVIDER", "openai").lower() == "openai"
    ):
        os.environ["PIPELINE_LLM_PROVIDER"] = "google"
    if (
        not (os.environ.get("OPENAI_API_KEY") or "").strip()
        and (os.environ.get("GOOGLE_API_KEY") or "").strip()
        and os.environ.get("PIPELINE_TTS_PROVIDER", "openai").lower() == "openai"
    ):
        os.environ["PIPELINE_TTS_PROVIDER"] = "gemini"


def resolve_pipeline_config(repo: Path) -> PipelineConfig:
    """Apply effective provider when .env has empty strings or only one key kind."""
    cfg = PipelineConfig.from_env(repo)
    oa = (os.environ.get("OPENAI_API_KEY") or "").strip()
    gg = (os.environ.get("GOOGLE_API_KEY") or "").strip()
    el = (os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if cfg.llm_provider == "openai" and not oa and gg:
        cfg = replace(cfg, llm_provider="google")
    if cfg.llm_provider == "google" and not gg and oa:
        cfg = replace(cfg, llm_provider="openai")
    if cfg.tts_provider == "openai" and not oa:
        if gg:
            cfg = replace(cfg, tts_provider="gemini")
    if cfg.tts_provider == "elevenlabs" and not el:
        if gg:
            cfg = replace(cfg, tts_provider="gemini")
        elif oa:
            cfg = replace(cfg, tts_provider="openai")
    return cfg


def _prepend_common_binary_dirs() -> None:
    """Help GUI-launched Python find Homebrew ffmpeg on macOS."""
    extra = ["/opt/homebrew/bin", "/usr/local/bin"]
    current = os.environ.get("PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    for d in reversed(extra):
        if d not in parts:
            parts.insert(0, d)
    os.environ["PATH"] = os.pathsep.join(parts)


def _ensure_ffmpeg() -> None:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise RuntimeError(
            "ffmpeg is required on PATH for video assembly (and for pydub MP3 merges). "
            "Install ffmpeg and retry."
        ) from e


def _default_pdf(repo: Path) -> Path:
    p = repo / "Lecture_17_AI_screenplays.pdf"
    if p.is_file():
        return p
    alt = repo / "Lecture_17_AI_screenplays.pdf.pdf"
    if alt.is_file():
        return alt
    return p


def main() -> None:
    _repo = Path(__file__).resolve().parent
    load_dotenv(_repo / ".env")
    load_dotenv()  # also honor cwd-based .env if present
    _bootstrap_env_from_dotenv_aliases()
    _prepend_common_binary_dirs()
    parser = argparse.ArgumentParser(description="Lecture deck → narrated video pipeline")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Repository root (default: directory of this script)",
    )
    parser.add_argument("--pdf", type=Path, default=None, help="Path to slide PDF")
    parser.add_argument(
        "--transcript",
        type=Path,
        default=None,
        help="Lecture transcript file (default: LectureTranscript in repo root)",
    )
    parser.add_argument(
        "--skip-style",
        action="store_true",
        help="Do not regenerate style.json if it already exists",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="No API keys: rasterize PDF, write stub JSON, silent MP3s, assemble MP4 (sanity check).",
    )
    args = parser.parse_args()
    _ensure_ffmpeg()

    repo = args.repo_root.resolve()
    cfg = resolve_pipeline_config(repo)

    pdf = (args.pdf or _default_pdf(repo)).resolve()
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF not found: {pdf}. Place Lecture_17_AI_screenplays.pdf in the repo root."
        )

    if args.smoke_test:
        from lecture_agents.smoke_pipeline import run_smoke_pipeline

        style_path = repo / "style.json"
        if not style_path.is_file():
            raise FileNotFoundError(
                f"Missing {style_path}. Commit or create style.json before --smoke-test."
            )
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = repo / "projects" / f"project_{stamp}_smoke"
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"Smoke test project: {project_dir}")
        print("Rasterize → stub JSON → silent audio → video (no LLM/TTS APIs).")
        final_mp4 = run_smoke_pipeline(
            repo=repo, pdf=pdf, project_dir=project_dir, dpi=cfg.pdf_dpi
        )
        print(f"Done: {final_mp4}")
        return

    transcript = (args.transcript or (repo / "LectureTranscript")).resolve()
    if not transcript.is_file():
        raise FileNotFoundError(f"Transcript not found: {transcript}")

    style_path = repo / "style.json"
    if not (args.skip_style and style_path.is_file()):
        print("Building style.json from transcript…")
        build_style_json(cfg, transcript, style_path)
    else:
        print("Skipping style.json (exists and --skip-style).")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = repo / "projects" / f"project_{stamp}"
    slide_dir = project_dir / "slide_images"
    audio_dir = project_dir / "audio"
    slide_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    print(f"Project directory: {project_dir}")
    print("Rasterizing PDF…")
    slide_paths = rasterize_pdf(pdf, slide_dir, dpi=cfg.pdf_dpi)

    slide_desc_path = project_dir / "slide_description.json"
    print("Slide description agent…")
    run_slide_descriptions(cfg, slide_paths, slide_desc_path)

    premise_path = project_dir / "premise.json"
    print("Premise agent…")
    run_premise_agent(cfg, slide_desc_path, premise_path)

    arc_path = project_dir / "arc.json"
    print("Arc agent…")
    run_arc_agent(cfg, premise_path, slide_desc_path, arc_path)

    narr_path = project_dir / "slide_description_narration.json"
    print("Narration agent…")
    run_narrations(
        cfg,
        style_path,
        premise_path,
        arc_path,
        slide_desc_path,
        slide_paths,
        narr_path,
    )

    narr_doc = json.loads(narr_path.read_text(encoding="utf-8"))
    print(f"TTS ({cfg.tts_provider})…")
    for slide in narr_doc["slides"]:
        idx = int(slide["slide_index"])
        text = str(slide["narration"])
        out_mp3 = audio_dir / f"slide_{idx:03d}.mp3"
        synthesize_slide_mp3(cfg, text, out_mp3)
        print(f"  audio slide_{idx:03d}.mp3")

    audio_paths = [audio_dir / f"slide_{i:03d}.mp3" for i in range(1, len(slide_paths) + 1)]
    for p in audio_paths:
        if not p.is_file():
            raise FileNotFoundError(f"Missing {p}")

    base = pdf.name
    while base.lower().endswith(".pdf"):
        base = base[:-4]
    final_mp4 = project_dir / f"{base}.mp4"
    print("Assembling video with ffmpeg…")
    assemble_lecture_video(slide_paths, audio_paths, final_mp4)
    print(f"Done: {final_mp4}")


if __name__ == "__main__":
    main()
