from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output, allowing ```json fences."""
    raw = text.strip()
    fence = re.match(r"^```(?:json)?\s*\n?", raw, re.IGNORECASE)
    if fence:
        raw = raw[fence.end() :]
        raw = re.sub(r"\n```\s*$", "", raw, flags=re.DOTALL)
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start : end + 1])
        raise
