# BIM Compliance Checker

> HKU AI+BIM Technical Test — July 2026

A web-based micro-prototype that performs automated compliance checking on building information models (IFC format).  
Upload an `.ifc` file, see it in 3D, and get instant violation reports.

## Features

- **3D Model Rendering** — Powered by [web-ifc-viewer](https://github.com/ThatOpen/web-ifc-viewer), renders IFC geometry directly in the browser
- **Compliance Rules**:
  1. Door clear width >= 900 mm (fire egress per GB 50016 / NFPA 101)
  2. FireRating property completeness on all doors and walls
- **Interactive Highlighting** — Violations colored red (fail) / yellow (warning); click any issue to focus camera
- **Dark-themed UI** — Drag-and-drop upload, real-time status, collapsible report panel

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| 3D Viewer | web-ifc-viewer (Three.js) | Browser-native IFC parsing, professional rendering, orbit controls |
| Backend API | Python + FastAPI + ifcopenshell | Clean async API, native IFC property extraction |
| Compliance Engine | Python + ifcopenshell | Direct IFC schema access, property set (Pset) extraction |
| Frontend | Vanilla JS + Vite | Zero-framework, fast HMR, simple build |

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 22+
- npm

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, drop an `.ifc` file, done.

### Test Samples
Three IFC files provided in `samples/`:
- `Ifc4_Revit_ARC.ifc` — Revit-exported architecture model (IFC4, 63 elements)
- `BasicHouse.ifc` — Simple residential house
- `Duplex_Architecture.ifc` — Multi-storey duplex with room spaces

## Architecture

```
Browser (web-ifc-viewer)    Backend (FastAPI)
       │                          │
       ├── load .ifc ── 3D render │
       │                          │
       ├── POST /api/upload ──────┤
       ├── POST /api/check/ ──────┤── ifcopenshell → checker.py
       │                          │
       └── colored subsets ◄──── result JSON
              ↑
       click-to-focus
```

## Project Structure

```
├── backend/             FastAPI server
│   ├── main.py          API endpoints + error handling
│   ├── checker.py       Compliance rule definitions
│   ├── geometry.py      IFC geometry extraction (legacy)
│   └── requirements.txt
├── frontend/            Vite + web-ifc-viewer
│   ├── index.html       Main page + CSS
│   ├── main.js          App logic
│   ├── package.json
│   └── public/          WASM files
├── samples/             Test IFC files
├── prompts/             AI prompts used during development
└── just-work.md         Development journal
```

## License

MIT
