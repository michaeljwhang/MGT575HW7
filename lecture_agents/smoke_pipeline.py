"""Offline smoke run: rasterize PDF, stub JSON artifacts, silent audio, mux MP4."""

from __future__ import annotations

import json
from pathlib import Path

from .pdf_rasterize import rasterize_pdf
from .silent_audio import write_silent_mp3
from .video_assembly import assemble_lecture_video


def run_smoke_pipeline(
    *,
    repo: Path,
    pdf: Path,
    project_dir: Path,
    dpi: int,
    silent_seconds: float = 1.2,
) -> Path:
    slide_dir = project_dir / "slide_images"
    audio_dir = project_dir / "audio"
    slide_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    slide_paths = rasterize_pdf(pdf, slide_dir, dpi=dpi)
    n = len(slide_paths)

    slides_desc = [
        {
            "slide_index": i + 1,
            "description": f"Smoke-test placeholder for slide {i + 1} of {n}.",
        }
        for i in range(n)
    ]
    slide_desc_path = project_dir / "slide_description.json"
    slide_desc_path.write_text(
        json.dumps(
            {"slides": slides_desc, "metadata": {"slide_count": n, "smoke_test": True}},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    premise = {
        "thesis": "Smoke test premise (no LLM).",
        "scope": "Validates rasterization, JSON IO, ffmpeg audio and video.",
        "learning_objectives": ["Verify pipeline wiring"],
        "audience": "Developer",
        "key_themes": ["smoke"],
        "constraints_for_narration": "N/A for smoke test",
    }
    (project_dir / "premise.json").write_text(
        json.dumps(premise, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    arc = {
        "flow_summary": "Linear progression through slides.",
        "phases": [
            {
                "name": "All slides",
                "slide_range_hint": f"1–{n}",
                "goal": "End-to-end assembly check",
                "beats": ["rasterize", "silent audio", "mux"],
            }
        ],
        "idea_progression": [f"Slide {i}" for i in range(1, n + 1)],
        "transitions_guidance": "None",
        "pacing_notes": "Fixed-duration silent clips",
    }
    (project_dir / "arc.json").write_text(
        json.dumps(arc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    narr_slides = [
        {
            "slide_index": s["slide_index"],
            "description": s["description"],
            "narration": f"Slide {s['slide_index']} narration placeholder for smoke test.",
        }
        for s in slides_desc
    ]
    (project_dir / "slide_description_narration.json").write_text(
        json.dumps(
            {"slides": narr_slides, "metadata": {"slide_count": n, "smoke_test": True}},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    for i in range(1, n + 1):
        write_silent_mp3(audio_dir / f"slide_{i:03d}.mp3", duration_sec=silent_seconds)

    audio_paths = [audio_dir / f"slide_{i:03d}.mp3" for i in range(1, n + 1)]
    base = pdf.name
    while base.lower().endswith(".pdf"):
        base = base[:-4]
    final_mp4 = project_dir / f"{base}.mp4"
    assemble_lecture_video(slide_paths, audio_paths, final_mp4)
    return final_mp4
