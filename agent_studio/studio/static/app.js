/* ECAA Agent Studio — canvas editor, run streaming and step-by-step trace viewer.
   No build step and no external libraries. */
"use strict";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const S = {
  catalog: null,
  nodes: [], edges: [],
  sel: null,                 // {kind:'node'|'edge', id}
  view: { x: 40, y: 40, k: 1 },
  runs: {},                  // agentNodeId -> run
  runOrder: [],
  activeRun: null,
  running: false,
  tab: "ledger",
  playTimer: null,
  hl: null,                  // highlighted evidence id
};
let seq = 1;
const uid = (p) => `${p}${Date.now().toString(36)}${(seq++).toString(36)}`;

const TYPES = {
  environment: { label: "Environment", color: "var(--env)", ins: 0, outs: 1,
    blurb: "Sandboxed task world: hidden state, read-only tools, policy." },
  agent: { label: "LLM agent", color: "var(--agent)", ins: 1, outs: 1,
    blurb: "The model that gathers evidence and decides." },
  selfreview: { label: "Self-review", color: "var(--review)", ins: 1, outs: 1,
    blurb: "The model re-checks its own decision (B+)." },
  policy: { label: "Policy gate", color: "var(--policy)", ins: 1, outs: 1,
    blurb: "Deterministic rule check before committing actions (C)." },
  verifier: { label: "ECAA verifier", color: "var(--verifier)", ins: 1, outs: 1,
    blurb: "Independent check of the explanation certificate (D1/D2)." },
  executor: { label: "Executor", color: "var(--exec)", ins: 1, outs: 0,
    blurb: "Records the final decision in the sandbox." },
};
const NEXT = { environment: ["agent"], agent: ["selfreview", "policy", "verifier", "executor"],
  selfreview: ["executor"], policy: ["executor"], verifier: ["executor"], executor: [] };
const ARCH_COLOR = { A: "var(--exec)", B: "var(--review)", "B+": "var(--review)", C: "var(--policy)",
  D1: "var(--verifier)", D2: "var(--verifier)" };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const show = (v) => (typeof v === "string" ? v : JSON.stringify(v));
const clone = (o) => JSON.parse(JSON.stringify(o));
const node = (id) => S.nodes.find((n) => n.id === id);
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* ignore */ } },
};
function parseValue(text) {
  const t = text.trim();
  if (t === "") return null;
  try { return JSON.parse(t); } catch { return t; }
}
function pill(text, cls = "") { return `<span class="pill ${cls}">${esc(text)}</span>`; }
function fmtUsd(v) { return v == null ? "–" : `$${v < 0.01 ? v.toFixed(4) : v.toFixed(3)}`; }
function act(name, params) {
  const e = Object.entries(params || {});
  return e.length ? `${name}(${e.map(([k, v]) => `${k}=${typeof v === "string" ? v : JSON.stringify(v)}`).join(", ")})` : name;
}
function fmtTok(n) { return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n ?? 0); }

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  S.catalog = await (await fetch("/api/catalog")).json();
  renderPalette();
  const saved = store.get("ecaa-studio-graph");
  if (saved && saved.nodes && saved.nodes.length) {
    S.nodes = saved.nodes; S.edges = saved.edges || []; S.view = saved.view || S.view;
  } else {
    loadTemplate("example");
  }
  bindCanvas(); bindChrome();
  // URL options for demos: ?template=compare&provider=mock&run=1&tab=cert&step=12
  const q = new URLSearchParams(location.search);
  if (q.get("template")) loadTemplate(q.get("template"));
  if (q.get("provider")) S.nodes.filter((n) => n.type === "agent").forEach((n) => { n.data.provider = q.get("provider"); });
  if (q.get("tab")) S.tab = q.get("tab");
  renderAll();
  if (q.get("template")) requestAnimationFrame(fit);
  if (q.get("run") === "1") {
    await runAll();
    const stepTo = Number(q.get("step"));
    const run = S.runs[S.activeRun];
    if (run && stepTo) { run.cursor = Math.min(run.items.length - 1, stepTo - 1); run.live = false; renderTrace(); }
  }
}

function save() { store.set("ecaa-studio-graph", { nodes: S.nodes, edges: S.edges, view: S.view }); }

// ---------------------------------------------------------------------------
// Defaults and templates
// ---------------------------------------------------------------------------
function scenario(id) { return S.catalog.scenarios.find((s) => s.id === id); }
function defaultData(type) {
  const live = S.catalog.providers.openai;
  switch (type) {
    case "environment": {
      const sc = S.catalog.scenarios[0];
      return { scenarioId: sc.id, state: clone(sc.state) };
    }
    case "agent": return { name: "Agent", provider: live ? "openai" : "mock", model: S.catalog.default_model,
      temperature: 0, explain: "before", max_steps: 14, max_revisions: 2 };
    case "selfreview": return { rounds: 1 };
    case "verifier": return { components: Object.keys(S.catalog.components), adaptive: false, replays: 1 };
    default: return {};
  }
}
function addNode(type, x, y, data = {}) {
  const n = { id: uid(type.slice(0, 3)), type, x, y, data: { ...defaultData(type), ...data } };
  S.nodes.push(n); return n;
}
function link(a, b) { S.edges.push({ id: uid("e"), from: a.id, to: b.id }); }

function loadTemplate(name) {
  S.nodes = []; S.edges = []; S.sel = null; S.view = { x: 40, y: 30, k: 1 };
  if (name === "blank") return;
  const env = addNode("environment", 20, 150);
  const row = (y, arch, label) => {
    const a = addNode("agent", 300, y, { name: label, explain: arch === "A" || arch === "C" ? "after" : "before" });
    const ex = addNode("executor", 840, y);
    link(env, a);
    if (arch === "A" || arch === "B") { link(a, ex); return; }
    const gate = arch === "C" ? addNode("policy", 570, y) : arch === "B+" ? addNode("selfreview", 570, y)
      : addNode("verifier", 570, y, { adaptive: arch === "D2" });
    link(a, gate); link(gate, ex);
  };
  if (name === "example") row(150, "D1", "ECAA buyer");
  if (name === "compare") { row(40, "A", "Standard buyer"); row(260, "D1", "ECAA buyer"); }
  if (name === "all") {
    env.y = 300;
    [["A", "Standard"], ["B", "Explain first"], ["C", "Policy-gated"], ["D1", "ECAA strict"], ["D2", "ECAA adaptive"]]
      .forEach(([arch, label], i) => row(10 + i * 150, arch, label));
  }
}

// ---------------------------------------------------------------------------
// Compilation: canvas -> agent pipelines
// ---------------------------------------------------------------------------
function archOf(agent, chain) {
  const gate = chain.length === 2 ? chain[0] : null;
  if (gate?.type === "verifier") return gate.data.adaptive ? "D2" : "D1";
  if (gate?.type === "policy") return "C";
  if (gate?.type === "selfreview") return "B+";
  return agent.data.explain === "after" ? "A" : "B";
}
function pipelines() {
  const out = [];
  for (const a of S.nodes.filter((n) => n.type === "agent")) {
    const inEdge = S.edges.find((e) => e.to === a.id);
    const env = inEdge ? node(inEdge.from) : null;
    const chain = []; let cur = a; const seen = new Set();
    while (true) {
      const e = S.edges.find((x) => x.from === cur.id);
      if (!e || seen.has(e.to)) break;
      seen.add(e.to); cur = node(e.to); if (!cur) break; chain.push(cur);
      if (cur.type === "executor") break;
    }
    const valid = !!env && chain.length > 0 && chain.length <= 2 && chain[chain.length - 1].type === "executor";
    const problem = !env ? "not connected to an environment" : !valid ? "not connected through to an executor" : "";
    const arch = archOf(a, chain);
    const gate = chain.length === 2 ? chain[0] : null;
    out.push({ agent: a, env, chain, gate, exec: valid ? chain[chain.length - 1] : null, valid, problem, arch,
      spec: {
        id: a.id, name: a.data.name, provider: a.data.provider, model: a.data.model,
        temperature: a.data.temperature, explain: a.data.explain,
        max_steps: a.data.max_steps, max_revisions: a.data.max_revisions,
        gate: gate?.type === "verifier" ? "verifier" : gate?.type === "policy" ? "policy" : "none",
        self_review: gate?.type === "selfreview" ? gate.data.rounds : 0,
        verifier: gate?.type === "verifier" ? gate.data : undefined,
      } });
  }
  return out;
}
function canConnect(from, to) {
  if (!from || !to || from.id === to.id) return false;
  if (!NEXT[from.type].includes(to.type)) return false;
  if (from.type !== "environment" && S.edges.some((e) => e.from === from.id)) return false;
  if (S.edges.some((e) => e.to === to.id)) return false;
  return true;
}

// ---------------------------------------------------------------------------
// Rendering: palette, canvas
// ---------------------------------------------------------------------------
function renderPalette() {
  $("#palette-items").innerHTML = Object.entries(TYPES).map(([t, d]) =>
    `<div class="pal-item" draggable="true" data-type="${t}" style="--c:${d.color}">
       <div><b>${d.label}</b><span>${d.blurb}</span></div></div>`).join("");
  document.querySelectorAll(".pal-item").forEach((el) =>
    el.addEventListener("dragstart", (ev) => ev.dataTransfer.setData("text/plain", el.dataset.type)));
}

function nodeSummary(n, pipes) {
  const d = n.data;
  if (n.type === "environment") {
    const sc = scenario(d.scenarioId);
    const st = d.state || {};
    return `<div class="n-title" title="${esc(sc?.title)}">${esc(sc?.title || "Custom environment")}</div>
      ${pill(st.domain?.replace("_", " ") || "?")}${pill(`${(st.entities || []).length} entities`)}${pill(`${Object.keys(st.facts || {}).length} facts`)}`;
  }
  if (n.type === "agent") {
    const p = pipes.find((x) => x.agent.id === n.id);
    const prov = d.provider === "mock" ? pill("mock model", "warn") : pill(d.model.replace(/-\d{4}-\d{2}-\d{2}$/, ""), "info");
    const arch = p ? `${pill(`${p.arch} · ${S.catalog.architectures[p.arch].name}`)}` : "";
    return `<div class="n-title">${esc(d.name)}</div>${prov}${arch}
      ${p && !p.valid ? `<div style="color:var(--bad)">${esc(p.problem)}</div>` : ""}`;
  }
  if (n.type === "verifier") {
    return `<div class="n-title">${d.adaptive ? "Adaptive (risk-tiered)" : "Strict"}</div>
      ${d.components.map((c) => pill(c)).join("")}`;
  }
  if (n.type === "policy") return `<div class="n-title">Policy gate</div>${pill("commit actions only")}`;
  if (n.type === "selfreview") return `<div class="n-title">${d.rounds} review round${d.rounds > 1 ? "s" : ""}</div>`;
  if (n.type === "executor") return `<div class="n-title">Sandbox executor</div>${pill("no external effect")}`;
  return "";
}

function renderNodes() {
  const pipes = pipelines();
  const invalidAgents = new Set(pipes.filter((p) => !p.valid).map((p) => p.agent.id));
  $("#nodes").innerHTML = S.nodes.map((n) => {
    const t = TYPES[n.type];
    const cls = ["node", S.sel?.kind === "node" && S.sel.id === n.id ? "sel" : "", invalidAgents.has(n.id) ? "invalid" : ""].join(" ");
    return `<div class="${cls}" data-id="${n.id}" style="left:${n.x}px;top:${n.y}px;--c:${t.color}">
      ${t.ins ? `<div class="port in" data-port="in" data-id="${n.id}"></div>` : ""}
      ${t.outs ? `<div class="port out" data-port="out" data-id="${n.id}"></div>` : ""}
      <div class="n-head"><div class="n-type">${t.label}</div></div>
      <div class="n-body">${nodeSummary(n, pipes)}<div class="n-status" data-status="${n.id}"></div></div>
    </div>`;
  }).join("");
  renderEdges();
  applyRunVisuals();
}

function portPos(id, which) {
  const n = node(id); const el = document.querySelector(`.node[data-id="${id}"]`);
  const w = el ? el.offsetWidth : 210;
  return { x: n.x + (which === "out" ? w : 0), y: n.y + 27 };
}
function curve(a, b) {
  const dx = Math.max(40, Math.abs(b.x - a.x) / 2);
  return `M${a.x},${a.y} C${a.x + dx},${a.y} ${b.x - dx},${b.y} ${b.x},${b.y}`;
}
function renderEdges(temp) {
  const svg = $("#edges");
  svg.innerHTML = S.edges.map((e) => {
    if (!node(e.from) || !node(e.to)) return "";
    const sel = S.sel?.kind === "edge" && S.sel.id === e.id ? "sel" : "";
    return `<path data-edge="${e.id}" class="${sel}" d="${curve(portPos(e.from, "out"), portPos(e.to, "in"))}"/>`;
  }).join("") + (temp ? `<path class="temp" d="${curve(temp.a, temp.b)}"/>` : "");
}
function applyView() {
  $("#world").style.transform = `translate(${S.view.x}px,${S.view.y}px) scale(${S.view.k})`;
}
function renderAll() {
  applyView(); renderNodes(); renderInspector(); updateRunNote();
}

// ---------------------------------------------------------------------------
// Canvas interaction
// ---------------------------------------------------------------------------
function toWorld(cx, cy) {
  const r = $("#canvas").getBoundingClientRect();
  return { x: (cx - r.left - S.view.x) / S.view.k, y: (cy - r.top - S.view.y) / S.view.k };
}
function bindCanvas() {
  const canvas = $("#canvas");
  canvas.addEventListener("dragover", (ev) => ev.preventDefault());
  canvas.addEventListener("drop", (ev) => {
    ev.preventDefault();
    const type = ev.dataTransfer.getData("text/plain");
    if (!TYPES[type]) return;
    const p = toWorld(ev.clientX, ev.clientY);
    const n = addNode(type, p.x - 100, p.y - 25);
    S.sel = { kind: "node", id: n.id }; save(); renderAll();
  });

  let drag = null;
  canvas.addEventListener("pointerdown", (ev) => {
    const port = ev.target.closest(".port");
    const nodeEl = ev.target.closest(".node");
    const edgeEl = ev.target.closest("path[data-edge]");
    canvas.focus();
    if (port && port.dataset.port === "out") {
      drag = { kind: "link", from: port.dataset.id };
    } else if (port && port.dataset.port === "in") {
      // drag an existing connection off an input to remove/re-route it
      const e = S.edges.find((x) => x.to === port.dataset.id);
      if (e) { S.edges = S.edges.filter((x) => x !== e); drag = { kind: "link", from: e.from }; save(); renderNodes(); }
    } else if (nodeEl) {
      const n = node(nodeEl.dataset.id);
      S.sel = { kind: "node", id: n.id };
      const p = toWorld(ev.clientX, ev.clientY);
      drag = { kind: "move", n, dx: p.x - n.x, dy: p.y - n.y, moved: false };
      document.querySelectorAll(".node.sel").forEach((x) => x.classList.remove("sel"));
      nodeEl.classList.add("sel"); renderInspector(); renderEdges();
    } else if (edgeEl) {
      S.sel = { kind: "edge", id: edgeEl.dataset.edge }; renderNodes(); renderInspector();
    } else {
      drag = { kind: "pan", sx: ev.clientX - S.view.x, sy: ev.clientY - S.view.y };
      canvas.classList.add("panning");
      if (S.sel) { S.sel = null; renderNodes(); renderInspector(); }
    }
    if (drag) canvas.setPointerCapture(ev.pointerId);
  });
  canvas.addEventListener("pointermove", (ev) => {
    if (!drag) return;
    if (drag.kind === "pan") {
      S.view.x = ev.clientX - drag.sx; S.view.y = ev.clientY - drag.sy; applyView();
    } else if (drag.kind === "move") {
      const p = toWorld(ev.clientX, ev.clientY);
      drag.n.x = Math.round((p.x - drag.dx) / 10) * 10; drag.n.y = Math.round((p.y - drag.dy) / 10) * 10;
      drag.moved = true;
      const el = document.querySelector(`.node[data-id="${drag.n.id}"]`);
      el.style.left = `${drag.n.x}px`; el.style.top = `${drag.n.y}px`;
      renderEdges(); applyRunVisuals(true);
    } else if (drag.kind === "link") {
      const b = toWorld(ev.clientX, ev.clientY);
      document.querySelectorAll(".port.hot").forEach((x) => x.classList.remove("hot"));
      const target = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".node");
      if (target && canConnect(node(drag.from), node(target.dataset.id))) target.querySelector(".port.in")?.classList.add("hot");
      renderEdges({ a: portPos(drag.from, "out"), b });
    }
  });
  canvas.addEventListener("pointerup", (ev) => {
    if (!drag) return;
    canvas.classList.remove("panning");
    if (drag.kind === "link") {
      const target = document.elementFromPoint(ev.clientX, ev.clientY)?.closest(".node");
      const to = target ? node(target.dataset.id) : null;
      const from = node(drag.from);
      if (to && canConnect(from, to)) { link(from, to); msg(""); }
      else if (to && to.id !== from.id) msg(`A ${TYPES[from.type].label} cannot connect to that ${TYPES[to.type].label} (allowed next: ${NEXT[from.type].map((t) => TYPES[t].label).join(", ") || "none"}; one input per block).`, true);
      save(); renderAll();
    } else if (drag.kind === "move") {
      if (drag.moved) save();
    } else if (drag.kind === "pan") save();
    drag = null;
  });
  canvas.addEventListener("wheel", (ev) => {
    ev.preventDefault();
    zoomAt(ev.deltaY < 0 ? 1.1 : 1 / 1.1, ev.clientX, ev.clientY);
  }, { passive: false });
  canvas.addEventListener("keydown", (ev) => {
    if ((ev.key === "Delete" || ev.key === "Backspace") && S.sel) {
      ev.preventDefault(); deleteSelected();
    }
  });
  $("#zoom-in").onclick = () => zoomCenter(1.15);
  $("#zoom-out").onclick = () => zoomCenter(1 / 1.15);
  $("#zoom-fit").onclick = fit;
}
function zoomAt(f, cx, cy) {
  const r = $("#canvas").getBoundingClientRect();
  const k = Math.min(2, Math.max(0.35, S.view.k * f)); const real = k / S.view.k;
  S.view.x = cx - r.left - (cx - r.left - S.view.x) * real;
  S.view.y = cy - r.top - (cy - r.top - S.view.y) * real;
  S.view.k = k; applyView(); save();
}
function zoomCenter(f) { const r = $("#canvas").getBoundingClientRect(); zoomAt(f, r.left + r.width / 2, r.top + r.height / 2); }
function fit() {
  if (!S.nodes.length) return;
  const r = $("#canvas").getBoundingClientRect();
  const xs = S.nodes.map((n) => n.x), ys = S.nodes.map((n) => n.y);
  const minX = Math.min(...xs) - 30, minY = Math.min(...ys) - 30, maxX = Math.max(...xs) + 250, maxY = Math.max(...ys) + 150;
  const k = Math.min(1.2, Math.max(0.35, Math.min(r.width / (maxX - minX), r.height / (maxY - minY))));
  S.view = { k, x: -minX * k + (r.width - (maxX - minX) * k) / 2, y: -minY * k + (r.height - (maxY - minY) * k) / 2 };
  applyView(); save();
}
function deleteSelected() {
  if (!S.sel) return;
  if (S.sel.kind === "edge") S.edges = S.edges.filter((e) => e.id !== S.sel.id);
  else {
    S.nodes = S.nodes.filter((n) => n.id !== S.sel.id);
    S.edges = S.edges.filter((e) => e.from !== S.sel.id && e.to !== S.sel.id);
  }
  S.sel = null; save(); renderAll();
}
function msg(text, err = false) { const el = $("#canvas-msg"); el.textContent = text; el.className = `canvas-msg${err ? " err" : ""}`; }

// ---------------------------------------------------------------------------
// Inspector
// ---------------------------------------------------------------------------
function renderInspector() {
  const el = $("#inspector");
  if (!S.sel) {
    el.innerHTML = `<h2>Inspector</h2><p class="hint">Select a block on the canvas to configure it.</p>
      <div class="box"><h4>How to use</h4>
      <ol class="rules"><li>Load <b>Example: ECAA agent buys monitors</b> or drag blocks from the left.</li>
      <li>Connect <b>Environment → Agent → (gate) → Executor</b>.</li>
      <li>Click an Environment to choose or edit the task; click an Agent to pick the model.</li>
      <li>Press <b>Run</b>. Each step streams into the trace below and lights up the canvas.</li>
      <li>Use the playback controls to step through what the agent did.</li></ol></div>
      <div class="box"><h4>Keyboard</h4>Delete removes the selected block or connection. Drag empty canvas to pan, scroll to zoom. Drag a connection off its input port to remove it.</div>`;
    return;
  }
  if (S.sel.kind === "edge") {
    el.innerHTML = `<h2>Connection</h2><button id="del">Delete connection</button>`;
    $("#del").onclick = deleteSelected; return;
  }
  const n = node(S.sel.id); if (!n) { S.sel = null; return renderInspector(); }
  const t = TYPES[n.type];
  const head = `<h2 style="color:${t.color}">${t.label}</h2><p class="hint">${t.blurb}</p>`;
  const del = `<p><button id="del" class="ghost">Delete block</button></p>`;
  const editors = { environment: inspectEnv, agent: inspectAgent, verifier: inspectVerifier,
    policy: inspectPolicy, selfreview: inspectReview, executor: inspectExec };
  el.innerHTML = head + `<div id="insp-body"></div>` + del;
  editors[n.type](n, $("#insp-body"));
  $("#del").onclick = deleteSelected;
}
function changed(n, rerenderInspector = false) {
  save(); renderNodes(); updateRunNote(); if (rerenderInspector) renderInspector();
}

function domainOfAgent(n) {
  const p = pipelines().find((x) => x.agent.id === n.id);
  return p?.env?.data.state?.domain;
}

function inspectEnv(n, el) {
  const d = n.data; const st = d.state;
  const groups = {};
  for (const sc of S.catalog.scenarios) {
    const g = "Examples";
    (groups[g] ||= []).push(sc);
  }
  const sc = scenario(d.scenarioId);
  const dom = S.catalog.domains[st.domain];
  const orig = sc?.state?.facts || {};
  const facts = Object.entries(st.facts || {});
  el.innerHTML = `
    <div class="field"><label for="env-sc">Task scenario</label>
      <select id="env-sc">${Object.entries(groups).map(([g, list]) => `<optgroup label="${esc(g)}">${list.map((s) =>
        `<option value="${esc(s.id)}" ${s.id === d.scenarioId ? "selected" : ""}>${esc(s.title)}</option>`).join("")}</optgroup>`).join("")}</select></div>
    ${sc ? `<div class="box">${esc(sc.story)}<div style="margin-top:4px">${pill(sc.domain.replace("_", " "))} ${pill(sc.difficulty)} ${pill(sc.source)}</div></div>` : ""}
    <div class="field"><button id="env-truth">Show correct answer (hidden from agents)</button><div id="env-truth-out"></div></div>
    <details open><summary>Hidden state — facts (${facts.length})</summary>
      <p class="hint">Agents never see this table; they reach it only through tools. Edit a value to create your own variant. Values are JSON (true, 12, "text", null).</p>
      <div class="field"><label for="env-ent">Entities</label><input id="env-ent" type="text" value="${esc((st.entities || []).join(", "))}"></div>
      <table class="facts">${facts.map(([k, v]) => `<tr><td>${esc(k)}</td><td><input data-fact="${esc(k)}" class="${JSON.stringify(orig[k]) !== JSON.stringify(v) ? "changed" : ""}" value="${esc(JSON.stringify(v))}"></td></tr>`).join("")}</table>
      <div class="row" style="margin-top:6px"><input id="env-newk" type="text" placeholder="new.fact.key"><input id="env-newv" type="text" placeholder="value"><button id="env-add" style="flex:0">Add</button></div>
    </details>
    <details><summary>Correspondence / informal notes (${(st.notes || []).length})</summary>
      <p class="hint">Returned by the correspondence tool. "claims" become <code>claimed.*</code> keys, which never count as facts.</p>
      ${(st.notes || []).map((no, i) => `<div class="note-ed"><textarea rows="2" data-note="${i}">${esc(no.text)}</textarea>
        <input type="text" data-claims="${i}" style="width:100%" value="${esc(JSON.stringify(no.claims || {}))}" title="claims JSON"></div>`).join("")}
      <button id="env-addnote">Add note</button>
    </details>
    <details><summary>Tools the agent can call (${dom.tools.length})</summary>
      <ul class="rules">${dom.tools.map((x) => `<li><code>${esc(x.name)}</code> — ${esc(x.description)}</li>`).join("")}</ul></details>
    <details><summary>Actions (${dom.actions.length})</summary>
      <ul class="rules">${dom.actions.map((x) => `<li><code>${esc(x.name)}</code>${x.commits ? " " + pill("commits", "warn") : ""} — ${esc(x.description)}</li>`).join("")}</ul></details>
    <details><summary>Policy rules (${dom.rules.length})</summary>
      <ul class="rules">${dom.rules.map((r) => `<li><b>${esc(r.id)}</b> <span class="muted">(${esc(r.governs.join(", "))})</span> ${esc(r.text)}</li>`).join("")}</ul>
      ${dom.procedure ? `<pre>${esc(dom.procedure)}</pre>` : ""}</details>
    <p><button id="env-reset" class="ghost">Reset to original scenario</button></p>`;
  $("#env-sc").onchange = (e) => { const s = scenario(e.target.value); d.scenarioId = s.id; d.state = clone(s.state); changed(n, true); };
  $("#env-reset").onclick = () => { d.state = clone(scenario(d.scenarioId).state); changed(n, true); };
  $("#env-ent").onchange = (e) => { st.entities = e.target.value.split(",").map((x) => x.trim()).filter(Boolean); changed(n); };
  el.querySelectorAll("input[data-fact]").forEach((inp) => inp.onchange = () => {
    st.facts[inp.dataset.fact] = parseValue(inp.value);
    inp.classList.toggle("changed", JSON.stringify(orig[inp.dataset.fact]) !== JSON.stringify(st.facts[inp.dataset.fact]));
    $("#env-truth-out").innerHTML = ""; changed(n);
  });
  $("#env-add").onclick = () => { const k = $("#env-newk").value.trim(); if (!k) return; st.facts[k] = parseValue($("#env-newv").value); changed(n, true); };
  el.querySelectorAll("textarea[data-note]").forEach((ta) => ta.onchange = () => { st.notes[+ta.dataset.note].text = ta.value; changed(n); });
  el.querySelectorAll("input[data-claims]").forEach((inp) => inp.onchange = () => {
    try { st.notes[+inp.dataset.claims].claims = JSON.parse(inp.value || "{}"); inp.style.borderColor = ""; changed(n); }
    catch { inp.style.borderColor = "var(--bad)"; }
  });
  $("#env-addnote").onclick = () => { (st.notes ||= []).push({ text: "", claims: {} }); changed(n, true); };
  $("#env-truth").onclick = async () => {
    const out = $("#env-truth-out");
    const r = await fetch("/api/oracle", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ state: st }) });
    const j = await r.json();
    out.innerHTML = r.ok ? `<div class="box"><div class="big">${esc(j.label)}</div>
      <div>Decisive rules: ${j.decisive_rules.map((x) => pill(x)).join(" ") || "–"}</div>
      <div>Decisive facts: ${j.decisive_facts.map((x) => `<code>${esc(x)}</code>`).join(", ") || "–"}</div>
      <p class="hint" style="margin:4px 0 0">Computed by the rule-based oracle from the hidden state. It is never shown to an agent.</p></div>`
      : `<div class="box" style="color:var(--bad)">${esc(j.error)}</div>`;
  };
}

function inspectAgent(n, el) {
  const d = n.data; const p = S.catalog.providers;
  const pipe = pipelines().find((x) => x.agent.id === n.id);
  const gated = pipe?.gate;
  el.innerHTML = `
    <div class="field"><label for="ag-name">Name</label><input id="ag-name" type="text" value="${esc(d.name)}"></div>
    <div class="field"><label for="ag-prov">Model provider</label><select id="ag-prov">
      <option value="mock" ${d.provider === "mock" ? "selected" : ""}>Mock (deterministic, offline, free)</option>
      <option value="openai" ${d.provider === "openai" ? "selected" : ""} ${p.openai ? "" : "disabled"}>OpenAI${p.openai ? "" : " (OPENAI_API_KEY not set)"}</option>
    </select></div>
    <div class="field"><label for="ag-model">Model</label><input id="ag-model" type="text" value="${esc(d.model)}" ${d.provider === "mock" ? "disabled" : ""}></div>
    <div class="row">
      <div class="field"><label for="ag-temp">Temperature</label><input id="ag-temp" type="number" min="0" max="2" step="0.1" value="${d.temperature}"></div>
      <div class="field"><label for="ag-steps">Max turns</label><input id="ag-steps" type="number" min="3" max="30" value="${d.max_steps}"></div>
      <div class="field"><label for="ag-rev">Max revisions</label><input id="ag-rev" type="number" min="0" max="5" value="${d.max_revisions}"></div>
    </div>
    <div class="field"><span class="lbl">Explanation</span>
      <label class="check"><input type="radio" name="ag-ex" value="before" ${d.explain !== "after" ? "checked" : ""} ${gated?.type === "policy" ? "disabled" : ""}>
        <span>Before acting (certificate)<small>The decision carries a structured explanation the pipeline can check.</small></span></label>
      <label class="check"><input type="radio" name="ag-ex" value="after" ${d.explain === "after" ? "checked" : ""} ${gated?.type === "verifier" || gated?.type === "selfreview" ? "disabled" : ""}>
        <span>After acting<small>Explains once the decision is already recorded.</small></span></label>
      ${gated ? `<p class="hint">Fixed by the ${TYPES[gated.type].label}: ${gated.type === "policy" ? "explains after acting" : "explains before acting"}.</p>` : ""}
    </div>
    ${pipe ? `<div class="box"><h4>Compiled architecture: ${esc(pipe.arch)} · ${esc(S.catalog.architectures[pipe.arch].name)}</h4>${esc(S.catalog.architectures[pipe.arch].description)}
      ${pipe.valid ? "" : `<div style="color:var(--bad);margin-top:4px">Incomplete: ${esc(pipe.problem)}.</div>`}</div>` : ""}
    <p><button id="ag-prompt" ${pipe?.env ? "" : "disabled"}>View the system prompt this agent receives</button></p>
    ${d.provider === "mock" ? `<div class="banner mock">The mock model is a deterministic test double that follows the policy with seeded errors. Its runs demonstrate the pipeline; they are not evidence about any real model.</div>` : ""}`;
  const bind = (id, key, conv = (v) => v) => { $(id).onchange = (e) => { d[key] = conv(e.target.value); changed(n, id === "#ag-prov"); }; };
  bind("#ag-name", "name"); bind("#ag-prov", "provider"); bind("#ag-model", "model");
  bind("#ag-temp", "temperature", Number); bind("#ag-steps", "max_steps", Number); bind("#ag-rev", "max_revisions", Number);
  el.querySelectorAll("input[name=ag-ex]").forEach((r) => r.onchange = () => { d.explain = r.value; changed(n, true); });
  $("#ag-prompt").onclick = async () => {
    const r = await fetch("/api/prompt", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent: pipe.spec, domain: domainOfAgent(n) }) });
    const j = await r.json();
    modal(`System prompt · ${j.architecture}`, j.prompt || j.error);
  };
}

function inspectVerifier(n, el) {
  const d = n.data;
  el.innerHTML = `
    <label class="check"><input type="checkbox" id="vf-ad" ${d.adaptive ? "checked" : ""}>
      <span><b>Adaptive depth (D2)</b><small>Low risk: provenance, numeric, policy. Medium adds contradiction and completeness. High (irreversible, large or conflicting evidence) adds counterfactual replay.</small></span></label>
    <div class="field"><span class="lbl">Checks${d.adaptive ? " (ceiling; tiers choose a subset)" : ""}</span>
      ${Object.entries(S.catalog.components).map(([c, txt]) => `<label class="check"><input type="checkbox" data-comp="${c}" ${d.components.includes(c) ? "checked" : ""}>
        <span><b>${c}</b><small>${esc(txt)}</small></span></label>`).join("")}</div>
    <div class="field"><label for="vf-rep">Replays per counterfactual claim</label><input id="vf-rep" type="number" min="1" max="3" value="${d.replays}"></div>
    <div class="box">A failed check blocks execution. The agent receives the reasons and may gather more evidence, fix its certificate or choose another action, up to the agent's revision limit; then it abstains.</div>`;
  $("#vf-ad").onchange = (e) => { d.adaptive = e.target.checked; changed(n, true); };
  $("#vf-rep").onchange = (e) => { d.replays = Number(e.target.value); changed(n); };
  el.querySelectorAll("input[data-comp]").forEach((c) => c.onchange = () => {
    d.components = Object.keys(S.catalog.components).filter((k) => el.querySelector(`input[data-comp="${k}"]`).checked);
    changed(n);
  });
}
function inspectPolicy(n, el) {
  const agentEdge = S.edges.find((e) => e.to === n.id);
  const pipe = agentEdge && pipelines().find((p) => p.agent.id === agentEdge.from);
  const dom = pipe?.env ? S.catalog.domains[pipe.env.data.state.domain] : null;
  el.innerHTML = `<div class="box">Before a committing action (purchase, refund, trade) is executed, every rule that governs it is recomputed from the facts the agent observed. Any rule that is violated or unknown blocks execution and is fed back to the agent. The explanation is written after acting and is not checked.</div>
    ${dom ? `<h4>Rules for ${esc(pipe.env.data.state.domain.replace("_", " "))}</h4><ul class="rules">${dom.rules.map((r) => `<li><b>${esc(r.id)}</b> ${esc(r.text)}</li>`).join("")}</ul>` : `<p class="hint">Connect it to an agent to see the rules.</p>`}`;
}
function inspectReview(n, el) {
  el.innerHTML = `<div class="field"><label for="rv">Review rounds</label><input id="rv" type="number" min="1" max="3" value="${n.data.rounds}"></div>
    <div class="box">The model is asked to re-check its own certificate and decision. This is the cost-matched control: extra model effort, but nothing outside the model checks the explanation.</div>`;
  $("#rv").onchange = (e) => { n.data.rounds = Number(e.target.value); changed(n); };
}
function inspectExec(n, el) {
  el.innerHTML = `<div class="box">Records the final decision. Nothing outside the sandbox is touched: no purchase, refund or trade is carried out.</div>`;
}

function modal(title, body) {
  $("#modal-title").textContent = title; $("#modal-body").textContent = body; $("#modal").hidden = false;
}

// ---------------------------------------------------------------------------
// Running
// ---------------------------------------------------------------------------
function updateRunNote() {
  const pipes = pipelines().filter((p) => p.valid);
  const live = pipes.filter((p) => p.agent.data.provider !== "mock");
  const note = !pipes.length ? "No complete pipeline" :
    live.length ? `${pipes.length} agent${pipes.length > 1 ? "s" : ""}, ${live.length} on a live model (≈ $0.01–0.04 each)` :
      `${pipes.length} agent${pipes.length > 1 ? "s" : ""} on the mock model (free)`;
  $("#run-note").textContent = note;
  $("#btn-run").disabled = S.running || !pipes.length;
}

async function runAll() {
  const pipes = pipelines().filter((p) => p.valid);
  if (!pipes.length) return;
  S.running = true; updateRunNote(); stopPlay();
  S.runs = {}; S.runOrder = []; S.activeRun = null;
  const byEnv = {};
  for (const p of pipes) (byEnv[p.env.id] ||= []).push(p);
  for (const p of pipes) {
    S.runs[p.agent.id] = { id: p.agent.id, name: p.agent.data.name, arch: p.arch, nodes: {
      env: p.env.id, agent: p.agent.id, gate: p.gate?.id, exec: p.exec.id }, gateType: p.gate?.type,
      envState: clone(p.env.data.state), items: [], cursor: -1, live: true, status: "starting",
      provider: p.agent.data.provider };
    S.runOrder.push(p.agent.id);
  }
  S.activeRun = S.runOrder[0];
  renderTrace();
  await Promise.all(Object.entries(byEnv).map(([envId, list]) => stream(node(envId), list)));
  S.running = false; updateRunNote(); renderTrace();
}

async function stream(env, list) {
  let res;
  try {
    res = await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ environment: { state: env.data.state }, agents: list.map((p) => p.spec) }) });
  } catch (e) { list.forEach((p) => fail(p.agent.id, String(e))); return; }
  if (!res.ok) { const j = await res.json().catch(() => ({})); list.forEach((p) => fail(p.agent.id, j.error || res.statusText)); return; }
  const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = "";
  let oracle = null;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, i); buf = buf.slice(i + 1);
      if (!line.trim()) continue;
      const m = JSON.parse(line);
      if (m.type === "batch_start") { oracle = m.oracle; list.forEach((p) => { S.runs[p.agent.id].oracle = oracle; S.runs[p.agent.id].objective = m.objective; }); }
      else if (m.type === "batch_error") list.forEach((p) => fail(p.agent.id, m.message));
      else if (m.agent_id && S.runs[m.agent_id]) ingest(S.runs[m.agent_id], m);
    }
  }
}
function fail(id, message) {
  const r = S.runs[id]; if (!r) return;
  r.status = "error"; r.items.push({ kind: "error", message }); r.cursor = r.items.length - 1; renderTrace();
}
function ingest(run, m) {
  if (m.type === "run_start") { Object.assign(run, { meta: m, status: "running" }); }
  else if (m.type === "event") { run.items.push({ kind: "event", ...m.event }); }
  else if (m.type === "run_end") { run.end = m; run.status = m.metrics.correct ? "correct" : "wrong"; run.items.push({ kind: "result" }); }
  else if (m.type === "run_error") { run.status = "error"; run.items.push({ kind: "error", message: m.message }); }
  if (run.live) run.cursor = run.items.length - 1;
  scheduleRender();
}
let renderPending = false;
function scheduleRender() {
  if (renderPending) return; renderPending = true;
  requestAnimationFrame(() => { renderPending = false; renderTrace(); });
}

// ---------------------------------------------------------------------------
// Trace: interpretation of events
// ---------------------------------------------------------------------------
function parseModel(text) { try { return JSON.parse(text); } catch { return null; } }

/** Which canvas node and edge an item lights up. */
function focusOf(run, it) {
  const N = run.nodes;
  if (!it || it.kind === "result") return { node: N.exec };
  if (it.kind === "error") return { node: N.agent };
  switch (it.event) {
    case "task_start": return { node: N.env, edge: [N.env, N.agent] };
    case "model_call":
      if (it.purpose === "replay") return { node: N.gate || N.agent };
      if (it.purpose === "review") return { node: N.gate || N.agent, edge: [N.agent, N.gate] };
      return { node: N.agent };
    case "tool_response": case "tool_error": return { node: N.env, edge: [N.env, N.agent], back: true };
    case "decision_proposed": return { node: N.agent, edge: N.gate ? [N.agent, N.gate] : [N.agent, N.exec] };
    case "verification_start": case "verification": case "counterfactual_replay_start":
    case "counterfactual_replay": case "policy_check": return { node: N.gate, edge: [N.agent, N.gate] };
    case "revision": return { node: N.agent, edge: [N.agent, N.gate], back: true };
    case "proposed_action": return { node: N.gate || N.agent, edge: N.gate ? [N.gate, N.exec] : [N.agent, N.exec] };
    case "executed_action": case "certificate": case "run_end": return { node: N.exec, edge: N.gate ? [N.gate, N.exec] : [N.agent, N.exec] };
    default: return { node: N.agent };
  }
}

/** Status lines for each pipeline node, as of the run's cursor. */
function statusOf(run) {
  const st = {}; const upto = run.items.slice(0, run.cursor + 1);
  let turns = 0, obs = 0, last = "", tokens = 0;
  for (const it of upto) {
    if (it.event === "model_call" && it.purpose === "replay") { tokens += (it.input_tokens || 0) + (it.output_tokens || 0); continue; }
    if (it.event === "model_call") {
      turns++; tokens += (it.input_tokens || 0) + (it.output_tokens || 0);
      const c = parseModel(it.text);
      last = it.purpose === "replay" ? "counterfactual replay turn" : it.purpose === "explain" ? "writing explanation"
        : c?.type === "tool_call" ? `calls ${c.tool}` : c?.type === "decision" ? `decides ${c.action}` : "thinking";
    }
    if (it.event === "tool_response") obs++;
  }
  st[run.nodes.agent] = turns ? `Turn ${turns} · ${last} · ${fmtTok(tokens)} tok` : (run.status === "starting" ? "waiting…" : "");
  st[run.nodes.env] = `${obs} observation${obs === 1 ? "" : "s"} served`;
  if (run.nodes.gate) {
    const g = [...upto].reverse().find((x) => ["verification", "policy_check", "verification_start", "counterfactual_replay_start", "counterfactual_replay"].includes(x.event));
    if (g?.event === "verification") {
      const cc = g.report.claim_checks; const ok = cc.filter((c) => c.status === "supported").length;
      const cf = g.report.counterfactual_tests.map((t) => pill(`counterfactual ${t.status}`, t.status === "confirmed" ? "ok" : t.status === "refuted" ? "bad" : "warn")).join(" ");
      st[run.nodes.gate] = `<span class="pill ${g.status === "PASS" ? "ok" : "bad"}">${g.status}</span> ${ok}/${cc.length} claims supported ${cf}`
        + (g.failures.length ? `<div class="why bad">${esc(g.failures[0].length > 160 ? g.failures[0].slice(0, 157) + "…" : g.failures[0])}${g.failures.length > 1 ? ` (+${g.failures.length - 1} more)` : ""}</div>` : "");
    }
    else if (g?.event === "policy_check") st[run.nodes.gate] = `<span class="pill ${g.passed ? "ok" : "bad"}">${g.passed ? "PASS" : "BLOCKED"}</span> ${esc(g.action)}`;
    else if (g?.event === "verification_start") st[run.nodes.gate] = `<span class="spin"></span> checking (${esc(g.tier)})`;
    else if (g) st[run.nodes.gate] = `<span class="spin"></span> replaying ${esc(g.fact)}`;
  }
  // the agent's current explanation, shown on the canvas
  const prop = [...upto].reverse().find((x) => x.event === "decision_proposed" && x.certificate);
  const fin = upto.find((x) => x.event === "certificate")?.certificate;
  const why = prop?.certificate?.summary || fin?.explanation?.summary;
  if (why) {
    const n = (prop?.certificate || fin.explanation).claims.length;
    const timing = prop ? "before acting" : "after acting";
    st[run.nodes.agent] += `<div class="why"><b>Why (${timing}, ${n} claims):</b> ${esc(why.length > 220 ? why.slice(0, 217) + "…" : why)}</div>`;
  }
  const ex = upto.find((x) => x.event === "executed_action");
  if (ex) {
    const res = upto.some((x) => x.kind === "result") && run.end;
    st[run.nodes.exec] = `${esc(ex.action)} ${res ? (run.end.metrics.correct ? pill("✓ correct", "ok") : pill("✗ wrong", "bad")) : ""}`;
  }
  return st;
}

function applyRunVisuals(edgesOnly = false) {
  document.querySelectorAll(".node.active").forEach((x) => x.classList.remove("active"));
  document.querySelectorAll("#edges path.flow").forEach((x) => x.classList.remove("flow", "back"));
  if (!edgesOnly) document.querySelectorAll("[data-status]").forEach((x) => { x.innerHTML = ""; });
  for (const id of S.runOrder) {
    const run = S.runs[id]; if (!run) continue;
    if (!edgesOnly) {
      for (const [nid, html] of Object.entries(statusOf(run))) {
        if (nid === run.nodes.env && id !== S.activeRun) continue;  // shared environment: show the selected run
        const el = document.querySelector(`[data-status="${nid}"]`);
        if (el && html) el.innerHTML = (el.innerHTML ? el.innerHTML + "<br>" : "") + html;
      }
    }
    const isActive = id === S.activeRun;
    const running = run.status === "running" && run.live;
    if (!isActive && !running) continue;
    const f = focusOf(run, run.items[run.cursor]);
    if (f.node) document.querySelector(`.node[data-id="${f.node}"]`)?.classList.add("active");
    if (f.edge && f.edge[0] && f.edge[1]) {
      const e = S.edges.find((x) => x.from === f.edge[0] && x.to === f.edge[1]);
      const p = e && document.querySelector(`path[data-edge="${e.id}"]`);
      if (p) { p.classList.add("flow"); if (f.back) p.classList.add("back"); }
    }
  }
}

// ---------------------------------------------------------------------------
// Trace: rendering
// ---------------------------------------------------------------------------
function renderTrace() {
  renderStrip(); renderTimeline(); renderDetails(); renderPlayback(); applyRunVisuals();
}
function renderStrip() {
  const el = $("#run-strip");
  if (!S.runOrder.length) return;
  el.innerHTML = S.runOrder.map((id) => {
    const r = S.runs[id];
    const u = r.end?.usage; const cost = r.end?.metrics?.cost_usd;
    const st = r.status === "running" || r.status === "starting" ? `<span class="spin"></span>` :
      r.status === "correct" ? pill("✓ correct", "ok") : r.status === "wrong" ? pill("✗ wrong", "bad") : pill("error", "bad");
    return `<button class="run-chip ${id === S.activeRun ? "on" : ""}" data-run="${id}" style="--c:${ARCH_COLOR[r.arch]}">
      <b>${esc(r.name)}</b>${pill(r.arch)} ${st} ${r.end ? `<span class="muted">${esc(r.end.final_action)} · ${fmtTok(u.input_tokens + u.output_tokens)} tok · ${fmtUsd(cost)}</span>` : ""}</button>`;
  }).join("");
  el.querySelectorAll("[data-run]").forEach((b) => b.onclick = () => { S.activeRun = b.dataset.run; stopPlay(); renderTrace(); });
}

function card(it, i, run) {
  const C = { env: "var(--env)", agent: "var(--agent)", gate: run.gateType === "policy" ? "var(--policy)" : run.gateType === "selfreview" ? "var(--review)" : "var(--verifier)", exec: "var(--exec)" };
  const meta = (x) => `<span class="c-meta">${x}</span>`;
  const t = it.t != null ? `${it.t.toFixed(1)}s` : "";
  const wrap = (color, title, body = "", m = t, compact = false) =>
    `<div class="card ${compact ? "compact" : ""}" data-i="${i}" data-n="${i + 1}" style="--c:${color}"><div class="c-head"><span class="c-title">${title}</span>${meta(m)}</div>${body ? `<div class="c-body">${body}</div>` : ""}</div>`;
  if (it.kind === "error") return wrap("var(--bad)", "Run failed", `<pre>${esc(it.message)}</pre>`);
  if (it.kind === "result") {
    const m = run.end.metrics;
    return wrap(m.correct ? "var(--ok)" : "var(--bad)", m.correct ? "✓ Matches the correct answer" : "✗ Does not match the correct answer",
      `Agent: <code>${esc(m.final_action)}</code> · Correct: <code>${esc(m.oracle_action)}</code>
       ${m.policy_violation ? pill("policy violation executed", "bad") : ""} ${m.abstained ? pill("abstained", "warn") : ""}`, "");
  }
  switch (it.event) {
    case "task_start": return wrap(C.env, "Task received", esc(it.objective), `${t} · ${esc(it.model)}`);
    case "model_call": {
      const c = parseModel(it.text);
      const purpose = { step: "Model turn", explain: "Model writes explanation", replay: "Replay turn (counterfactual)", review: "Self-review turn" }[it.purpose] || it.purpose;
      let what = it.error ? `<span style="color:var(--bad)">provider error: ${esc(it.error)}</span>`
        : !c ? `<span style="color:var(--warn)">reply was not valid JSON</span>`
        : c.type === "tool_call" ? `→ calls <code>${esc(c.tool)}(${esc(Object.entries(c.args || {}).map(([k, v]) => `${k}=${show(v)}`).join(", "))})</code>`
        : c.type === "decision" ? `→ decides <code>${esc(act(c.action, c.params))}</code>${c.certificate ? " with certificate" : ""}`
        : c.certificate || c.summary ? "→ explanation" : "";
      return wrap(it.purpose === "replay" ? C.gate : C.agent, `${purpose} ${what}`,
        `<details><summary class="muted" style="font-weight:400">raw model output</summary><pre>${esc(c ? JSON.stringify(c, null, 2) : it.text)}</pre></details>`,
        `${t} · ${fmtTok(it.input_tokens)}→${fmtTok(it.output_tokens)} · ${(it.latency_s || 0).toFixed(1)}s`);
    }
    case "tool_response": {
      const auth = new Set(it.authoritative_keys || []);
      const rows = Object.entries(it.content).map(([k, v]) => `<tr class="${auth.has(k) ? "auth" : k.startsWith("claimed.") ? "informal" : ""}"><td>${esc(k)}</td><td>${esc(show(v))}</td></tr>`).join("");
      return wrap(C.env, `Observation <span class="ev">${esc(it.evidence_id)}</span> from <code>${esc(it.tool)}</code>`,
        `<table class="kv">${rows}</table>`);
    }
    case "tool_error": return wrap("var(--warn)", `Tool refused: <code>${esc(it.tool)}</code>`, esc(it.message));
    case "decision_proposed": {
      const cert = it.certificate;
      return wrap(C.agent, `Proposes <code>${esc(it.action)}</code>${it.revision ? ` (revision ${it.revision})` : ""}`,
        cert ? `${esc(cert.summary)}<div style="margin-top:3px">${pill(`${cert.claims.length} claims`)} ${cert.decisive_factors.map((x) => `<code>${esc(x)}</code>`).join(", ")}</div>` : "");
    }
    case "verification_start": return wrap(C.gate, `Verifier checks the certificate · tier <b>${esc(it.tier)}</b>`, it.components.map((c) => pill(c)).join(" "), t, true);
    case "counterfactual_replay_start": return wrap(C.gate, `Counterfactual replay: re-runs the decision with <code>${esc(it.fact)} = ${esc(show(it.value))}</code>`, "", t, true);
    case "counterfactual_replay": return wrap(C.gate, `Replay result: <code>${esc(it.action ?? "no decision")}</code>`, "", t, true);
    case "verification": {
      const r = it.report; const counts = {};
      r.claim_checks.forEach((c) => { counts[c.status] = (counts[c.status] || 0) + 1; });
      return wrap(it.status === "PASS" ? "var(--ok)" : "var(--bad)", `Verification ${pill(it.status, it.status === "PASS" ? "ok" : "bad")} for <code>${esc(it.action)}</code>`,
        `${Object.entries(counts).map(([k, v]) => pill(`${v} ${k}`, k === "supported" ? "ok" : k === "not_checked" ? "" : k === "uncertain" ? "warn" : "bad")).join(" ")}
         ${r.counterfactual_tests.map((ct) => pill(`counterfactual ${ct.status}`, ct.status === "confirmed" ? "ok" : ct.status === "refuted" ? "bad" : "warn")).join(" ")}
         ${it.failures.length ? `<ul class="reasons">${it.failures.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}`);
    }
    case "policy_check":
      return wrap(it.passed ? "var(--ok)" : "var(--bad)", `Policy gate ${pill(it.passed ? "PASS" : "BLOCKED", it.passed ? "ok" : "bad")} for <code>${esc(it.action)}</code>`,
        `<table class="kv"><tr><th>Rule</th><th>Status</th><th>Detail</th></tr>${(it.results || []).map((r) => `<tr><td>${esc(r.rule_id)}</td><td>${pill(r.status, r.status === "satisfied" ? "ok" : r.status === "violated" ? "bad" : "warn")}</td><td>${esc(r.detail)}</td></tr>`).join("")}</table>`);
    case "revision": return wrap("var(--warn)", `Sent back for revision (${esc(it.reason)})`, `<ul class="reasons">${it.failures.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>`);
    case "proposed_action": return wrap(C.exec, `Submitted for execution: <code>${esc(it.action)}</code>`, "", t, true);
    case "executed_action": return wrap(C.exec, `Executed in sandbox: <code>${esc(it.action)}</code>`, esc(it.outcome?.message), t, true);
    case "certificate": return wrap(C.exec, "Certificate issued", `<span class="muted">See the Certificate &amp; checks tab.</span>`, t, true);
    case "run_end": return wrap(C.exec, `Run finished: <code>${esc(it.final_action)}</code>`, "", t, true);
    default: return wrap("var(--line)", esc(it.event), `<pre>${esc(JSON.stringify(it, null, 2))}</pre>`);
  }
}

function renderTimeline() {
  const el = $("#timeline"); const run = S.runs[S.activeRun];
  if (!run) { el.innerHTML = `<p class="muted">The step-by-step trace of the selected run appears here.</p>`; return; }
  const banner = run.provider === "mock"
    ? `<div class="banner mock">MOCK model: a deterministic test double. This trace demonstrates the pipeline and is not evidence about a real model.</div>`
    : `<div class="banner live">Live model ${esc(run.meta?.model || "")} in a synthetic sandbox. Nothing is executed outside the sandbox.</div>`;
  el.innerHTML = banner + run.items.map((it, i) => card(it, i, run)).join("") + (run.status === "running" ? `<p class="muted"><span class="spin"></span> running…</p>` : "");
  el.querySelectorAll(".card").forEach((c) => {
    const i = +c.dataset.i;
    if (i === run.cursor) c.classList.add("cur");
    if (!run.live && i > run.cursor) c.classList.add("future");
    c.addEventListener("click", (ev) => {
      if (ev.target.closest("details")) return;
      run.cursor = i; run.live = i === run.items.length - 1 && run.status === "running"; stopPlay(); renderTrace();
    });
  });
  const cur = el.querySelector(".card.cur");
  if (cur) {
    const top = cur.offsetTop, bottom = top + cur.offsetHeight;
    if (top < el.scrollTop || bottom > el.scrollTop + el.clientHeight) el.scrollTop = top - el.clientHeight / 3;
  }
}

function renderPlayback() {
  const run = S.runs[S.activeRun]; const n = run ? run.items.length : 0;
  const sc = $("#pb-scrub"); sc.max = Math.max(0, n - 1); sc.value = run ? Math.max(0, run.cursor) : 0;
  $("#pb-pos").textContent = run ? `${run.cursor + 1} / ${n}${run.live && run.status === "running" ? " · live" : ""}` : "0 / 0";
  $("#pb-play").textContent = S.playTimer ? "❚❚" : "▶";
}

// --- details tabs -------------------------------------------------------------
function upto(run) { return run.items.slice(0, run.cursor + 1); }
function renderDetails() {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === S.tab));
  const el = $("#details-body"); const run = S.runs[S.activeRun];
  if (!run) { el.innerHTML = `<p class="muted">Run a pipeline to see the evidence it gathered, its explanation certificate, each verification check and the outcome.</p>`; return; }
  ({ ledger: detailLedger, cert: detailCert, outcome: detailOutcome, prompt: detailPrompt })[S.tab](run, el);
  el.querySelectorAll(".ev[data-ev]").forEach((x) => {
    x.onmouseenter = () => { document.querySelectorAll(`tr[data-evrow="${x.dataset.ev}"]`).forEach((r) => r.classList.add("hl")); };
    x.onmouseleave = () => { document.querySelectorAll("tr.hl").forEach((r) => r.classList.remove("hl")); };
  });
}

function detailLedger(run, el) {
  const obs = upto(run).filter((x) => x.event === "tool_response");
  const truth = run.envState.facts || {};
  const facts = {};
  for (const o of obs) for (const k of o.authoritative_keys || []) if (k in o.content) facts[k] = { v: o.content[k], ev: o.evidence_id };
  const informal = [];
  for (const o of obs) for (const [k, v] of Object.entries(o.content)) if (k.startsWith("claimed.")) informal.push({ k, v, ev: o.evidence_id });
  const unseen = Object.keys(truth).filter((k) => !(k in facts));
  el.innerHTML = `
    <p class="hint">Facts the agent has established so far (from authoritative tools), compared with the hidden true state. Informal claims never count as facts.</p>
    <table class="kv"><tr><th>Fact</th><th>Observed</th><th>Evidence</th><th>True value</th></tr>
    ${Object.entries(facts).map(([k, f]) => {
      const ok = JSON.stringify(f.v) === JSON.stringify(truth[k]);
      return `<tr class="auth" data-evrow="${esc(f.ev)}"><td>${esc(k)}</td><td>${esc(show(f.v))}</td><td><span class="ev">${esc(f.ev)}</span></td><td>${ok ? pill("✓", "ok") : `${pill("≠", "bad")} ${esc(show(truth[k]))}`}</td></tr>`;
    }).join("") || `<tr><td colspan="4" class="muted">Nothing observed yet.</td></tr>`}</table>
    ${informal.length ? `<h4>Informal claims (not facts)</h4><table class="kv">${informal.map((x) =>
      `<tr class="informal" data-evrow="${esc(x.ev)}"><td>${esc(x.k)}</td><td>${esc(show(x.v))}</td><td><span class="ev">${esc(x.ev)}</span></td><td>${(() => { const k = x.k.slice(8); return k in truth ? (JSON.stringify(truth[k]) === JSON.stringify(x.v) ? pill("true", "ok") : pill(`false: really ${show(truth[k])}`, "bad")) : ""; })()}</td></tr>`).join("")}</table>` : ""}
    <details><summary>Hidden facts not yet observed (${unseen.length})</summary><table class="kv">${unseen.map((k) => `<tr><td>${esc(k)}</td><td>${esc(show(truth[k]))}</td></tr>`).join("")}</table></details>
    <h4>Observations (${obs.length})</h4>
    ${obs.map((o) => `<details><summary><span class="ev">${esc(o.evidence_id)}</span> ${esc(o.tool)}(${esc(Object.entries(o.args).map(([k, v]) => `${k}=${show(v)}`).join(", "))})</summary><pre>${esc(JSON.stringify(o.content, null, 2))}</pre></details>`).join("")}`;
}

function claimLine(c, check, evIndex) {
  const kind = c.kind;
  let body = "";
  if (kind === "evidence") body = `<code>${esc(c.fact)}</code> = <code>${esc(show(c.value))}</code>`;
  else if (kind === "numeric") body = `<code>${esc(c.expression)}</code> = <code>${esc(show(c.value))}</code>`;
  else if (kind === "policy") body = `<b>${esc(c.rule_id)}</b> is <b>${esc(c.status)}</b> for <code>${esc(act(c.action, c.params))}</code>`;
  else if (kind === "counterfactual") body = `if <code>${esc(c.fact)} = ${esc(show(c.value))}</code> → <code>${esc(act(c.predicted_action, c.predicted_params))}</code>`;
  const evs = (c.evidence_ids || []).map((e) => `<span class="ev" data-ev="${esc(e)}" title="${esc(evIndex[e] ? JSON.stringify(evIndex[e]) : "not an observed evidence id")}">${esc(e)}</span>`).join(" ");
  const st = check ? pill(check.status, check.status === "supported" ? "ok" : check.status === "not_checked" ? "" : check.status === "uncertain" ? "warn" : "bad") : "";
  return `<div class="claim"><span class="k">${esc(c.id)} · ${esc(kind)}</span>${st} ${body} ${evs}
    ${c.text ? `<div class="muted">${esc(c.text)}</div>` : ""}
    ${check && check.reasons.length ? `<ul class="reasons">${check.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}</div>`;
}

function detailCert(run, el) {
  const items = upto(run);
  const prop = [...items].reverse().find((x) => x.event === "decision_proposed" && x.certificate);
  const finalCert = items.find((x) => x.event === "certificate")?.certificate;
  const ver = [...items].reverse().find((x) => x.event === "verification");
  const draft = prop?.certificate || finalCert?.explanation;
  const evIndex = {}; items.filter((x) => x.event === "tool_response").forEach((o) => { evIndex[o.evidence_id] = o.content; });
  if (!draft || (!draft.claims.length && !draft.summary)) {
    el.innerHTML = `<p class="muted">${run.arch === "A" || run.arch === "C" ? "This architecture explains only after acting; the explanation appears once the decision is executed." : "No certificate yet."}</p>`;
    return;
  }
  const checks = {}; (ver?.report.claim_checks || []).forEach((c) => { checks[c.claim_id] = c; });
  const when = finalCert && !prop ? "written after acting (not checked before execution)" : prop ? `proposed with <code>${esc(prop.action)}</code>` : "";
  el.innerHTML = `
    ${ver ? `<div class="verdict ${ver.status === "PASS" ? "ok" : "bad"}"><span class="big">${ver.status}</span><span>Independent verification of <code>${esc(ver.action)}</code> · tier ${esc(ver.tier)} · ${ver.report.components_run.map((c) => pill(c)).join(" ")}</span></div>` : ""}
    <p class="hint">Certificate ${when}.</p>
    <div class="box"><b>Summary.</b> ${esc(draft.summary)}
      ${draft.decisive_factors.length ? `<div style="margin-top:4px"><b>Decisive factors:</b> ${draft.decisive_factors.map((x) => `<code>${esc(x)}</code>`).join(", ")}</div>` : ""}
      ${draft.expected_outcome ? `<div><b>Expected outcome:</b> ${esc(draft.expected_outcome)}</div>` : ""}
      ${draft.limitations?.length ? `<div><b>Limitations:</b> ${draft.limitations.map(esc).join("; ")}</div>` : ""}</div>
    <h4>Claims (${draft.claims.length})${ver ? " with verifier results" : ""}</h4>
    ${draft.claims.map((c) => claimLine(c, checks[c.id], evIndex)).join("")}
    ${draft.alternatives?.length ? `<h4>Alternatives considered</h4><table class="kv"><tr><th>Action</th><th>Rejected because</th></tr>${draft.alternatives.map((a) => `<tr><td>${esc(act(a.action, a.params))}</td><td>${a.rejected_because.map((r) => pill(r)).join(" ")} ${esc(a.text || "")}</td></tr>`).join("")}</table>` : ""}
    ${ver?.report.policy_results?.length ? `<h4>Policy recomputed by the verifier</h4><table class="kv"><tr><th>Rule</th><th>Action</th><th>Status</th><th>Detail</th></tr>${ver.report.policy_results.map((r) => `<tr><td>${esc(r.rule_id)}</td><td>${esc(r.action || "")}</td><td>${pill(r.status, r.status === "satisfied" ? "ok" : r.status === "violated" ? "bad" : "warn")}</td><td>${esc(r.detail || "")}</td></tr>`).join("")}</table>` : ""}
    ${ver?.report.counterfactual_tests?.length ? `<h4>Counterfactual tests</h4><table class="kv"><tr><th>Intervention</th><th>Predicted</th><th>Observed on replay</th><th>Result</th></tr>${ver.report.counterfactual_tests.map((t) => `<tr><td>${esc(t.fact)} = ${esc(show(t.value))}</td><td>${esc(t.predicted)}</td><td>${t.observed.map(esc).join(", ")}</td><td>${pill(t.status, t.status === "confirmed" ? "ok" : t.status === "refuted" ? "bad" : "warn")}</td></tr>`).join("")}</table>` : ""}
    ${ver?.failures.length ? `<h4>Why it failed</h4><ul class="reasons">${ver.failures.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}`;
}

function detailOutcome(run, el) {
  const o = run.oracle;
  if (!run.end || !upto(run).some((x) => x.kind === "result")) {
    el.innerHTML = `<p class="muted">${run.status === "running" ? "Still running." : "Step to the end of the run to see the outcome."}</p>
      ${o ? `<details><summary>Peek at the correct answer</summary><div class="box"><b>${esc(o.label)}</b></div></details>` : ""}`;
    return;
  }
  const m = run.end.metrics; const u = run.end.usage;
  const yes = (b) => (b ? pill("yes", "bad") : pill("no", "ok"));
  el.innerHTML = `
    <div class="verdict ${m.correct ? "ok" : m.abstained ? "warn" : "bad"}"><span class="big">${m.correct ? "✓ Correct" : m.abstained ? "Abstained" : "✗ Wrong"}</span>
      <span>Agent: <code>${esc(m.final_action)}</code><br>Correct answer: <code>${esc(m.oracle_action)}</code></span></div>
    <div class="box"><b>Why that is the answer.</b> Decisive rules ${o.decisive_rules.map((r) => pill(r)).join(" ") || "–"}; changing any of these facts would change the decision: ${o.decisive_facts.map((f) => `<code>${esc(f)}</code>`).join(", ") || "–"}.</div>
    <h4>Safety and explanation quality</h4>
    <div class="grid2">
      <div>Executed a policy violation</div><div>${yes(m.policy_violation)}</div>
      <div>Acted without support in observed facts</div><div>${yes(m.unsupported_action)}</div>
      <div>Explanation has an unsupported or false claim</div><div>${yes(m.any_unsupported_claim)}</div>
      <div>Cited evidence that does not exist</div><div>${yes(m.fabricated_evidence)}</div>
      <div>Fact claims true in the hidden state</div><div>${m.fact_claim_truth == null ? "–" : (m.fact_claim_truth * 100).toFixed(0) + "%"}</div>
      <div>Decisive factors recalled</div><div>${m.decisive_recall == null ? "–" : (m.decisive_recall * 100).toFixed(0) + "%"}</div>
      <div>Explanation completeness</div><div>${m.completeness == null ? "–" : (m.completeness * 100).toFixed(0) + "%"}</div>
    </div>
    <h4>Effort</h4>
    <div class="grid2">
      <div>Model calls (of which replays)</div><div>${u.model_calls} (${u.replay_calls})</div>
      <div>Tokens in / out</div><div>${fmtTok(u.input_tokens)} / ${fmtTok(u.output_tokens)}</div>
      <div>Cost (standard rate)</div><div>${fmtUsd(m.cost_usd)}</div>
      <div>Tool calls</div><div>${run.end.ledger.length}</div>
      <div>Verifications · revisions</div><div>${u.verifications} · ${m.revisions ?? "–"}</div>
      <div>Wall time</div><div>${run.end.wall_time_s.toFixed(1)}s</div>
    </div>`;
}

function detailPrompt(run, el) {
  el.innerHTML = run.meta ? `<p class="hint">Exactly what the ${esc(run.arch)} agent was told. The hidden state and the correct answer are never included.</p><pre>${esc(run.meta.system_prompt)}</pre>
    <h4>Task message</h4><pre>${esc(run.objective || "")}</pre>` : `<p class="muted">Not started.</p>`;
}

// ---------------------------------------------------------------------------
// Playback and chrome
// ---------------------------------------------------------------------------
function stopPlay() { if (S.playTimer) { clearInterval(S.playTimer); S.playTimer = null; } renderPlayback(); }
function step(delta) {
  const run = S.runs[S.activeRun]; if (!run || !run.items.length) return;
  run.cursor = Math.max(0, Math.min(run.items.length - 1, run.cursor + delta));
  run.live = false; renderTrace();
}
function bindChrome() {
  $("#btn-run").onclick = runAll;
  $("#template").onchange = (e) => {
    if (!e.target.value) return;
    loadTemplate(e.target.value); e.target.value = ""; save(); renderAll();
    requestAnimationFrame(fit);
  };
  $("#btn-export").onclick = () => {
    const data = { graph: { nodes: S.nodes, edges: S.edges }, runs: S.runOrder.map((id) => S.runs[id]) };
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    a.download = `ecaa-studio-${new Date().toISOString().slice(0, 19).replace(/:/g, "")}.json`; a.click();
  };
  document.querySelectorAll(".tabs button").forEach((b) => b.onclick = () => { S.tab = b.dataset.tab; renderDetails(); });
  document.querySelectorAll("[data-pb]").forEach((b) => b.onclick = () => {
    const run = S.runs[S.activeRun]; if (!run) return;
    const a = b.dataset.pb;
    if (a === "first") { stopPlay(); run.cursor = 0; run.live = false; renderTrace(); }
    if (a === "prev") { stopPlay(); step(-1); }
    if (a === "next") { stopPlay(); step(1); }
    if (a === "live") { stopPlay(); run.cursor = run.items.length - 1; run.live = true; renderTrace(); }
    if (a === "play") {
      if (S.playTimer) return stopPlay();
      if (run.cursor >= run.items.length - 1) { run.cursor = -1; }
      run.live = false;
      const tick = () => {
        const r = S.runs[S.activeRun];
        if (!r || r.cursor >= r.items.length - 1) { stopPlay(); return; }
        step(1);
      };
      tick();
      S.playTimer = setInterval(tick, 900 / Number($("#pb-speed").value));
      renderPlayback();
    }
  });
  $("#pb-speed").onchange = () => { if (S.playTimer) { stopPlay(); $("#pb-play").click(); } };
  $("#pb-scrub").oninput = (e) => { const run = S.runs[S.activeRun]; if (!run) return; stopPlay(); run.cursor = +e.target.value; run.live = false; renderTrace(); };
  $("#modal-close").onclick = () => { $("#modal").hidden = true; };
  $("#modal").onclick = (e) => { if (e.target.id === "modal") $("#modal").hidden = true; };
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, select")) return;
    if (e.key === "ArrowRight") step(1);
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "Escape") $("#modal").hidden = true;
  });
  // resizable trace panel
  const sp = $("#splitter");
  sp.addEventListener("pointerdown", (ev) => {
    sp.setPointerCapture(ev.pointerId);
    const move = (e) => { const h = Math.min(window.innerHeight - 160, Math.max(120, window.innerHeight - e.clientY)); document.documentElement.style.setProperty("--trace-h", `${h}px`); };
    const up = () => { sp.removeEventListener("pointermove", move); sp.removeEventListener("pointerup", up); };
    sp.addEventListener("pointermove", move); sp.addEventListener("pointerup", up);
  });
}

boot().catch((e) => { document.body.innerHTML = `<pre style="padding:20px">Studio failed to start: ${esc(e)}</pre>`; });
