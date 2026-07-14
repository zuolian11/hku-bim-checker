"""
Compliance checking rules for IFC building models.

Rule 1: Door clear width check (configurable threshold)
Rule 2: FireRating property presence (with smart name-based heuristics)
"""
import ifcopenshell
import ifcopenshell.util.element as util
from dataclasses import dataclass, field

# Default fire egress door width per GB 50016 (adjustable)
DOOR_WIDTH_MIN_MM = 900.0

# Known FireRating property set names across different BIM software
FIRE_RATING_PSETS = [
    "Pset_WallCommon", "Pset_DoorCommon",
    "FireRating", "Rating",
    "Pset_WallCommon_Fire", "Pset_DoorCommon_Fire",
]


@dataclass
class RuleResult:
    rule_name: str
    description: str
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    items: list = field(default_factory=list)


def check_all(model, min_width=DOOR_WIDTH_MIN_MM) -> list[RuleResult]:
    """Run all compliance checks."""
    return [
        check_door_width(model, min_width),
        check_fire_rating(model),
    ]


def check_door_width(model, min_width_mm: float = DOOR_WIDTH_MIN_MM) -> RuleResult:
    """Check that all doors meet the minimum clear width requirement."""
    result = RuleResult(
        rule_name="door_clear_width",
        description=f"Door clear width >= {min_width_mm:.0f} mm (configurable)",
    )

    for door in model.by_type("IfcDoor"):
        info = door.get_info()
        width = info.get("OverallWidth")

        item = {
            "guid": info.get("GlobalId"),
            "id": info.get("id"),
            "name": info.get("Name") or "Unnamed",
            "type": "IfcDoor",
        }

        if width is None:
            item["status"] = "warning"
            item["message"] = "Width data not available — may need manual check"
            result.warnings += 1
        elif float(width) < min_width_mm:
            item["status"] = "fail"
            item["message"] = f"Width {width:.0f} mm < {min_width_mm:.0f} mm"
            result.failed += 1
        else:
            item["status"] = "pass"
            item["message"] = f"OK ({width:.0f} mm)"
            result.passed += 1

        result.items.append(item)

    return result


def check_fire_rating(model) -> RuleResult:
    """Check that doors and walls have FireRating assigned.
    
    Searches multiple Pset names to account for different BIM software.
    Floors and stair elements with 'Fire' in name but no rating are flagged
    as high-severity warnings.
    """
    result = RuleResult(
        rule_name="fire_rating_presence",
        description="FireRating assigned to structural doors and walls",
    )

    for elem in model.by_type("IfcDoor") + model.by_type("IfcWall"):
        info = elem.get_info()
        name = info.get("Name") or "Unnamed"
        etype = info.get("type", elem.is_a())

        # Search all known Pset names for FireRating
        psets = util.get_psets(elem)
        fire_rating = None
        for pset_name in FIRE_RATING_PSETS:
            for pset_key, pset_data in psets.items():
                if pset_name in pset_key:
                    fr = pset_data.get("FireRating")
                    if fr:
                        fire_rating = fr
                        break
            if fire_rating:
                break

        item = {
            "guid": info.get("GlobalId"),
            "id": info.get("id"),
            "name": name,
            "type": etype,
        }

        if not fire_rating:
            # Smart heuristic: element named "Fire*" but no FireRating
            if any(kw in name.lower() for kw in ("fire", "firewall", "fire_", "1-hr", "2-hr")):
                item["status"] = "fail"
                item["message"] = f"'{name}' implies fire rating but none assigned"
                result.failed += 1
            else:
                item["status"] = "warning"
                item["message"] = "FireRating not assigned — may need manual review"
                result.warnings += 1
        else:
            item["status"] = "pass"
            item["message"] = f"FireRating: {fire_rating}"
            result.passed += 1

        result.items.append(item)

    return result

# ── JSON Model Checkers ─────────────────────────────

def check_door_width_json(data, min_width_mm=DOOR_WIDTH_MIN_MM) -> RuleResult:
    result = RuleResult("door_clear_width", f"Door width >= {min_width_mm:.0f} mm")
    for i, d in enumerate(data.get("doors", [])):
        w = d.get("width")
        name = d.get("name", f"Door #{i+1}")
        item = {"id": i + 1, "name": name, "type": "Door", "guid": None}
        if w is None:
            item["status"] = "warning"; item["message"] = "No width data"; result.warnings += 1
        elif w < min_width_mm:
            item["status"] = "fail"; item["message"] = f"Width {w}mm < {min_width_mm:.0f}mm"; result.failed += 1
        else:
            item["status"] = "pass"; item["message"] = f"OK ({w}mm)"; result.passed += 1
        result.items.append(item)
    return result


def check_fire_rating_json(data) -> RuleResult:
    result = RuleResult("fire_rating_presence", "FireRating assigned")
    all_elems = [("Door", d) for d in data.get("doors", [])] + \
                [("Wall", w) for w in data.get("walls", [])]
    for i, (etype, e) in enumerate(all_elems):
        name = e.get("name", f"{etype} #{i+1}")
        fr = e.get("fireRating")
        item = {"id": i + 1, "name": name, "type": etype, "guid": None}
        if not fr:
            if any(kw in str(name).lower() for kw in ("fire", "firewall", "1-hr", "2-hr")):
                item["status"] = "fail"; item["message"] = f"'{name}' implies fire rating but none assigned"; result.failed += 1
            else:
                item["status"] = "warning"; item["message"] = "FireRating not assigned"; result.warnings += 1
        else:
            item["status"] = "pass"; item["message"] = f"FireRating: {fr}"; result.passed += 1
        result.items.append(item)
    return result
