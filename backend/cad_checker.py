"""
CAD (DXF) file compliance checking.

Parses DXF using ezdxf, extracts line/polyline entities,
and checks for doorway compliance patterns.
"""
import ezdxf

from checker import RuleResult, DOOR_WIDTH_MIN_MM


def check_dxf_width(filepath: str, min_width_mm=DOOR_WIDTH_MIN_MM) -> RuleResult:
    """Check DXF for door-like rectangles and verify widths."""
    result = RuleResult(
        "cad_door_width",
        f"Detect doors in CAD and check width >= {min_width_mm:.0f} mm"
    )
    try:
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()
    except Exception as e:
        result.warnings += 1
        result.items.append({
            "id": 0, "name": "DXF Parse Error", "type": "CAD",
            "status": "warning", "message": str(e)
        })
        return result

    rect_count = 0
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and len(e) == 4:
            pts = list(e)
            widths = [
                abs(pts[0][0] - pts[1][0]),
                abs(pts[1][0] - pts[2][0]),
            ]
            door_w = min(widths) if widths else 0
            rect_count += 1
            item = {
                "id": rect_count, "name": f"Rect #{rect_count}",
                "type": "CAD", "guid": None,
            }
            if door_w < min_width_mm:
                item["status"] = "fail"
                item["message"] = f"Potential door width {door_w:.0f}mm < {min_width_mm:.0f}mm"
                result.failed += 1
            else:
                item["status"] = "pass"
                item["message"] = f"OK ({door_w:.0f}mm)"
                result.passed += 1
            result.items.append(item)

    if rect_count == 0:
        result.warnings += 1
        result.items.append({
            "id": 0, "name": "CAD Model", "type": "CAD",
            "status": "warning",
            "message": "No door-like rectangles found. DXF may use blocks rather than polylines."
        })

    return result


def check_dxf_fire_rating(filepath: str) -> RuleResult:
    """DXF lacks FireRating metadata — flag all elements for manual review."""
    result = RuleResult(
        "cad_fire_rating",
        "FireRating not available in CAD format — requires manual review"
    )
    result.warnings += 1
    result.items.append({
        "id": 0, "name": "CAD Model", "type": "CAD", "status": "warning",
        "message": "CAD/DXF format does not store FireRating metadata. Use IFC for automated checking."
    })
    return result
