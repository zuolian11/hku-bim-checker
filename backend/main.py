"""
BIM Compliance Checker — Backend API
FastAPI server that runs compliance checks on IFC models.
"""
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import ifcopenshell

from checker import check_all

app = FastAPI(title="BIM Compliance Checker")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BASE = Path(__file__).resolve().parent
TEMP = BASE / "temp"
TEMP.mkdir(exist_ok=True)

# In-memory model storage (resets on restart)
models = {}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Accept an .ifc file, store it, return a model ID."""
    if not file.filename.lower().endswith(".ifc"):
        raise HTTPException(400, "Only .ifc files are accepted.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large (max {MAX_FILE_SIZE // 1024 // 1024} MB).")

    model_id = uuid.uuid4().hex[:8]
    filepath = TEMP / f"{model_id}.ifc"
    filepath.write_bytes(contents)

    models[model_id] = str(filepath)
    return {"model_id": model_id, "filename": file.filename}


@app.post("/api/check/{model_id}")
def run_check(model_id: str):
    """Run compliance rules on a previously uploaded model."""
    if model_id not in models:
        raise HTTPException(404, "Model not found. Upload first.")

    model = ifcopenshell.open(models[model_id])
    results = check_all(model)

    return {
        "model_id": model_id,
        "rules": [
            {
                "name": r.rule_name,
                "description": r.description,
                "passed": r.passed,
                "failed": r.failed,
                "warnings": r.warnings,
                "items": r.items,
            }
            for r in results
        ],
    }
