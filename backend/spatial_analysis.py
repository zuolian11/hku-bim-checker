"""
Spatial analysis for IFC building models.
Identifies door types: egress, interior, exterior, stairwell.
"""

import ifcopenshell
import ifcopenshell.util.element as util


def analyze_spatial(model) -> dict:
    """Analyze building spatial structure and classify doors."""
    doors = model.by_type("IfcDoor")
    walls = model.by_type("IfcWall")
    spaces = model.by_type("IfcSpace")
    storeys = model.by_type("IfcBuildingStorey")

    # Classify doors by name heuristics and spatial context
    egress_keywords = ("exit", "entrance", "main", "fire_exit", "escape", "emergency",
                       "疏散", "入口", "安全出口", "逃生")
    stair_keywords = ("stair", "楼梯")
    interior_keywords = ("interior", "internal", "room", "office", "bed", "bath", "single",
                         "室内", "卧室", "办公")

    door_classifications = []
    for d in doors:
        info = d.get_info()
        name = (info.get("Name") or "").lower()
        width = info.get("OverallWidth")
        eid = info.get("id")

        # Classification logic
        cls = "interior"
        for kw in egress_keywords:
            if kw in name:
                cls = "egress"; break
        if cls != "egress":
            for kw in stair_keywords:
                if kw in name:
                    cls = "stairwell"; break
        if cls == "interior" and width and width >= 1200:
            cls = "egress"  # Wide doors likely egress

        # Check if door is in an external wall
        psets = util.get_psets(d)
        is_external = psets.get("Pset_DoorCommon", {}).get("IsExternal", False)

        door_classifications.append({
            "id": eid,
            "name": info.get("Name") or "Unnamed",
            "guid": info.get("GlobalId"),
            "width_mm": round(width, 1) if width else None,
            "classification": cls,
            "is_external": bool(is_external),
        })

    # Also get wall classifications (for FireRating context)
    wall_info = []
    for w in walls[:10]:
        info = w.get_info()
        wall_info.append({
            "id": info.get("id"),
            "name": info.get("Name") or "Unnamed",
        })

    return {
        "summary": {
            "total_doors": len(doors),
            "total_walls": len(walls),
            "total_spaces": len(spaces),
            "total_storeys": len(storeys),
            "egress_doors": sum(1 for d in door_classifications if d["classification"] == "egress"),
            "interior_doors": sum(1 for d in door_classifications if d["classification"] == "interior"),
            "stairwell_doors": sum(1 for d in door_classifications if d["classification"] == "stairwell"),
        },
        "doors": door_classifications,
    }
