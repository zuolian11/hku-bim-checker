/**
 * BIM Compliance Checker — Frontend
 *
 * Uses web-ifc-viewer for 3D rendering of IFC models,
 * FastAPI backend for compliance checking.
 */

import { IfcViewerAPI } from "web-ifc-viewer";
import { MeshBasicMaterial } from "three";

// ── UI Helpers ──────────────────────────────────────
const $ = (id) => document.getElementById(id);
const statusEl = $("status");
function status(msg, ok = true) {
  statusEl.textContent = msg;
  statusEl.style.color = ok ? "#4ecca3" : "#e94560";
}

// ── Viewer Init ─────────────────────────────────────
status("Initializing 3D engine...");
const viewer = new IfcViewerAPI({ container: $("viewer") });
viewer.grid.setGrid(30, 30);
viewer.IFC.setWasmPath("/");
viewer.IFC.loader.ifcManager.applyWebIfcConfig({ COORDINATE_TO_ORIGIN: true });

// ── State ───────────────────────────────────────────
let checkResults = null;
let modelID = 0;

// ── File Upload ─────────────────────────────────────
const uploadPanel = $("upload-panel");
const fileInput = $("file-input");
uploadPanel.addEventListener("click", () => fileInput.click());
uploadPanel.addEventListener("dragover", (e) => { e.preventDefault(); });
uploadPanel.addEventListener("drop", (e) => {
  e.preventDefault();
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

// ── Main Flow ───────────────────────────────────────
async function handleFile(file) {
  // Validate
  if (!file.name.toLowerCase().endsWith(".ifc")) {
    status("Please upload an .ifc file", false);
    return;
  }

  // Switch UI to results mode
  uploadPanel.style.display = "none";
  $("summary").style.display = "block";
  $("issues").style.display = "block";
  $("btn-reset").classList.remove("hidden");

  try {
    // Step 1: Load 3D model
    status("Loading 3D model...");
    const model = await viewer.IFC.loadIfc(file, false);
    modelID = model.modelID;

    // Step 2: Run compliance checks
    status("Running compliance checks...");
    const fd = new FormData();
    fd.append("file", file);
    const upRes = await fetch("http://localhost:8000/api/upload", { method: "POST", body: fd });
    if (!upRes.ok) throw new Error("Upload failed: " + upRes.status);
    const { model_id } = await upRes.json();

    const chRes = await fetch(`http://localhost:8000/api/check/${model_id}`, { method: "POST" });
    if (!chRes.ok) throw new Error("Check failed: " + chRes.status);
    checkResults = await chRes.json();
    renderReport();

    // Step 3: Highlight violations
    if (checkResults.rules.some((r) => r.failed > 0 || r.warnings > 0)) {
      status("Highlighting violations...");
      highlightViolations(modelID);
    }

    status("Ready");
  } catch (err) {
    status("Error: " + err.message, false);
    console.error(err);
  }
}

// ── Violation Highlighting ──────────────────────────
function highlightViolations(mid) {
  const failed = [];
  const warned = [];

  for (const rule of checkResults.rules) {
    for (const item of rule.items) {
      if (item.status === "fail") failed.push(item.id);
      else if (item.status === "warning") warned.push(item.id);
    }
  }

  if (failed.length) {
    viewer.IFC.loader.ifcManager.createSubset({
      modelID: mid,
      ids: failed,
      removePrevious: true,
      customID: "fail-overlay",
      material: new MeshBasicMaterial({
        color: 0xe94560,
        transparent: true,
        opacity: 0.5,
        depthTest: true,
      }),
    });
  }

  if (warned.length) {
    viewer.IFC.loader.ifcManager.createSubset({
      modelID: mid,
      ids: warned,
      removePrevious: true,
      customID: "warn-overlay",
      material: new MeshBasicMaterial({
        color: 0xf0a500,
        transparent: true,
        opacity: 0.5,
        depthTest: true,
      }),
    });
  }
}

// ── Report Rendering ────────────────────────────────
function renderReport() {
  let summary = "";
  let issues = "";

  for (const rule of checkResults.rules) {
    summary += `<h3>${rule.description}</h3>`;
    summary += `<div class="stat-row"><span>Passed</span><span class="pass">${rule.passed}</span></div>`;
    summary += `<div class="stat-row"><span>Failed</span><span class="fail">${rule.failed}</span></div>`;
    if (rule.warnings) {
      summary += `<div class="stat-row"><span>Warnings</span><span class="warn">${rule.warnings}</span></div>`;
    }

    for (const item of rule.items) {
      if (item.status === "pass") continue;
      const css = item.status === "warning" ? " warn" : "";
      issues += `
        <div class="issue${css}" data-id="${item.id}">
          <span class="name">${item.name || "Unnamed"}</span>
          <span class="detail">${item.message} (${item.type || ""})</span>
        </div>`;
    }
  }

  $("summary").innerHTML = `<h2>Summary</h2>${summary}`;
  $("issues").innerHTML = `<h2>Issues</h2>${issues || "<p>All checks passed.</p>"}`;

  // Click-to-focus
  $("issues").querySelectorAll(".issue").forEach((el) => {
    el.addEventListener("click", async () => {
      const id = parseInt(el.dataset.id);
      try {
        const subset = viewer.IFC.loader.ifcManager.createSubset({
          modelID,
          ids: [id],
          removePrevious: true,
          customID: "focus-highlight",
          material: new MeshBasicMaterial({
            color: 0x00ff88,
            transparent: true,
            opacity: 0.8,
            depthTest: true,
          }),
        });
        if (subset) {
          await viewer.context.ifcCamera.targetItem(subset);
        }
        // Remove focus highlight after 2s
        setTimeout(() => {
          viewer.IFC.loader.ifcManager.removeSubset(modelID, undefined, "focus-highlight");
        }, 2500);
      } catch (err) {
        console.error("Focus failed:", err);
      }
    });
  });
}

status("Drop an .ifc file to begin");
