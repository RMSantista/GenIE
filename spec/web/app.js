/* GenIE SPA — production port of the design prototype (vanilla JS).
   Talks to the FastAPI backend: /api/v1/{models,keys,uploads,runs,downloads}. */

"use strict";

const API = "/api/v1";

// ── Icons (stroke = currentColor) ────────────────────────────────────────────
const ICON_PATHS = {
  Key: '<path d="M14 9a4 4 0 1 1-3.9 5l-5.6 5.6V21H7v-1.5h1.5V18H10v-1.5l4.1-4.1A4 4 0 0 1 14 9z"/><circle cx="16" cy="9" r="1"/>',
  Plus: '<path d="M12 5v14M5 12h14"/>',
  Link: '<path d="M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1"/><path d="M14 10a4 4 0 0 0-5.66 0l-3 3A4 4 0 0 0 11 18.66l1-1"/>',
  Folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  Db: '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
  Api: '<path d="M4 7l4 4-4 4M16 7l4 4-4 4M14 5l-4 14"/>',
  Upload: '<path d="M12 16V4M6 10l6-6 6 6M4 20h16"/>',
  Down: '<path d="M12 4v12M6 14l6 6 6-6M4 4h16"/>',
  Send: '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
  Stop: '<rect x="5" y="5" width="14" height="14" rx="1"/>',
  X: '<path d="M6 6l12 12M18 6L6 18"/>',
  Copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
  Check: '<path d="M4 12l5 5L20 6"/>',
  Lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  Spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
  Brain: '<path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-2 5 3 3 0 0 0 2 5v1a3 3 0 0 0 3 3"/><path d="M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 2 5 3 3 0 0 1-2 5v1a3 3 0 0 1-3 3"/><path d="M12 4v16"/>',
  Box: '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>',
  Eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  EyeOff: '<path d="M3 3l18 18"/><path d="M10.6 6.1A10 10 0 0 1 22 12s-1.4 2.7-4.1 4.7"/><path d="M6.2 6.2C3.5 8.2 2 12 2 12s3.5 7 10 7c1.8 0 3.5-.5 5-1.4"/><circle cx="12" cy="12" r="2.5"/>',
  Reload: '<path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/>',
  Chev: '<path d="M9 6l6 6-6 6"/>',
};

function icon(name, size = 14) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="icon" aria-hidden="true">${ICON_PATHS[name] || ""}</svg>`;
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ── Catalogs ─────────────────────────────────────────────────────────────────
const CONN_TYPES_IN = [
  { id: "url", label: "URL", icon: "Link", placeholder: "https://exemplo.com/relatorio.pdf" },
  { id: "path", label: "Pasta local", icon: "Folder", placeholder: "/home/voce/Documents/exames" },
  { id: "db", label: "Banco de dados", icon: "Db", placeholder: "sqlite:///dados.db ou postgres://host:5432/db" },
  { id: "api", label: "API REST", icon: "Api", placeholder: "https://api.servico.com/v1/exames" },
  { id: "upload", label: "Upload", icon: "Upload", placeholder: null },
];
const CONN_TYPES_OUT = [
  { id: "url", label: "URL (webhook)", icon: "Link", placeholder: "https://hooks.servico.com/genie/abc" },
  { id: "path", label: "Pasta local", icon: "Folder", placeholder: "/home/voce/Documents/saida" },
  { id: "db", label: "Banco de dados", icon: "Db", placeholder: "sqlite:///saida.db" },
  { id: "api", label: "API REST", icon: "Api", placeholder: "https://api.tabex.com/v2/exames" },
  { id: "download", label: "Download", icon: "Down", placeholder: null },
];
const AGENTS = [
  { id: "conector", name: "Conector", role: "I/O", desc: "Estabelece conexões de entrada e saída.", icon: "Link" },
  { id: "localizador", name: "Localizador", role: "Extração", desc: "Vasculha o conteúdo e extrai o que foi pedido.", icon: "Brain" },
  { id: "organizador", name: "Organizador", role: "Formato", desc: "Estrutura os dados no formato de saída exigido.", icon: "Box" },
];
const KEY_PLACEHOLDERS = { openai: "sk-…", anthropic: "sk-ant-…", google: "AIza…" };

// ── State ────────────────────────────────────────────────────────────────────
const state = {
  models: [],
  modelId: null,
  input: { type: "url", target: "", user: "", password: "", token: "", files: [] },
  output: { type: "api", target: "", user: "", password: "", token: "" },
  run: freshRun(),
  eventSource: null,
};

function freshRun() {
  const agents = {};
  AGENTS.forEach((a) => { agents[a.id] = { status: "idle", progress: 0, message: "" }; });
  return { status: "idle", jobId: null, agents, logs: [], result: null, resultTab: "table" };
}

function currentModel() {
  return state.models.find((m) => m.id === state.modelId) || null;
}

// ── API helpers ──────────────────────────────────────────────────────────────
async function apiJson(path, options = {}) {
  const response = await fetch(API + path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail ? String(data.detail) : `HTTP ${response.status}`);
  }
  return data;
}

async function loadModels() {
  state.models = await apiJson("/models");
  if (!state.modelId || !currentModel()) state.modelId = state.models[0]?.id || null;
}

// ── Topbar + model section ───────────────────────────────────────────────────
function renderModelArea() {
  const select = document.getElementById("model-select");
  select.innerHTML = state.models
    .map((m) => `<option value="${esc(m.id)}" ${m.id === state.modelId ? "selected" : ""}>${esc(m.provider_label)} · ${esc(m.label)}</option>`)
    .join("");

  const model = currentModel();
  const hasKey = !!model?.has_key;
  document.getElementById("model-note").textContent = model?.note || "";

  const keyState = document.getElementById("key-state");
  keyState.className = `key-state ${hasKey ? "" : "missing"}`;
  keyState.innerHTML = `<span class="dot"></span>${icon("Lock", 11)} ${hasKey ? "chave configurada" : "sem chave"}`;

  const manageBtn = document.getElementById("manage-key-btn");
  manageBtn.innerHTML = hasKey
    ? `${icon("Key", 12)} Gerenciar chave`
    : `${icon("Plus", 12)} Nova API Key`;

  const top = document.getElementById("top-key-state");
  top.title = hasKey ? "Chave configurada com segurança" : "Sem chave para este modelo";
  top.innerHTML = `
    <span style="width:7px;height:7px;border-radius:99px;background:${hasKey ? "var(--green)" : "var(--amber)"};
      box-shadow:0 0 0 3px ${hasKey ? "oklch(0.78 0.15 155 / 0.18)" : "oklch(0.82 0.14 80 / 0.18)"}"></span>
    <span>${esc(model?.provider_label || "")} <b>${esc(model?.label || "")}</b></span>`;
}

// ── Connection sections (02 / 04) ────────────────────────────────────────────
function renderConnSection(kind) {
  const isInput = kind === "in";
  const TYPES = isInput ? CONN_TYPES_IN : CONN_TYPES_OUT;
  const value = isInput ? state.input : state.output;
  const section = document.getElementById(isInput ? "section-input" : "section-output");
  const type = TYPES.find((t) => t.id === value.type) || TYPES[0];
  const needsCreds = value.type === "db";
  const needsToken = value.type === "api";
  const isUpload = isInput && value.type === "upload";
  const isDownload = !isInput && value.type === "download";

  const options = TYPES
    .map((t) => `<option value="${t.id}" ${t.id === value.type ? "selected" : ""}>${esc(t.label)}</option>`)
    .join("");

  let composite;
  if (!isUpload && !isDownload) {
    composite = `
      <div class="composite" style="grid-template-columns:170px 1fr">
        <select data-role="type" aria-label="Tipo">${options}</select>
        <input class="mono" data-role="target" placeholder="${esc(type.placeholder || "")}" value="${esc(value.target)}" />
      </div>`;
  } else {
    composite = `
      <div class="composite" style="grid-template-columns:170px 1fr">
        <select data-role="type" aria-label="Tipo">${options}</select>
        <div style="padding:10px 12px;color:var(--fg-3);font-family:var(--font-mono);font-size:12px">
          ${isUpload ? "arraste arquivos na área abaixo →" : "GenIE devolverá o arquivo no navegador"}
        </div>
      </div>`;
  }

  let aux = "";
  if (needsCreds) {
    aux = `
      <div class="field-row cols-2">
        <div class="field"><label>Usuário</label>
          <input class="ctl mono" data-role="user" placeholder="admin" value="${esc(value.user)}" /></div>
        <div class="field"><label>Senha</label>
          <div class="composite" style="grid-template-columns:1fr 38px">
            <input class="mono" data-role="password" type="password" autocomplete="off" spellcheck="false" placeholder="••••••••" value="${esc(value.password)}" />
            <button type="button" data-role="toggle-pass" aria-label="Mostrar"
              style="background:transparent;border:0;color:var(--fg-3);display:grid;place-items:center;border-left:1px solid var(--line)">${icon("Eye")}</button>
          </div></div>
      </div>`;
  }
  if (needsToken) {
    aux = `
      <div class="field"><label>Bearer token / chave de acesso</label>
        <div class="composite" style="grid-template-columns:1fr 38px">
          <input class="mono" data-role="token" type="password" autocomplete="off" spellcheck="false" placeholder="sk_••••••••••••" value="${esc(value.token)}" />
          <button type="button" data-role="toggle-pass" aria-label="Mostrar"
            style="background:transparent;border:0;color:var(--fg-3);display:grid;place-items:center;border-left:1px solid var(--line)">${icon("Eye")}</button>
        </div></div>`;
  }
  if (isUpload) {
    const fileRows = (value.files || [])
      .map((f, i) => `
        <div class="file-row">${icon("Box", 12)}<span class="name">${esc(f.name)}</span>
          <span class="size">${fmtSize(f.size)}</span>
          <button class="x" data-remove="${i}" aria-label="Remover">${icon("X", 12)}</button>
        </div>`)
      .join("");
    aux = `
      <div class="dropzone" data-role="dropzone">
        <div class="ico">${icon("Upload", 18)}</div>
        <div class="label">
          <div class="t">Arraste arquivos aqui ou clique para escolher</div>
          <div class="s">.pdf .csv .xlsx .json .txt .html — múltiplos arquivos suportados</div>
        </div>
        <input type="file" multiple style="display:none" data-role="file-input" />
      </div>
      ${value.files?.length ? `<div class="files">${fileRows}</div>` : ""}`;
  }
  if (isDownload) {
    aux = `
      <div class="dropzone" style="cursor:default">
        <div class="ico">${icon("Down", 18)}</div>
        <div class="label">
          <div class="t">Saída como arquivo de download</div>
          <div class="s">JSON e CSV — links assinados, válidos por 15 minutos</div>
        </div>
      </div>`;
  }

  let tokens = "";
  if (value.target || isUpload || isDownload) {
    const chips = [`<span class="tok">${esc(type.label)}</span>`];
    if (value.user) chips.push(`<span class="tok">user=${esc(value.user)}</span>`);
    if (value.password) chips.push('<span class="tok">pass=••••</span>');
    if (value.token) chips.push('<span class="tok">token=••••</span>');
    if (isUpload && value.files?.length) chips.push(`<span class="tok">${value.files.length} arquivo(s)</span>`);
    tokens = `<div class="tokens">${chips.join("")}</div>`;
  }

  section.innerHTML = `
    <div class="section-head">
      <div class="num">${isInput ? "02" : "04"}</div>
      <div class="label">${isInput ? "Origem dos dados (entrada)" : "Destino dos dados (saída)"}</div>
      <div class="hint">conector</div>
    </div>
    ${composite}${aux}${tokens}`;

  wireConnSection(section, kind);
}

function wireConnSection(section, kind) {
  const isInput = kind === "in";
  const value = isInput ? state.input : state.output;

  section.querySelector('[data-role="type"]').addEventListener("change", (e) => {
    Object.assign(value, { type: e.target.value, target: "", user: "", password: "", token: "" });
    if (isInput) value.files = [];
    renderConnSection(kind);
    renderActionBar();
  });

  const bind = (role, key) => {
    const el = section.querySelector(`[data-role="${role}"]`);
    if (el) el.addEventListener("input", (e) => { value[key] = e.target.value; renderActionBar(); });
  };
  bind("target", "target");
  bind("user", "user");
  bind("password", "password");
  bind("token", "token");

  const toggle = section.querySelector('[data-role="toggle-pass"]');
  if (toggle) {
    toggle.addEventListener("click", () => {
      const field = section.querySelector('[data-role="password"], [data-role="token"]');
      const show = field.type === "password";
      field.type = show ? "text" : "password";
      toggle.innerHTML = show ? icon("EyeOff") : icon("Eye");
    });
  }

  const dropzone = section.querySelector('[data-role="dropzone"]');
  if (dropzone) {
    const fileInput = section.querySelector('[data-role="file-input"]');
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => e.preventDefault());
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      value.files = [...value.files, ...e.dataTransfer.files];
      renderConnSection(kind); renderActionBar();
    });
    fileInput.addEventListener("change", (e) => {
      value.files = [...value.files, ...e.target.files];
      renderConnSection(kind); renderActionBar();
    });
  }
  section.querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      value.files = value.files.filter((_, i) => i !== Number(btn.dataset.remove));
      renderConnSection(kind); renderActionBar();
    });
  });
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// ── Action bar ───────────────────────────────────────────────────────────────
function canRun() {
  const model = currentModel();
  const prompt = document.getElementById("prompt").value.trim();
  const hasInput = state.input.type === "upload" ? state.input.files.length > 0 : !!state.input.target.trim();
  return !!model?.has_key && hasInput && prompt.length > 0 && state.run.status !== "running" && state.run.status !== "starting";
}

function renderActionBar() {
  const model = currentModel();
  const inText = state.input.type + (state.input.target ? `:${state.input.target.slice(0, 24)}` : state.input.files?.length ? `(${state.input.files.length})` : "");
  const outText = state.output.type + (state.output.target ? `:${state.output.target.slice(0, 24)}` : "");
  document.getElementById("summary").innerHTML = `
    <span><b>${esc(model?.label || "—")}</b></span>
    <span>in <b>${esc(inText || "—")}</b></span>
    <span>out <b>${esc(outText || "—")}</b></span>`;

  const slot = document.getElementById("action-buttons");
  if (state.run.status === "running" || state.run.status === "starting") {
    slot.innerHTML = `<button class="btn" id="stop-btn">${icon("Stop", 12)} Interromper</button>`;
    document.getElementById("stop-btn").addEventListener("click", stopRun);
  } else {
    const clear = state.run.status !== "idle"
      ? `<button class="btn ghost" id="clear-btn">${icon("Reload", 12)} Limpar</button>` : "";
    slot.innerHTML = `${clear}
      <button class="btn primary" id="run-btn" ${canRun() ? "" : "disabled"}
        title="${currentModel()?.has_key ? "" : "Configure uma API Key para o modelo selecionado"}">
        ${icon("Send", 12)} Enviar requisição</button>`;
    document.getElementById("run-btn").addEventListener("click", startRun);
    const clearBtn = document.getElementById("clear-btn");
    if (clearBtn) clearBtn.addEventListener("click", () => { closeStream(); state.run = freshRun(); renderMonitor(); renderActionBar(); });
  }
}

// ── Monitor ──────────────────────────────────────────────────────────────────
function renderMonitor() {
  const monitor = document.getElementById("monitor");
  const run = state.run;

  if (run.status === "idle" && run.logs.length === 0) {
    monitor.innerHTML = `
      <div class="monitor-inner" style="grid-template-rows:1fr">
        <div class="monitor-empty"><div>
          <span class="badge">Monitor de agentes</span>
          <h2>Pronto para orquestrar</h2>
          <p>Três agentes — <b>Conector</b>, <b>Localizador</b> e <b>Organizador</b> — trabalham em sequência:
            o conector busca a fonte, o localizador extrai o que você pediu, o organizador formata e o conector
            entrega no destino.</p>
          <div class="agents" style="margin-top:24px">
            ${AGENTS.map((a) => `
              <div class="agent">
                <div class="agent-head"><div class="ico">${icon(a.icon)}</div><div class="name">${a.name}</div></div>
                <div class="desc">${a.desc}</div>
              </div>`).join("")}
          </div>
        </div></div>
      </div>`;
    return;
  }

  const statusLabel = { starting: "iniciando", running: "executando", done: "concluído", error: "erro", cancelled: "interrompido", idle: "ocioso" }[run.status] || run.status;
  const pillClass = run.status === "starting" ? "running" : run.status;
  const total = Math.round(AGENTS.reduce((s, a) => s + (run.agents[a.id].progress || 0), 0) / AGENTS.length);

  monitor.innerHTML = `
    <div class="monitor-inner" style="grid-template-rows:auto auto 1fr auto">
      <div class="monitor-head">
        <span class="title">Monitor de agentes</span>
        <span class="status-pill ${pillClass}"><span class="dot"></span>${statusLabel}</span>
        <div class="spacer"></div>
        <span class="meta" id="monitor-meta">job ${esc(run.jobId || "")} · ${run.logs.length} eventos · ${total}%</span>
      </div>
      <div class="agents" id="agents-row">${AGENTS.map(agentCardHtml).join("")}</div>
      <div class="monitor-body">
        <div class="panel">
          <div class="panel-head"><span>Log de execução</span></div>
          <div class="log" id="log">${run.logs.map(logLineHtml).join("")}</div>
        </div>
        <div id="output-slot">${run.result ? outputPreviewHtml() : ""}</div>
      </div>
    </div>`;

  const log = document.getElementById("log");
  log.scrollTop = log.scrollHeight;
  wireOutputPreview();
}

function agentCardHtml(agent) {
  const s = state.run.agents[agent.id];
  const tag = { idle: "aguardando", active: "executando", done: "concluído" }[s.status] || s.status;
  return `
    <div class="agent ${s.status}">
      <div class="agent-head">
        <div class="ico">${icon(agent.icon)}</div>
        <div style="display:flex;flex-direction:column;gap:0">
          <div class="name">${agent.name}</div><div class="role">${agent.role}</div>
        </div>
        <div class="status-tag">${tag}</div>
      </div>
      <div class="desc">${esc(s.message || agent.desc)}</div>
      <div class="progress"><span style="width:${s.progress || 0}%"></span></div>
    </div>`;
}

function logLineHtml(line) {
  return `
    <div class="line ${line.level || ""}">
      <span class="t">${esc(line.t)}</span>
      <span class="a ${esc(line.agent)}">${esc(line.agent)}</span>
      <span class="m">${esc(line.m)}</span>
    </div>`;
}

function outputPreviewHtml() {
  const result = state.run.result;
  if (!result) return "";
  const outType = (CONN_TYPES_OUT.find((t) => t.id === state.output.type) || {}).label || state.output.type;
  const target = result.delivered_to?.target || "—";
  const records = Array.isArray(result.records) ? result.records.filter((r) => r && typeof r === "object") : [];
  const isTabular = records.length > 0;
  const tab = isTabular ? state.run.resultTab : "json";

  const downloads = Object.entries(result.downloads || {})
    .map(([fmt, url]) => `<a class="dl" href="${esc(url)}" download>${icon("Down", 11)} ${esc(fmt.toUpperCase())}</a>`)
    .join("");

  let body;
  if (tab === "table" && isTabular) {
    const columns = [];
    records.forEach((r) => Object.keys(r).forEach((k) => { if (!k.startsWith("_") && !columns.includes(k)) columns.push(k); }));
    body = `
      <table class="result">
        <thead><tr>${columns.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead>
        <tbody>${records.map((r) => `
          <tr>${columns.map((c) => {
            const out = r._outOfRange?.[c] ? "v out-of-range" : "v";
            const cell = r[c] === null || r[c] === undefined ? "" : typeof r[c] === "object" ? JSON.stringify(r[c]) : String(r[c]);
            return `<td><span class="${out}">${esc(cell)}</span></td>`;
          }).join("")}</tr>`).join("")}
        </tbody>
      </table>`;
  } else {
    body = `<pre style="margin:0;padding:12px 14px;font-family:var(--font-mono);font-size:11.5px;line-height:1.55;color:var(--fg-1);white-space:pre-wrap">${esc(JSON.stringify(result, null, 2))}</pre>`;
  }

  return `
    <div class="output">
      <div class="output-head">
        <span class="t">Saída entregue</span>
        <span class="target">${icon("Send", 11)}<span class="arrow">→</span>${esc(outType)} <span style="color:var(--fg-3)">·</span> ${esc(target)}</span>
        <div class="actions">
          ${downloads}
          <div class="toggle-group" style="padding:2px">
            <button class="opt" id="tab-table" aria-pressed="${tab === "table"}" ${isTabular ? "" : "disabled"}>Tabela</button>
            <button class="opt" id="tab-json" aria-pressed="${tab === "json"}">JSON</button>
          </div>
          <button class="btn ghost icon-only" id="copy-json" title="Copiar JSON">${icon("Copy")}</button>
        </div>
      </div>
      <div class="output-body">${body}</div>
    </div>`;
}

function wireOutputPreview() {
  const tabTable = document.getElementById("tab-table");
  const tabJson = document.getElementById("tab-json");
  const copyBtn = document.getElementById("copy-json");
  if (tabTable) tabTable.addEventListener("click", () => { state.run.resultTab = "table"; renderMonitor(); });
  if (tabJson) tabJson.addEventListener("click", () => { state.run.resultTab = "json"; renderMonitor(); });
  if (copyBtn) copyBtn.addEventListener("click", () => {
    navigator.clipboard?.writeText(JSON.stringify(state.run.result, null, 2));
    copyBtn.innerHTML = icon("Check");
    setTimeout(() => { copyBtn.innerHTML = icon("Copy"); }, 1500);
  });
}

// ── Run engine (real backend) ────────────────────────────────────────────────
function closeStream() {
  if (state.eventSource) { state.eventSource.close(); state.eventSource = null; }
}

async function startRun() {
  if (!canRun()) return;
  closeStream();
  state.run = freshRun();
  state.run.status = "starting";
  renderActionBar();
  renderMonitor();

  const prompt = document.getElementById("prompt").value.trim();
  const format = document.getElementById("format").value;

  try {
    let uploadId = null;
    if (state.input.type === "upload") {
      const form = new FormData();
      state.input.files.forEach((file) => form.append("files", file));
      pushLocalLog("sistema", `Enviando ${state.input.files.length} arquivo(s)…`);
      const upload = await apiJson("/uploads", { method: "POST", body: form });
      uploadId = upload.upload_id;
      pushLocalLog("sistema", `Upload concluído (${upload.files.length} arquivo(s))`, "ok");
    }

    const body = {
      model_id: state.modelId,
      input: {
        type: state.input.type,
        target: state.input.target,
        user: state.input.user,
        password: state.input.password,
        token: state.input.token,
        upload_id: uploadId,
      },
      prompt,
      output: {
        type: state.output.type,
        target: state.output.target,
        user: state.output.user,
        password: state.output.password,
        token: state.output.token,
      },
      format,
    };

    const created = await apiJson("/runs", { method: "POST", body: JSON.stringify(body) });
    state.run.jobId = created.job_id;
    state.run.status = "running";
    state.run.agents.conector.status = "active";
    renderActionBar();
    subscribe(created.job_id);
  } catch (error) {
    state.run.status = "error";
    pushLocalLog("sistema", String(error.message || error), "error");
    renderActionBar();
    renderMonitor();
  }
}

function subscribe(jobId) {
  const source = new EventSource(`${API}/runs/${jobId}/events`);
  state.eventSource = source;

  source.onmessage = (message) => {
    let event;
    try { event = JSON.parse(message.data); } catch { return; }
    applyEvent(event);
  };
  source.onerror = async () => {
    if (state.run.status !== "running") { closeStream(); return; }
    // EventSource auto-reconnects with Last-Event-ID; double-check job state.
    try {
      const info = await apiJson(`/runs/${jobId}`);
      if (info.status !== "running" && info.status !== "queued") {
        closeStream();
        state.run.status = info.status;
        if (info.result) state.run.result = info.result;
        if (info.error) pushLocalLog("sistema", info.error, "error");
        renderActionBar(); renderMonitor();
      }
    } catch { /* transient; let EventSource retry */ }
  };
}

function applyEvent(event) {
  const run = state.run;
  const agents = run.agents;

  if (agents[event.agent]) {
    const agent = agents[event.agent];
    if (event.type === "done") {
      agent.status = "done"; agent.progress = 100;
      if (event.message) agent.message = event.message;
    } else {
      if (agent.status !== "done") agent.status = "active";
      if (typeof event.progress === "number") agent.progress = event.progress;
      if (event.message) agent.message = event.message;
    }
  }

  if (event.message) {
    run.logs.push({ t: event.ts, agent: event.agent, m: event.message, level: event.level || "" });
  }

  if (event.type === "finish") {
    run.status = event.status || "done";
    run.result = event.result || null;
    closeStream();
    renderActionBar();
  } else if (event.type === "error") {
    run.status = event.status || "error";
    closeStream();
    renderActionBar();
  }

  renderMonitor();
}

function pushLocalLog(agent, message, level = "") {
  const t = new Date().toLocaleTimeString("pt-BR", { hour12: false }).slice(0, 8);
  state.run.logs.push({ t, agent, m: message, level });
  renderMonitor();
}

async function stopRun() {
  const jobId = state.run.jobId;
  closeStream();
  if (jobId) {
    try {
      const info = await apiJson(`/runs/${jobId}/cancel`, { method: "POST" });
      state.run.status = info.status || "cancelled";
    } catch { state.run.status = "cancelled"; }
  } else {
    state.run.status = "idle";
  }
  renderActionBar();
  renderMonitor();
}

// ── API Key modal ────────────────────────────────────────────────────────────
function openKeyModal() {
  const model = currentModel();
  if (!model) return;
  const root = document.getElementById("modal-root");
  const masked = model.masked_key || "";

  root.innerHTML = `
    <div class="modal-back" id="modal-back">
      <div class="modal" id="modal">
        <h3>API Key — ${esc(model.provider_label)} · ${esc(model.label)}</h3>
        <p>A chave é enviada uma única vez ao servidor GenIE, cifrada com AES-256-GCM e
          <b>usada apenas</b> em chamadas do GenIE para o provedor do modelo.
          Ela nunca volta ao navegador, não aparece em logs nem na saída entregue.</p>
        ${model.has_key ? `
          <div class="field" style="margin-bottom:12px">
            <label>Chave atual (mascarada)</label>
            <div class="ctl mono" style="display:flex;align-items:center;gap:8px">
              ${icon("Lock", 11)} ${esc(masked)}
              <span style="margin-left:auto;font-size:10px;color:var(--fg-3)">armazenada cifrada</span>
            </div>
          </div>` : ""}
        <div class="field">
          <label>${model.has_key ? "Substituir por nova chave" : "Cole a chave do provedor"}</label>
          <input class="ctl mono" id="key-input" type="password" autocomplete="off" spellcheck="false"
            placeholder="${esc(KEY_PLACEHOLDERS[model.provider] || "chave")}" />
        </div>
        <div class="hint-row">${icon("Lock", 11)} armazenamento cifrado no servidor · escopo: somente requisições do GenIE</div>
        <div class="error-row" id="key-error"></div>
        <div class="row">
          ${model.has_key ? `<button class="btn" id="key-remove" style="margin-right:auto;color:var(--red)">Remover</button>` : ""}
          <button class="btn ghost" id="key-cancel">Cancelar</button>
          <button class="btn primary" id="key-save" disabled>${icon("Check", 12)} Salvar</button>
        </div>
      </div>
    </div>`;

  const back = document.getElementById("modal-back");
  const input = document.getElementById("key-input");
  const saveBtn = document.getElementById("key-save");
  const errorRow = document.getElementById("key-error");
  const close = () => { root.innerHTML = ""; };

  back.addEventListener("click", close);
  document.getElementById("modal").addEventListener("click", (e) => e.stopPropagation());
  document.getElementById("key-cancel").addEventListener("click", close);
  input.addEventListener("input", () => { saveBtn.disabled = !input.value.trim(); });
  input.focus();

  saveBtn.addEventListener("click", async () => {
    saveBtn.disabled = true;
    saveBtn.innerHTML = `<span class="spin"></span> Validando…`;
    errorRow.classList.remove("show");
    try {
      await apiJson("/keys", {
        method: "POST",
        body: JSON.stringify({ provider: model.provider, key: input.value.trim(), validate_key: true }),
      });
      input.value = "";
      close();
      await loadModels();
      renderModelArea(); renderActionBar();
    } catch (error) {
      errorRow.textContent = String(error.message || error);
      errorRow.classList.add("show");
      saveBtn.innerHTML = `${icon("Check", 12)} Salvar`;
      saveBtn.disabled = false;
    }
  });

  const removeBtn = document.getElementById("key-remove");
  if (removeBtn) {
    removeBtn.addEventListener("click", async () => {
      try {
        await apiJson(`/keys/${encodeURIComponent(model.provider)}`, { method: "DELETE" });
        close();
        await loadModels();
        renderModelArea(); renderActionBar();
      } catch (error) {
        errorRow.textContent = String(error.message || error);
        errorRow.classList.add("show");
      }
    });
  }
}

// ── Example ──────────────────────────────────────────────────────────────────
function loadExample() {
  state.input = { type: "upload", target: "", user: "", password: "", token: "", files: state.input.type === "upload" ? state.input.files : [] };
  document.getElementById("prompt").value =
    "Extraia, para cada exame encontrado nos arquivos enviados, os campos: Data, Nome do Exame, Resultado e Valor de Referência. Ignore cabeçalhos, rodapés e dados de contato do laboratório.";
  state.output = { type: "download", target: "", user: "", password: "", token: "" };
  document.getElementById("format").value =
    'Gere um registro JSON por exame com os campos:\n{\n  "data": "YYYY-MM-DD",\n  "exame": "<nome>",\n  "resultado": "<valor + unidade>",\n  "referencia": "<faixa>"\n}';
  renderConnSection("in");
  renderConnSection("out");
  renderActionBar();
}

// ── Boot ─────────────────────────────────────────────────────────────────────
async function boot() {
  document.getElementById("model-select").addEventListener("change", (e) => {
    state.modelId = e.target.value;
    renderModelArea(); renderActionBar();
  });
  document.getElementById("manage-key-btn").addEventListener("click", openKeyModal);
  document.getElementById("example-btn").addEventListener("click", loadExample);
  document.getElementById("prompt").addEventListener("input", renderActionBar);
  document.querySelectorAll("[data-icon]").forEach((el) => { el.innerHTML = icon(el.dataset.icon, 11); });

  renderConnSection("in");
  renderConnSection("out");
  renderMonitor();

  try {
    await loadModels();
  } catch (error) {
    pushLocalLog("sistema", `Falha ao carregar modelos: ${error.message || error}`, "error");
  }
  renderModelArea();
  renderActionBar();
}

boot();
