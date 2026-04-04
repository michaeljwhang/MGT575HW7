from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def rasterize_pdf(pdf_path: Path, out_dir: Path, dpi: int = 150) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path.as_posix())
    paths: list[Path] = []
    try:
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=dpi)
            out = out_dir / f"slide_{i + 1:03d}.png"
            pix.save(out.as_posix())
            paths.append(out)
    finally:
        doc.close()
    return paths
