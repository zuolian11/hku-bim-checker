"""
Compliance checking rules for IFC building models.

Two rules:
  1. Door clear width >= 900 mm (fire egress, per GB 50016 / NFPA 101)
  2. FireRating property present on all doors and walls (data completeness)
"""
import ifcopenshell
import ifcopenshell.util.element as util
from dataclasses import dataclass, field


@dataclass
class RuleResult:
    rule_name: str
    description: str
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    items: list = field(default_factory=list)


def check_all(model) -> list[RuleResult]:
    """Run all compliance checks on an IFC model."""
    return [
        check_door_width(model),
        check_fire_rating(model),
    ]


def check_door_width(model, min_width_mm: float = 900.0) -> RuleResult:
    """Check that all doors have sufficient clear width for fire egress."""
    result = RuleResult(
        rule_name="door_clear_width",
        description=f"Door clear width >= {min_width_mm:.0f} mm",
    )

    for door in model.by_type("IfcDoor"):
        info = door.get_info()
        item = {
            "guid": info.get("GlobalId"),
            "id": info.get("id"),
            "name": info.get("Name") or "Unnamed",
            "type": "IfcDoor",
        }

        width = info.get("OverallWidth")
        if width is None:
            item["status"] = "warning"
            item["message"] = "Width data not available"
            result.warnings += 1
        elif width < min_width_mm:
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
    """Check that all doors and walls have FireRating property set."""
    result = RuleResult(
        rule_name="fire_rating_completeness",
        description="FireRating property present on all doors and walls",
    )

    for elem in model.by_type("IfcDoor") + model.by_type("IfcWall"):
        info = elem.get_info()
        psets = util.get_psets(elem)
        fire_rating = (
            psets.get("Pset_WallCommon", {}).get("FireRating")
            or psets.get("Pset_DoorCommon", {}).get("FireRating")
        )

        item = {
            "guid": info.get("GlobalId"),
            "id": info.get("id"),
            "name": info.get("Name") or "Unnamed",
            "type": info.get("type", str(info.get("type", "Unknown"))),
        }

        if not fire_rating:
            item["status"] = "fail"
            item["message"] = "FireRating not assigned"
            result.failed += 1
        else:
            item["status"] = "pass"
            item["message"] = f"FireRating: {fire_rating}"
            result.passed += 1

        result.items.append(item)

    return result
