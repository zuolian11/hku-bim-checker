import ifcopenshell
import ifcopenshell.util.element as util
import ifcopenshell.util.placement as pl


def extract_geometry(ifc_path: str) -> dict:
    model = ifcopenshell.open(ifc_path)
    elements = []

    positions = []
    for elem in model.by_type("IfcDoor") + model.by_type("IfcWall"):
        try:
            p = pl.get_local_placement(elem.ObjectPlacement)
            positions.append((float(p[0][3]), float(p[1][3]), float(p[2][3])))
        except Exception:
            positions.append((0, 0, 0))

    if not positions:
        return {"elements": [], "total": 0}

    cx = sum(p[0] for p in positions) / len(positions)
    cy = sum(p[1] for p in positions) / len(positions)
    cz = sum(p[2] for p in positions) / len(positions)

    sx = max(p[0] for p in positions) - min(p[0] for p in positions) or 1
    sy = max(p[1] for p in positions) - min(p[1] for p in positions) or 1
    scale = 1.0

    for door in model.by_type("IfcDoor"):
        geo = _elem_box(door, cx, cy, cz, scale, "IfcDoor", [0.2, 0.5, 1.0])
        if geo:
            elements.append(geo)

    for wall in model.by_type("IfcWall"):
        geo = _elem_box(wall, cx, cy, cz, scale, "IfcWall", [0.7, 0.7, 0.7])
        if geo:
            elements.append(geo)

    return {"elements": elements, "total": len(elements)}


def _elem_box(elem, cx, cy, cz, scale, etype, color) -> dict | None:
    info = elem.get_info()
    is_door = (etype == "IfcDoor")

    if is_door:
        w_m = float(info.get("OverallWidth") or 900) * 0.001
        h_m = float(info.get("OverallHeight") or 2100) * 0.001
        d_m = 0.1
    else:
        qtos = util.get_psets(elem, qtos_only=True)
        base = {}
        for k, v in qtos.items():
            if k.startswith("Qto_"):
                base = v; break
        w_m = float(base.get("Length", base.get("NetSideLength", 3000))) * 0.001
        h_m = float(base.get("Height", base.get("NetHeight", 3000))) * 0.001
        d_m = float(base.get("Width", base.get("NetWidth", 200))) * 0.001

    try:
        p = pl.get_local_placement(elem.ObjectPlacement)
        px, py, pz = float(p[0][3]), float(p[1][3]), float(p[2][3])
    except Exception:
        px, py, pz = 0, 0, 0

    px = (px - cx) * scale
    py = (py - cy) * scale
    pz = (pz - cz) * scale

    w = w_m * scale
    d = d_m * scale
    h = h_m * scale

    hw, hd, hh = w / 2, d / 2, h / 2
    verts = [
        px - hw, py - hd, pz - hh,  px + hw, py - hd, pz - hh,
        px + hw, py + hd, pz - hh,  px - hw, py + hd, pz - hh,
        px - hw, py - hd, pz + hh,  px + hw, py - hd, pz + hh,
        px + hw, py + hd, pz + hh,  px - hw, py + hd, pz + hh,
    ]
    faces = [
        0, 1, 2, 0, 2, 3,  4, 5, 6, 4, 6, 7,
        0, 4, 5, 0, 5, 1,  1, 5, 6, 1, 6, 2,
        2, 6, 7, 2, 7, 3,  3, 7, 4, 3, 4, 0,
    ]
    return {"id": info["id"], "type": etype, "vertices": verts, "faces": faces, "color": color}
