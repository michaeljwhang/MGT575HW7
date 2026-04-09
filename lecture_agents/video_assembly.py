from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    quiet = os.environ.get("PIPELINE_FFMPEG_VERBOSE", "").lower() not in ("1", "true", "yes")
    kwargs: dict = {"check": True, "cwd": cwd.as_posix() if cwd else None}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    subprocess.run(cmd, **kwargs)


def mux_still_with_audio(image: Path, audio: Path, out_mp4: Path) -> None:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        image.as_posix(),
        "-i",
        audio.as_posix(),
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        out_mp4.as_posix(),
    ]
    _run(cmd)


def assemble_lecture_video(
    slide_images: list[Path],
    audio_files: list[Path],
    final_mp4: Path,
) -> None:
    if len(slide_images) != len(audio_files):
        raise ValueError("slide_images and audio_files length mismatch")
    final_mp4 = final_mp4.resolve()
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        segment_names: list[str] = []
        for i, (img, aud) in enumerate(zip(slide_images, audio_files, strict=True)):
            name = f"seg_{i + 1:03d}.mp4"
            seg = td_path / name
            mux_still_with_audio(img, aud, seg)
            segment_names.append(name)

        list_path = td_path / "concat_list.txt"
        lines = "\n".join(f"file '{n}'" for n in segment_names) + "\n"
        list_path.write_text(lines, encoding="utf-8")
        # Re-encode here so timestamps stay monotonic (stream copy can warn on still-image segments).
        _run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path.as_posix(),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                final_mp4.as_posix(),
            ],
            cwd=td_path,
        )
