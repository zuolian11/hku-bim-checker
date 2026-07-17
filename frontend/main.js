/**
 * BIM Compliance Checker — Frontend
 */
import { IfcViewerAPI } from "web-ifc-viewer";
import { MeshStandardMaterial, Box3, Vector3 } from "three";

const $ = (id) => document.getElementById(id);

// ── Viewer ──────────────────────────────────────────
const viewer = new IfcViewerAPI({ container: $("viewer") });
viewer.grid.setGrid(30, 30);
viewer.IFC.setWasmPath("/");
viewer.IFC.loader.ifcManager.applyWebIfcConfig({ COORDINATE_TO_ORIGIN: true });

let checkResults = null;
let modelID = 0;
let backendModelID = null;

// ── Status ──────────────────────────────────────────
const statusBar = $("status");
function showStatus(msg, error = false, loading = false) {
  statusBar.classList.add("show");
  statusBar.classList.toggle("error", error);
  statusBar.innerHTML = (loading ? '<span class="dot"></span>' : "") + msg;
}
function hideStatus() { statusBar.classList.remove("show"); }

// ── API Key Persistence ────────────────────────────
const keyInput = $("ai-key");
const savedKey = localStorage.getItem("bim_api_key");
if (savedKey) keyInput.value = savedKey;
keyInput.addEventListener("input", () => localStorage.setItem("bim_api_key", keyInput.value.trim()));

$("btn-key-toggle").addEventListener("click", () => {
  const isPass = keyInput.type === "password";
  keyInput.type = isPass ? "text" : "password";
  $("btn-key-toggle").textContent = isPass ? "Hide" : "Show";
});

$("btn-recheck").addEventListener("click", async () => {
  if (!backendModelID) { showStatus("Upload a model first."); return; }
  try {
    showStatus("Re-checking...", false, true);
    checkResults = await (await fetch(`http://localhost:8000/api/check/${backendModelID}`, { method: "POST" })).json();
    renderReport();
    highlightViolations(modelID);
    hideStatus();
  } catch(e) { showStatus(e.message, true); }
});

$("btn-pdf").addEventListener("click", async () => {
  if (!checkResults) { showStatus("Run a check first."); return; }
  try {
    showStatus("Generating PDF...", false, true);
    const res = await fetch("http://localhost:8000/api/report-pdf", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report: checkResults }),
    });
    if (!res.ok) { showStatus("PDF failed: " + res.status, true); return; }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "compliance-report.pdf";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    hideStatus();
  } catch(e) { showStatus(e.message, true); }
});

function getApiKey() { return $("ai-key").value.trim(); }
$("btn-preview").addEventListener("click", async () => {
  const text = $("ai-input").value.trim();
  if (!text) return;
  try {
    showStatus("Analyzing...", false, true);
    const res = await fetch("http://localhost:8000/api/ai-preview", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ regulation: text, api_key: getApiKey() }),
    });
    const data = await res.json();
    const preview = $("ai-preview");
    preview.style.display = "block";
    const rules = data.parsed_rules;
    if (rules[0]?.condition === "parse_failed") {
      preview.innerHTML = `<span style="color:var(--warn)">${rules[0].error || "Parse failed"}</span>`;
    } else {
      preview.innerHTML = rules.map(r =>
        `<div style="color:var(--pass);margin:4px 0">${r.target === "IfcDoor" ? "Door" : r.target.replace("Ifc","")} | ${r.property} ${r.condition} ${r.value ?? ""} ${r.unit ?? ""} ${r.scope !== "all" ? "("+r.scope+")" : ""}</div>`
      ).join("");
    }
    hideStatus();
  } catch(e) { showStatus(e.message, true); }
});
$("btn-ai").addEventListener("click", async () => {
  if (!backendModelID) { showStatus("Upload a model first."); return; }
  const text = $("ai-input").value.trim();
  if (!text) return;
  showStatus("Generating rule...", false, true);
  try {
    const res = await fetch(`http://localhost:8000/api/ai-rule/${backendModelID}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ regulation: text }),
    });
    const data = await res.json();
    if (!data.rules || !Array.isArray(data.rules)) {
      showStatus("Rule generation failed: " + JSON.stringify(data), true);
      return;
    }
    checkResults = data;
    renderReport();
    hideStatus();
    // Reload the model to apply new colors
    if (window._lastFile && modelID >= 0) {
      viewer.IFC.loader.ifcManager.close(modelID);
      const m = await viewer.IFC.loadIfc(window._lastFile, false);
      modelID = m.modelID;
      highlightViolations(modelID);
    }
  } catch (e) { showStatus(e.message, true); }
});
const drop = $("drop-zone");
const inp = $("file-input");
drop.addEventListener("click", () => inp.click());
drop.addEventListener("dragover", (e) => e.preventDefault());
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  if (e.dataTransfer.files.length) handle(e.dataTransfer.files[0]);
});
inp.addEventListener("change", () => { if (inp.files.length) handle(inp.files[0]); });

async function handle(file) {
  window._lastFile = file;
  const isIFC = file.name.toLowerCase().endsWith(".ifc");
  drop.style.display = "none";
  $("section-summary").classList.add("show");
  $("section-issues").classList.add("show");
  $("btn-clear").style.display = "";

  try {
    if (isIFC) {
      showStatus("Loading 3D model...", false, true);
      const model = await viewer.IFC.loadIfc(file, false);
      modelID = model.modelID;
    }

    showStatus("Running checks...", false, true);
    const fd = new FormData(); fd.append("file", file);
    const u = await (await fetch("http://localhost:8000/api/upload", { method: "POST", body: fd })).json();
    backendModelID = u.model_id;
    checkResults = await (await fetch(`http://localhost:8000/api/check/${backendModelID}`, { method: "POST" })).json();

    renderReport();
    if (isIFC) {
      highlightViolations(modelID);
      loadSpatialAnalysis(backendModelID);
      viewer.grid.active = false;
      viewer.grid.dispose();
    }
    hideStatus();
  } catch (e) {
    showStatus(e.message, true);
    console.error(e);
  }
}

// ── Highlight ───────────────────────────────────────
function highlightViolations(mid) {
  const failed = [], warned = [];
  for (const r of checkResults.rules) {
    for (const it of r.items) {
      if (it.status === "fail") failed.push(it.id);
      else if (it.status === "warning") warned.push(it.id);
    }
  }
  if (failed.length) {
    viewer.IFC.loader.ifcManager.createSubset({
      modelID: mid, ids: failed, removePrevious: true, customID: "fail",
      material: new MeshStandardMaterial({
        color: 0xff0000, roughness: 0.5, metalness: 0,
      }),
    });
  }
  if (warned.length) {
    viewer.IFC.loader.ifcManager.createSubset({
      modelID: mid, ids: warned, removePrevious: true, customID: "warn",
      material: new MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.5, metalness: 0 }),
    });
  }
}

// ── Report ──────────────────────────────────────────
function renderReport() {
  const rules = checkResults?.rules;
  if (!rules || !Array.isArray(rules)) {
    $("issue-list").innerHTML = '<p style="color:var(--muted);font-size:12px;padding:12px">No rule results.</p>';
    return;
  }
  let pass = 0, fail = 0, warn = 0;
  let items = "";

  for (const r of checkResults.rules) {
    pass += r.passed; fail += r.failed; warn += r.warnings;
    for (const it of r.items) {
      if (it.status === "pass") continue;
      const isWarn = it.status === "warning";
      items += `
        <div class="issue-item" data-id="${it.id}" data-type="${it.type}">
          <span class="tag ${isWarn ? 'warn' : 'fail'}">${isWarn ? 'Warning' : 'Failed'}</span>
          <div class="title">${it.name || "Unnamed"}</div>
          <div class="sub">${it.message}</div>
        </div>`;
    }
  }

  $("stat-cards").innerHTML = `
    <div class="stat-card pass"><div class="number">${pass}</div><div class="label">Passed</div></div>
    <div class="stat-card fail"><div class="number">${fail}</div><div class="label">Failed</div></div>
    <div class="stat-card warn" style="grid-column:span 2"><div class="number">${warn}</div><div class="label">Warnings</div></div>
  `;
  $("issue-list").innerHTML = items || '<p style="color:var(--muted);font-size:12px;padding:12px">All checks passed.</p>';

  // Click focus
  $("issue-list").querySelectorAll(".issue-item").forEach((el) => {
    el.addEventListener("click", async () => {
      const id = parseInt(el.dataset.id);
      try {
        viewer.IFC.loader.ifcManager.removeSubset(modelID, undefined, "focus");
        const subset = viewer.IFC.loader.ifcManager.createSubset({
          modelID, ids: [id], removePrevious: false, customID: "focus",
          material: new MeshStandardMaterial({ color: 0xff00ff, roughness: 0.3, metalness: 0.4, transparent: true, opacity: 0.7 }),
        });
        if (subset) {
          await viewer.context.ifcCamera.targetItem(subset);
        }
        setTimeout(() => viewer.IFC.loader.ifcManager.removeSubset(modelID, undefined, "focus"), 3000);
      } catch (err) { console.error(err); }
    });
  });
}

// ── Spatial Analysis ───────────────────────────────
async function loadSpatialAnalysis(mid) {
  try {
    const res = await fetch(`http://localhost:8000/api/analyze/${mid}`);
    const data = await res.json();
    const s = data.summary;
    $("stat-cards").innerHTML += `
      <div class="stat-card" style="grid-column:span 2;margin-top:8px;font-size:12px;padding:10px 12px;text-align:left;line-height:1.6">
        <div style="color:var(--muted);margin-bottom:4px">Door Classification</div>
        <span style="color:#ef4444;font-weight:600">${s.egress_doors}</span> egress &nbsp;
        <span style="color:#3b82f6;font-weight:600">${s.interior_doors}</span> interior &nbsp;
        <span style="color:#f59e0b;font-weight:600">${s.stairwell_doors}</span> stairwell
        <div style="color:var(--muted);font-size:10px;margin-top:4px">${s.total_spaces} spaces, ${s.total_storeys} storeys</div>
      </div>`;
    $("ai-input").placeholder = s.egress_doors > 0
      ? `egress doors must be at least 1000mm wide`
      : "all doors must be at least 900mm wide";
  } catch(e) {}
}
