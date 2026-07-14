"""
BIM Compliance Checker — Backend API
"""
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import ifcopenshell

from checker import check_all, check_door_width_json, check_fire_rating_json, RuleResult
from cad_checker import check_dxf_width, check_dxf_fire_rating
from cad_utils import detect_dwg_version
from ai_rule_gen import parse_regulation
from llm_engine import llm_parse_regulation, llm_explain_failure
from pdf_report import generate_pdf
from spatial_analysis import analyze_spatial

app = FastAPI(title="BIM Compliance Checker")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE = Path(__file__).resolve().parent
TEMP = BASE / "temp"
TEMP.mkdir(exist_ok=True)
models = {}
MAX_FILE_SIZE = 50 * 1024 * 1024


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Accept .ifc or .json file."""
    name = file.filename.lower()
    if not (name.endswith(".ifc") or name.endswith(".json") or name.endswith(".dxf") or name.endswith(".dwg")):
        raise HTTPException(400, "Only .ifc, .json, .dxf, .dwg files accepted.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large.")

    model_id = uuid.uuid4().hex[:8]
    if name.endswith(".ifc"): ext = ".ifc"
    elif name.endswith(".json"): ext = ".json"
    elif name.endswith(".dxf"): ext = ".dxf"
    else: ext = ".dwg"
    filepath = TEMP / f"{model_id}{ext}"
    filepath.write_bytes(contents)

    models[model_id] = (str(filepath), ext)
    return {"model_id": model_id, "filename": file.filename, "format": ext.lstrip(".")}


@app.post("/api/check/{model_id}")
def run_check(model_id: str):
    """Run compliance rules on uploaded model (IFC or JSON)."""
    if model_id not in models:
        raise HTTPException(404, "Model not found.")

    filepath, ext = models[model_id]

    if ext == ".json":
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        results = [check_door_width_json(data), check_fire_rating_json(data)]
    elif ext in (".dxf", ".dwg"):
        if ext == ".dwg":
            version = detect_dwg_version(filepath) or "unknown version"
            results = [RuleResult(
                "dwg_format", "DWG binary format — needs conversion to DXF",
                warnings=1, items=[{
                    "id": 0, "name": f"DWG ({version})", "type": "CAD",
                    "status": "warning",
                    "message": f"DWG ({version}) detected. Convert: AutoCAD > Save As .dxf, or use free ODA File Converter."
                }]
            )]
        else:
            results = [check_dxf_width(filepath), check_dxf_fire_rating(filepath)]
    else:
        model = ifcopenshell.open(filepath)
        results = check_all(model)

    return {
        "model_id": model_id,
        "rules": [
            {"name": r.rule_name, "description": r.description,
             "passed": r.passed, "failed": r.failed, "warnings": r.warnings,
             "items": r.items}
            for r in results
        ],
    }


@app.get("/api/analyze/{model_id}")
def analyze_model(model_id: str):
    """Analyze building spatial structure and classify doors."""
    if model_id not in models:
        raise HTTPException(404, "Model not found.")
    filepath, ext = models[model_id]
    if ext != ".ifc":
        raise HTTPException(400, "Spatial analysis only available for IFC files.")
    model = ifcopenshell.open(filepath)
    return analyze_spatial(model)


@app.post("/api/ai-preview")
async def ai_preview(body: dict):
    """Preview generated rules. Falls back to LLM if regex fails."""
    text = body.get("regulation", "").strip()
    if not text: raise HTTPException(400, "Regulation text required.")
    api_key = body.get("api_key", "")

    rules = parse_regulation(text)

    # If regex found nothing and API key provided, try LLM
    if not rules and api_key:
        llm_rules = await llm_parse_regulation(text, api_key)
        if llm_rules:
            rules = llm_rules

    if not rules:
        rules = [{"condition": "parse_failed", "error": "Could not parse. Try LLM by providing an API key."}]

    return {"regulation": text, "parsed_rules": rules, "count": len(rules)}


@app.post("/api/ai-explain")
async def ai_explain(body: dict):
    """Generate AI remediation suggestion for a failed element."""
    element = body.get("element", {})
    rule_desc = body.get("rule", "")
    api_key = body.get("api_key", "")
    if not api_key:
        return {"explanation": "Add your API key to get AI-powered remediation suggestions."}

    explanation = await llm_explain_failure(element, rule_desc, api_key)
    return {"explanation": explanation}


@app.post("/api/ai-rule/{model_id}")
async def ai_rule(model_id: str, body: dict):
    text = body.get("regulation", "").strip()
    if not text: raise HTTPException(400, "Regulation text required.")
    if model_id not in models: raise HTTPException(404, "Upload a model first.")

    parsed = parse_regulation(text)
    filepath, ext = models[model_id]
    model = ifcopenshell.open(filepath)

    # Determine door filter from regulation text
    text_lower = text.lower()
    use_egress_only = any(kw in text_lower for kw in
        ("egress", "exit", "escape", "fire_exit", "疏散", "安全出口"))
    use_exterior = "exterior" in text_lower or "external" in text_lower or "室外" in text

    # Get spatial classification
    spatial = analyze_spatial(model) if ext == ".ifc" else None
    classified = {d["id"]: d["classification"] for d in (spatial or {}).get("doors", [])}

    from checker import RuleResult
    import ifcopenshell.util.element as util
    results = []

    for rule_def in parsed:
        r = RuleResult(rule_def["rule_name"], f"AI: {text[:60]}")
        elems = []
        if "IfcDoor" in rule_def["target"]:
            elems += model.by_type("IfcDoor")
        if "IfcWall" in rule_def["target"]:
            elems += model.by_type("IfcWall")

        prop, cond, val = rule_def["property"], rule_def["condition"], rule_def["value"]

        for e in elems:
            eid = e.get_info()["id"]

            # Apply classification filter
            if use_egress_only:
                cls = classified.get(eid, "interior")
                if cls not in ("egress", "stairwell"):
                    continue
            if use_exterior:
                cls = classified.get(eid, "interior")
                if cls != "exterior":
                    continue

            info = e.get_info()
            item = {"id": eid, "name": info.get("Name") or "Unnamed",
                    "type": info.get("type", e.is_a()), "guid": info.get("GlobalId"),
                    "classification": classified.get(eid, "unknown")}

            if cond == "exists":
                psets = util.get_psets(e)
                fr = psets.get("Pset_WallCommon", {}).get(prop) or psets.get("Pset_DoorCommon", {}).get(prop)
                if fr: item.update(status="pass", message=f"{prop}: {fr}"); r.passed += 1
                else: item.update(status="fail", message=f"{prop} not assigned"); r.failed += 1
            elif cond == "gte":
                actual = info.get(prop)
                if actual is None: item.update(status="warning", message=f"No {prop} data"); r.warnings += 1
                elif float(actual) < float(val): item.update(status="fail", message=f"{prop} {actual:.0f} < {val:.0f}"); r.failed += 1
                else: item.update(status="pass", message=f"OK ({actual:.0f})"); r.passed += 1
            elif cond == "parse_failed":
                item.update(status="warning", message=rule_def.get("error", "Parse failed")); r.warnings += 1
            r.items.append(item)
        results.append(r)

    return {"model_id": model_id, "regulation": text, "parsed_rules": parsed,
            "classification_filter": "egress" if use_egress_only else "all",
            "rules": [{"name": r.rule_name, "description": r.description,
                        "passed": r.passed, "failed": r.failed, "warnings": r.warnings,
                        "items": r.items} for r in results]}

from fastapi.responses import Response

@app.post("/api/debug-pdf")
def debug_pdf(body: dict):
    return {"got_report": "report" in body, "keys": list(body.keys()), "rules_count": len(body.get("report", {}).get("rules", []))}


@app.post("/api/report-pdf")
def export_pdf(body: dict):
    try:
        data = body.get("report", {})
        if not data: raise HTTPException(400, "Report data required.")
        pdf_bytes = generate_pdf(data)
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=report.pdf"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))
