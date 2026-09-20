from __future__ import annotations
import json, re

def parse_entity_catalog(text: str):
    if not isinstance(text, str) or not text.strip():
        return []
    t = text.strip()
    # fenced JSON / 앞뒤 설명을 최대한 흡수
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.I | re.S).strip()
    start = t.find('[')
    end = t.rfind(']')
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(t[start:end + 1])
    except Exception:
        return []
    return [x for x in data if isinstance(x, dict)] if isinstance(data, list) else []
