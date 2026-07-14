# BIM Compliance Checker

> HKU AI+BIM Technical Test — July 2026  
> Built with [OpenCode](https://opencode.ai) AI assistant

A web-based micro-prototype for automated compliance checking on building models.

**Upload an IFC/JSON/CAD file → See 3D model → Get violation report → Generate custom rules with AI**

## Features

- **3D Model Rendering** — Powered by [web-ifc-viewer](https://github.com/ThatOpen/web-ifc-viewer)
- **Built-in Rules**: Door width (>= 900mm) + FireRating presence
- **Spatial Analysis** — Auto-classifies doors as egress / interior / stairwell
- **AI Rule Generator** — Type `"egress doors must be at least 1000mm wide"` → creates and runs the rule
- **Multi-format** — IFC, JSON, DXF supported; DWG detected with conversion guidance
- **Interactive** — Click any violation to fly camera to that element

## Quick Start

```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Example Prompts for AI Rule Generator

| Input | Result |
|-------|--------|
| `doors at least 900mm wide` | Check all doors >= 900mm |
| `egress doors at least 1000mm` | Only egress doors >= 1000mm |
| `FireRating required on all walls` | Check FireRating exists |
| `height must be at least 2100mm` | Check door height |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| 3D Viewer | web-ifc-viewer + Three.js |
| Backend | Python + FastAPI + ifcopenshell |
| AI Rules | Python regex + spatial analysis |
| CAD | ezdxf (DXF), binary header (DWG) |
| Frontend | Vanilla JS + Vite |

## Architecture

```
Browser (web-ifc-viewer)       Backend (FastAPI)
       │                             │
       ├── load .ifc → 3D            │
       ├── POST /api/upload ─────────┤
       ├── POST /api/check ──────────┤── ifcopenshell → checker.py
       ├── GET  /api/analyze ────────┤── spatial_analysis.py
       ├── POST /api/ai-rule ────────┤── ai_rule_gen.py
       │                             │
       └── colored subsets ←──── result + classifications
```

## File Structure

```
├── backend/
│   ├── main.py              FastAPI endpoints
│   ├── checker.py           Core compliance rules
│   ├── ai_rule_gen.py       NLP → rule engine
│   ├── spatial_analysis.py  Door classification
│   ├── cad_checker.py       DXF parsing rules
│   ├── cad_utils.py         DWG format detection
│   └── requirements.txt
├── frontend/
│   ├── index.html           UI + CSS
│   ├── main.js              App logic
│   └── package.json
├── samples/                 Test files (IFC, JSON, DWG)
├── prompts/                 AI prompts used
└── just-work.md             Development journal
```

## License

MIT
