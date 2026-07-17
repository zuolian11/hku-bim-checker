# AI Prompts Used

This project was built using AI-powered coding assistance.
Below are the key prompts and the AI-assisted decisions made.

## Architecture & Design

- "Analyze the HKU AI+BIM technical test requirements and propose options"
  → Led to choosing FastAPI + ifcopenshell + web-ifc-viewer stack
- "Evaluate web-ifc-viewer as a rendering solution"
  → Replaced custom Three.js geometry approach with web-ifc-viewer for professional 3D rendering

## Compliance Rules

- "Implement door clear width check per fire egress standards (>= 900mm)"
  → checker.py: extracts IfcDoor.OverallWidth, flags violations
- "Implement FireRating completeness check on doors and walls"
  → checker.py: extracts Pset_Pset_WallCommon.FireRating and Pset_DoorCommon.FireRating

## Debugging & Iteration

- "Why is no 3D model rendering? Diagnose step by step"
  → Found 3 issues: JS syntax error, coordinate scaling (35km site), WASM path not set
- "Fix color coding of failed elements using createSubset"
  → Used web-ifc-viewer's createSubset API for red/yellow overlays

## Key AI-Assisted Decisions

| Decision | Reasoning |
|----------|-----------|
| Use web-ifc-viewer instead of raw Three.js | Professional IFC rendering + built-in navigation + WASM parsing |
| Parse IFC on frontend (browser) | No server-side geometry conversion needed, faster |
| Keep FastAPI backend for rule checking only | Clean separation: Python for rules, JS for visualization |
| COORDINATE_TO_ORIGIN config | Models with geo-referenced coordinates (35km span) need origin centering |
