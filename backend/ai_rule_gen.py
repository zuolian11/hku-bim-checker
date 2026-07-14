"""
AI Rule Generator — Natural language → executable compliance rules.

Patterns: width, height, fire rating, count, existence
Units: mm, cm, m (auto-convert to mm)
"""
import re


def parse_regulation(text: str) -> list[dict]:
    """Parse a natural-language regulation into rule definitions."""
    tl = text.lower().strip()
    rules = []

    # ── Extract all numbers+units from text ──────────
    numbers = []
    for m in re.finditer(r"(\d+\.?\d*)\s*(mm|cm|m|毫米|厘米|米)?", tl):
        val = float(m.group(1))
        unit = m.group(2) or "mm"
        if unit in ("cm", "厘米"): val *= 10
        elif unit in ("m", "米"): val *= 1000
        numbers.append(val)

    # ── Target detection ─────────────────────────────
    is_door = bool(re.search(r"(door|门|入口|出口)", tl))
    is_wall = bool(re.search(r"(wall|墙|墙体)", tl))
    is_egress = bool(re.search(r"(egress|exit|escape|fire.exit|疏散|安全出口|逃生)", tl))
    is_window = bool(re.search(r"(window|窗)", tl))

    # ── Condition detection ──────────────────────────
    is_at_least  = bool(re.search(r"(≥|>=|at least|不小于|不得小于|minimum|min|不小于|至少|不低于|起码)", tl))
    is_at_most   = bool(re.search(r"(≤|<=|at most|不大于|不超过|maximum|max|不大于|最多|不超过)", tl))
    is_required  = bool(re.search(r"(required|must have|shall have|需要|必须有|必须设置|要求|必须)", tl))
    is_not_found = bool(re.search(r"(no.*(found|assigned)|缺失|没有|缺|none)", tl))
    is_fire      = bool(re.search(r"(fire.?rating|fire.?resistance|fireproof|防火等级|耐火|防火)", tl))

    # ── Target type ──────────────────────────────────
    target_types = []
    if is_door: target_types.append("IfcDoor")
    if is_wall: target_types.append("IfcWall")
    if is_window: target_types.append("IfcWindow")
    if not target_types: target_types = ["IfcDoor", "IfcWall"]

    target_label = "+".join(t.replace("Ifc", "") for t in target_types)
    scope = "egress" if is_egress else "all"

    # ── Rule 1: Width ────────────────────────────────
    if is_door and numbers:
        n = numbers[0]
        rules.append({
            "rule_name": f"custom:{text[:40]}",
            "target": "IfcDoor",
            "property": "OverallWidth",
            "condition": "gte",
            "value": n,
            "unit": "mm",
            "scope": scope,
        })

    # ── Rule 2: FireRating ───────────────────────────
    if is_fire and (is_door or is_wall):
        if is_required or is_not_found or "firerating" in tl.replace(" ", ""):
            rules.append({
                "rule_name": f"custom:{text[:40]}",
                "target": "+".join(target_types),
                "property": "FireRating",
                "condition": "exists",
                "value": None,
                "scope": scope,
            })

    # ── Rule 3: Height ───────────────────────────────
    is_height = bool(re.search(r"(height|tall|高|高度)", tl))
    if is_height and (is_door or is_window) and numbers:
        rules.append({
            "rule_name": f"custom:{text[:40]}",
            "target": "+".join(target_types),
            "property": "OverallHeight",
            "condition": "gte",
            "value": numbers[0],
            "unit": "mm",
            "scope": scope,
        })

    # ── Rule 4: Count ────────────────────────────────
    count_match = re.search(r"(at least|minimum|至少|最少)\s*(\d+)\s*(door|门|exit|出口|window|窗)", tl)
    if count_match:
        rules.append({
            "rule_name": f"custom:{text[:40]}",
            "target": "+".join(target_types),
            "property": "count",
            "condition": "gte",
            "value": int(count_match.group(2)),
            "unit": "count",
            "scope": scope,
        })

    # ── Fallback ─────────────────────────────────────
    if not rules:
        hint = "Try: 'doors at least 900mm' or 'walls need FireRating'"

    return rules
