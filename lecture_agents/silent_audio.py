"""Generate silent MP3 clips with ffmpeg (no API keys; used for smoke tests)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def write_silent_mp3(out_path: Path, duration_sec: float = 1.5) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=mono:sample_rate=44100",
        "-t",
        str(duration_sec),
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        out_path.as_posix(),
    ]
    quiet = os.environ.get("PIPELINE_FFMPEG_VERBOSE", "").lower() not in ("1", "true", "yes")
    kwargs: dict = {"check": True}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    subprocess.run(cmd, **kwargs)
