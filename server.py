#!/usr/bin/env python3
"""
Cambium Import Details Tool
Run: python3 server.py
Open: http://localhost:8000
Password: hazique123
"""

import json, csv, io, os, copy
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import pandas as pd

# ── Load & normalize data ──────────────────────────────────────────────────────
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Cambium_Import_Details.xlsx")
DATA_FILE  = os.path.join(os.path.dirname(__file__), "data.json")

def sanitize(data):
    """Replace NaN/Inf with safe values so json.dumps never outputs NaN."""
    import math
    clean = []
    for row in data:
        new_row = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                new_row[k] = ""
            else:
                new_row[k] = v
        clean.append(new_row)
    return clean

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
        return sanitize(data)
    df = pd.read_excel(EXCEL_PATH, header=1)
    df["Brand"] = df["Brand"].str.strip().str.title()
    df["Asin"]  = df["Asin"].fillna("")
    df["SR NO"] = range(1, len(df) + 1)
    data = df.to_dict(orient="records")
    data = sanitize(data)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)
    return data

DB: list = load_data()
UNDO_STACK: list = []
REDO_STACK: list = []

def push_undo():
    UNDO_STACK.append(copy.deepcopy(DB))
    REDO_STACK.clear()
    if len(UNDO_STACK) > 50:
        UNDO_STACK.pop(0)

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(DB, f)

# ── HTML ───────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cambium Import Details</title>
<style>
  :root{
    --bg:#07090f;--surface:#0e1118;--surface2:#131825;
    --accent:#60a5fa;--accent2:#818cf8;--accent3:#06b6d4;--danger:#f87171;
    --success:#34d399;--warn:#fbbf24;--text:#e2e8f0;
    --text2:#94a3b8;--text3:#cbd5e1;--border:#1e2a45;--border2:rgba(96,165,250,.25);
    --row-hover:#0f1520;--highlight:#fde047;
    --glow:rgba(96,165,250,.2);--glow2:rgba(129,140,248,.15);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}

  /* ── LOGIN ── */
  #loginScreen{display:flex;align-items:center;justify-content:center;min-height:100vh;
    background:linear-gradient(135deg,#0f1117 0%,#1a1d40 100%)}
  .loginBox{background:linear-gradient(160deg,#0e1118,#131825);border:1px solid rgba(96,165,250,.2);border-radius:20px;
    padding:48px 56px;text-align:center;max-width:400px;width:90%;
    box-shadow:0 32px 80px rgba(0,0,0,.7),0 0 80px rgba(96,165,250,.06)}
  .loginBox h1{font-size:2rem;margin-bottom:6px;font-weight:800;
    background:linear-gradient(135deg,var(--accent),var(--accent2),var(--accent3));
    -webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .loginBox p{color:var(--text2);margin-bottom:32px;font-size:.9rem}
  .loginBox input{width:100%;padding:12px 16px;border-radius:8px;border:1px solid var(--border);
    background:var(--bg);color:var(--text);font-size:1rem;margin-bottom:16px;outline:none;transition:.2s}
  .loginBox input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(79,142,247,.2)}
  .loginBox button{width:100%;padding:12px;border-radius:8px;border:none;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    color:#fff;font-size:1rem;font-weight:600;cursor:pointer;transition:.2s}
  .loginBox button:hover{opacity:.9;transform:translateY(-1px)}
  #loginError{color:var(--danger);font-size:.85rem;margin-top:8px;min-height:20px}
  .lockIcon{font-size:3rem;margin-bottom:16px}

  /* ── MAIN APP ── */
  #app{display:none}
  header{background:linear-gradient(135deg,#060810 0%,#0b0e18 100%);border-bottom:1px solid rgba(99,102,241,.2);box-shadow:0 1px 0 rgba(99,102,241,.1),0 8px 32px rgba(0,0,0,.6);backdrop-filter:blur(12px);
    padding:0 24px;height:60px;display:flex;align-items:center;justify-content:space-between;
    position:sticky;top:0;z-index:100}
  header .logo{font-size:1.15rem;font-weight:700;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    -webkit-background-clip:text;-webkit-text-fill-color:transparent}
  header .meta{font-size:.8rem;color:var(--text2)}
  .hBtns{display:flex;gap:8px;align-items:center}
  .hBtn{padding:8px 16px;border-radius:9px;border:1px solid var(--border2);
    background:rgba(255,255,255,.04);color:var(--text3);font-size:.8rem;cursor:pointer;
    transition:.2s;white-space:nowrap;font-weight:500;letter-spacing:.02em}
  .hBtn:hover{border-color:var(--accent);color:var(--accent);background:rgba(99,102,241,.08);transform:translateY(-1px)}
  .hBtn.primary{background:linear-gradient(135deg,var(--accent),var(--accent2));
    border:none;color:#fff;font-weight:700;box-shadow:0 4px 15px var(--glow)}
  .hBtn.primary:hover{opacity:.92;color:#fff;transform:translateY(-2px);box-shadow:0 6px 20px var(--glow)}
  .hBtn.export-btn{border-color:rgba(6,182,212,.3);color:var(--accent3);background:rgba(6,182,212,.05)}
  .hBtn.export-btn:hover{border-color:var(--accent3);background:rgba(6,182,212,.12);transform:translateY(-1px)}
  .hBtn.danger{border-color:rgba(244,63,94,.3);color:var(--danger);background:rgba(244,63,94,.05)}
  .hBtn.danger:hover{background:rgba(244,63,94,.15);border-color:var(--danger);transform:translateY(-1px)}

  /* ── TOOLBAR ── */
  .toolbar{padding:10px 24px;background:rgba(6,8,16,.9);border-bottom:1px solid var(--border);backdrop-filter:blur(12px);
    display:flex;gap:8px;align-items:center;flex-wrap:wrap;position:sticky;top:60px;z-index:90}
  .toolbar input[type=text]{padding:8px 16px;border-radius:9px;border:1px solid var(--border2);
    background:rgba(96,165,250,.06);color:var(--text);font-size:.84rem;width:240px;outline:none;transition:.2s}
  .toolbar input[type=text]:focus{border-color:var(--accent);background:rgba(96,165,250,.1);box-shadow:0 0 0 3px rgba(96,165,250,.15)}
  .toolbar input[type=text]::placeholder{color:var(--text2)}
  .filter-wrap{display:flex;flex-direction:column;gap:2px}
  .filter-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.09em;
    color:var(--accent2);padding:0 2px;opacity:.85}
  .toolbar select{padding:7px 32px 7px 12px;border-radius:9px;border:1px solid var(--border2);
    background:#0d1526;color:var(--text);font-size:.83rem;font-weight:500;
    outline:none;cursor:pointer;transition:.2s;
    appearance:none;-webkit-appearance:none;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24'%3E%3Cpath fill='%2360a5fa' d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
    background-repeat:no-repeat;background-position:right 8px center;
    min-width:140px}
  .toolbar select:hover{border-color:var(--accent);background-color:#111d35;color:#fff}
  .toolbar select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(96,165,250,.15);color:#fff}
  .toolbar select option{background:#0d1526;color:var(--text);padding:8px}
  .sep{width:1px;height:28px;background:var(--border);margin:0 4px}
  .badge{padding:5px 12px;border-radius:20px;font-size:.75rem;font-weight:700;
    background:rgba(96,165,250,.12);color:var(--accent);border:1px solid rgba(96,165,250,.25);letter-spacing:.02em}

  /* ── STATS BAR ── */
  .statsBar{display:flex;gap:10px;padding:12px 24px;background:rgba(6,8,16,.7);
    border-bottom:1px solid var(--border);overflow-x:auto;backdrop-filter:blur(4px)}
  .statCard{background:linear-gradient(135deg,rgba(255,255,255,.04),rgba(255,255,255,.01));
    border:1px solid rgba(96,165,250,.15);border-radius:12px;
    padding:12px 20px;min-width:160px;flex-shrink:0;transition:.25s;position:relative;overflow:hidden;cursor:default}
  .statCard:hover{border-color:rgba(96,165,250,.4);transform:translateY(-2px);
    box-shadow:0 8px 28px rgba(96,165,250,.12);background:linear-gradient(135deg,rgba(96,165,250,.07),rgba(129,140,248,.03))}
  .statCard .label{font-size:.68rem;color:var(--text2);text-transform:uppercase;letter-spacing:.1em;font-weight:600}
  .statCard .val{font-size:1.35rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:4px;line-height:1}
  .statCard .sub{font-size:.71rem;color:var(--text2);margin-top:4px;opacity:.8}

  /* ── TABLE WRAPPER ── */
  .tableWrap{overflow:auto;max-height:calc(100vh - 240px);padding:0 24px 24px}
  table{width:100%;border-collapse:collapse;font-size:.84rem;min-width:900px}
  thead th{background:rgba(6,8,16,.95);backdrop-filter:blur(12px);position:sticky;top:0;z-index:10;
    padding:13px 14px;text-align:left;font-size:.72rem;font-weight:700;
    text-transform:uppercase;letter-spacing:.1em;color:var(--text2);
    border-bottom:1px solid rgba(99,102,241,.3);white-space:nowrap;cursor:pointer;user-select:none;
    transition:.2s}
  thead th:hover{color:var(--accent);background:rgba(99,102,241,.05)}
  thead th:hover{color:var(--accent)}
  thead th .sortIcon{margin-left:5px;opacity:.5}
  thead th.asc .sortIcon::after{content:"▲"}
  thead th.desc .sortIcon::after{content:"▼"}
  thead th:not(.asc):not(.desc) .sortIcon::after{content:"⇅"}

  tbody tr{border-bottom:1px solid rgba(30,36,64,.8);transition:.2s}
  tbody tr:hover{background:linear-gradient(90deg,rgba(99,102,241,.06),rgba(99,102,241,.02));
    box-shadow:inset 3px 0 0 var(--accent)}
  tbody tr:nth-child(even){background:rgba(255,255,255,.01)}
  tbody tr:nth-child(even):hover{background:linear-gradient(90deg,rgba(99,102,241,.07),rgba(99,102,241,.02))}
  tbody tr.selected{background:rgba(79,142,247,.12);border-left:3px solid var(--accent)}
  tbody tr.edited{background:rgba(243,156,18,.06)}
  tbody tr.new-row{background:rgba(46,204,113,.06)}

  td{padding:10px 14px;vertical-align:middle;position:relative}
  td.editable{cursor:text}
  td.editable:hover::after{content:"✎";position:absolute;right:6px;top:50%;
    transform:translateY(-50%);font-size:.7rem;color:var(--accent);opacity:.6}
  td input.cellInput{width:100%;background:var(--bg);border:1px solid var(--accent);
    border-radius:4px;color:var(--text);padding:3px 6px;font-size:.84rem;outline:none;font-family:inherit}

  .srNo{color:var(--text2);font-size:.8rem;width:50px}
  .brand-badge{display:inline-block;padding:4px 12px;border-radius:8px;font-size:.73rem;font-weight:700;letter-spacing:.04em;border:1px solid transparent}
  .textCell{text-align:center}
  .empty-cell{color:var(--text2);opacity:.3;font-size:.8rem}
  .bl-badge{display:inline-block;padding:4px 12px;border-radius:8px;font-size:.78rem;font-weight:600;
    background:linear-gradient(135deg,rgba(124,111,255,.25),rgba(124,111,255,.1));
    color:#a89fff;border:1px solid rgba(124,111,255,.3);letter-spacing:.02em;
    box-shadow:0 2px 8px rgba(124,111,255,.15)}
  .eta-badge{display:inline-block;padding:4px 12px;border-radius:8px;font-size:.78rem;font-weight:600;
    background:linear-gradient(135deg,rgba(46,204,113,.2),rgba(46,204,113,.08));
    color:#5de6a0;border:1px solid rgba(46,204,113,.25);letter-spacing:.02em;
    box-shadow:0 2px 8px rgba(46,204,113,.12)}
  .eta-td{min-width:160px}
  .eta-wrap{display:flex;flex-direction:column;align-items:center;gap:4px}
  .eta-picker{width:100%;padding:5px 8px;border-radius:7px;border:1px solid var(--border);
    background:rgba(52,211,153,.08);color:var(--text);font-size:.78rem;outline:none;
    cursor:pointer;transition:.2s;text-align:center;font-family:inherit}
  .eta-picker:hover{border-color:var(--success);background:rgba(52,211,153,.15)}
  .eta-picker:focus{border-color:var(--success);box-shadow:0 0 0 3px rgba(52,211,153,.2);background:rgba(52,211,153,.15)}
  .eta-picker::-webkit-calendar-picker-indicator{filter:invert(.7) sepia(1) saturate(2) hue-rotate(100deg);cursor:pointer;opacity:.8}
  .eta-picker::-webkit-calendar-picker-indicator:hover{opacity:1}
  .brand-audio{background:linear-gradient(135deg,rgba(79,142,247,.25),rgba(79,142,247,.1));color:#7ab3ff;box-shadow:0 2px 8px rgba(79,142,247,.15)}
  .brand-nexlev{background:linear-gradient(135deg,rgba(108,99,255,.25),rgba(108,99,255,.1));color:#a09fff;box-shadow:0 2px 8px rgba(108,99,255,.15)}
  .brand-tonor{background:linear-gradient(135deg,rgba(46,204,113,.25),rgba(46,204,113,.1));color:#68e09a;box-shadow:0 2px 8px rgba(46,204,113,.15)}
  .brand-white{background:linear-gradient(135deg,rgba(243,156,18,.25),rgba(243,156,18,.1));color:#f7bb6a;box-shadow:0 2px 8px rgba(243,156,18,.15)}
  .brand-other{background:rgba(148,148,148,.2);color:#bbb}

  .numCell{text-align:center;font-variant-numeric:tabular-nums;font-weight:600;letter-spacing:.03em}
  .numCell.zero{color:var(--text2);opacity:.5}
  .numCell.high{color:var(--success);font-weight:600}
  .numCell.medium{color:var(--warn)}
  .numCell.low{color:var(--danger)}

  .asin-link{color:var(--accent);text-decoration:none;font-size:.8rem}
  .asin-link:hover{text-decoration:underline}

  /* row actions */
  .rowActions{display:flex;gap:4px;opacity:0;transition:.2s}
  tr:hover .rowActions{opacity:1}
  .remarksTd:hover .rowActions{opacity:1}
  .rowBtn{padding:3px 8px;border-radius:5px;border:none;cursor:pointer;font-size:.72rem;font-weight:600;transition:.15s}
  .rowBtn.del{background:rgba(231,76,60,.15);color:var(--danger)}
  .rowBtn.del:hover{background:var(--danger);color:#fff}
  .rowBtn.dup{background:rgba(79,142,247,.15);color:var(--accent)}
  .rowBtn.dup:hover{background:var(--accent);color:#fff}
  .remarksTd{min-width:220px;max-width:320px;padding:6px 10px!important}
  .remarksWrap{display:flex;flex-direction:column;gap:5px}
  .remarksInput{width:100%;background:rgba(79,142,247,.06);border:1px solid var(--border);
    border-radius:7px;color:var(--text);padding:6px 10px;font-size:.82rem;font-family:inherit;
    resize:none;outline:none;transition:.2s;min-height:32px;line-height:1.4}
  .remarksInput:focus{border-color:var(--accent);background:rgba(79,142,247,.12);
    box-shadow:0 0 0 3px rgba(79,142,247,.15)}
  .remarksInput::placeholder{color:var(--text2);opacity:.5}
  .rowActions{display:flex;gap:4px;justify-content:flex-end}

  /* ── TOOLTIP ── */
  [data-tip]{position:relative}
  [data-tip]:hover::before{content:attr(data-tip);position:absolute;bottom:110%;left:50%;
    transform:translateX(-50%);background:#1e2235;color:var(--text);
    padding:6px 10px;border-radius:6px;font-size:.75rem;white-space:nowrap;z-index:999;
    border:1px solid var(--border);pointer-events:none}

  /* ── ADD ROW MODAL ── */
  .overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:200;
    align-items:center;justify-content:center}
  .overlay.open{display:flex}
  .modal{background:linear-gradient(160deg,#0e1118,#131825);border:1px solid rgba(96,165,250,.2);border-radius:18px;
    padding:36px;width:520px;max-width:95vw;box-shadow:0 32px 80px rgba(0,0,0,.7),0 0 60px rgba(96,165,250,.05)}
  .modal h2{font-size:1.15rem;margin-bottom:20px;color:var(--text)}
  .formGrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .formGrid .full{grid-column:1/-1}
  .formGroup label{display:block;font-size:.78rem;color:var(--text2);margin-bottom:5px;font-weight:600}
  .formGroup input,.formGroup select{width:100%;padding:9px 12px;border-radius:7px;
    border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:.9rem;outline:none;transition:.2s}
  .formGroup input:focus,.formGroup select:focus{border-color:var(--accent)}
  .modalBtns{display:flex;gap:10px;margin-top:20px;justify-content:flex-end}

  /* ── TOAST ── */
  #toast{position:fixed;bottom:28px;right:28px;z-index:500;display:flex;flex-direction:column;gap:8px}
  .toastItem{padding:12px 20px;border-radius:10px;font-size:.84rem;font-weight:600;
    animation:slideIn .3s cubic-bezier(.34,1.56,.64,1);max-width:320px;box-shadow:0 12px 32px rgba(0,0,0,.5);letter-spacing:.01em}
  .toastItem.ok{background:var(--success);color:#fff}
  .toastItem.err{background:var(--danger);color:#fff}
  .toastItem.info{background:var(--accent);color:#fff}
  @keyframes slideIn{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}

  /* ── EMPTY ── */
  .empty{text-align:center;padding:64px;color:var(--text2)}
  .empty .icon{font-size:3rem;margin-bottom:12px}

  /* scrollbar */
  ::-webkit-scrollbar{width:6px;height:6px}
  ::-webkit-scrollbar-track{background:var(--bg)}
  ::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
  ::-webkit-scrollbar-thumb:hover{background:var(--text2)}

  /* highlight search match */
  mark{background:rgba(255,215,0,.35);color:var(--highlight);border-radius:2px;padding:0 1px}

  @media(max-width:640px){
    .statsBar{gap:8px;padding:8px 12px}
    .toolbar{padding:10px 12px}
    .tableWrap{padding:0 8px 16px}
    header{padding:0 12px}
  }
</style>
</head>
<body>

<!-- LOGIN -->
<div id="loginScreen">
  <div class="loginBox">
    <div class="lockIcon">🔐</div>
    <h1>Cambium Tool</h1>
    <p>Import Details Management System</p>
    <input type="password" id="pwInput" placeholder="Enter password" autocomplete="current-password"
      onkeydown="if(event.key==='Enter')doLogin()">
    <button onclick="doLogin()">Sign In</button>
    <div id="loginError"></div>
  </div>
</div>

<!-- MAIN APP -->
<div id="app">
  <header>
    <div style="display:flex;align-items:center;gap:12px">
      <div style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:1rem;box-shadow:0 4px 12px var(--glow)">📦</div>
      <div>
        <div class="logo">Cambium Import Details</div>
        <div style="font-size:.68rem;color:var(--text2);letter-spacing:.08em;text-transform:uppercase">Inventory Management System</div>
      </div>
    </div>
    <span class="meta" id="headerMeta"></span>
    <div class="hBtns">
      <button class="hBtn primary" onclick="showAddModal()">＋ Add Row</button>
      <button class="hBtn export-btn" onclick="exportCSV()">⬇ Export CSV</button>
      <button class="hBtn danger" onclick="logout()">⏻ Logout</button>
    </div>
  </header>

  <div class="toolbar">
    <input type="text" id="searchBox" placeholder="🔍  Search any field…" oninput="applyFilters()">
    <div class="filter-wrap">
      <span class="filter-label">Brand</span>
      <select id="filterBrand" onchange="applyFilters()">
        <option value="">All Brands</option>
      </select>
    </div>
    <div class="filter-wrap">
      <span class="filter-label">ASIN Status</span>
      <select id="filterHasAsin" onchange="applyFilters()">
        <option value="">All ASIN Status</option>
        <option value="yes">Has ASIN</option>
        <option value="no">No ASIN</option>
      </select>
    </div>
    <div class="filter-wrap">
      <span class="filter-label">Inventory</span>
      <select id="filterInventory" onchange="applyFilters()">
        <option value="">All Inventory</option>
        <option value="zero">Zero Stock</option>
        <option value="low">Low (1–100)</option>
        <option value="medium">Medium (101–999)</option>
        <option value="high">High (1000+)</option>
      </select>
    </div>
    <div class="sep"></div>
    <button class="hBtn" onclick="clearFilters()">✕ Clear</button>
    <span class="badge" id="rowCount">— rows</span>
  </div>

  <div class="statsBar" id="statsBar"></div>

  <div class="tableWrap">
    <table id="mainTable">
      <thead>
        <tr id="headerRow"></tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="empty" id="emptyState" style="display:none">
      <div class="icon">🔍</div>
      <div>No matching records found</div>
    </div>
  </div>
</div>

<!-- ADD ROW MODAL -->
<div class="overlay" id="addModal">
  <div class="modal">
    <h2>➕ Add New Row</h2>
    <div class="formGrid">
      <div class="formGroup"><label>Brand</label>
        <select id="mBrand"></select></div>
      <div class="formGroup"><label>SKU</label>
        <input type="text" id="mSku" placeholder="FBA…"></div>
      <div class="formGroup"><label>ASIN</label>
        <input type="text" id="mAsin" placeholder="B0…"></div>
      <div class="formGroup"><label>Model Name</label>
        <input type="text" id="mModel"></div>
      <div class="formGroup"><label>Pipeline Inventory</label>
        <input type="number" id="mPipeline" value="0" min="0"></div>
      <div class="formGroup"><label>BL (Bill of Lading)</label>
        <input type="text" id="mBL" placeholder="e.g. BL-2024-001"></div>
      <div class="formGroup"><label>ETA (Date)</label>
        <input type="date" id="mETA"></div>
      <div class="formGroup"><label>Open Order</label>
        <input type="number" id="mOrder" value="0" min="0"></div>
      <div class="formGroup full"><label>Remarks</label>
        <input type="text" id="mRemarks" placeholder="Any notes or comments…"></div>
    </div>
    <div class="modalBtns">
      <button class="hBtn" onclick="closeModal()">Cancel</button>
      <button class="hBtn primary" onclick="addRow()">Add Row</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
const PASSWORD = "hazique123";
let rawData = [];
let filtered = [];
let sortCol = null, sortDir = 1;
const COLS = ["SR NO","Brand","SKU","Asin","Model Name","Pipeline Inventory","BL","ETA","Open Order"];
const ALL_EXPORT_COLS = ["SR NO","Brand","SKU","Asin","Model Name","Pipeline Inventory","BL","ETA","Open Order","Remarks"];
const EDITABLE = ["Brand","SKU","Asin","Model Name","Pipeline Inventory","Open Order"];
let undoStack = [], redoStack = [];

// ── AUTH ─────────────────────────────────────────────────────────────────────
function doLogin(){
  const pw = document.getElementById("pwInput").value;
  if(pw === PASSWORD){
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("app").style.display = "block";
    sessionStorage.setItem("auth","1");
    init();
  } else {
    document.getElementById("loginError").textContent = "❌ Wrong password. Try again.";
    document.getElementById("pwInput").value = "";
    document.getElementById("pwInput").focus();
  }
}
function logout(){
  sessionStorage.removeItem("auth");
  location.reload();
}
if(sessionStorage.getItem("auth")==="1"){
  document.getElementById("loginScreen").style.display="none";
  document.getElementById("app").style.display="block";
}

// ── INIT ─────────────────────────────────────────────────────────────────────
async function init(){
  const res = await fetch("/api/data");
  rawData = await res.json();
  buildBrandFilter();
  buildModalBrand();
  buildHeaders();
  applyFilters();
  updateStats();
  bindKeys();
  document.getElementById("app").style.display = "block";
}

function buildHeaders(){
  const tr = document.getElementById("headerRow");
  tr.innerHTML = "";
  COLS.forEach(col => {
    const th = document.createElement("th");
    th.innerHTML = col + ' <span class="sortIcon"></span>';
    th.dataset.col = col;
    th.onclick = () => sortBy(col);
    tr.appendChild(th);
  });
  // actions col
  const ta = document.createElement("th");
  ta.textContent = "Remarks";
  tr.appendChild(ta);
}

function buildBrandFilter(){
  const sel = document.getElementById("filterBrand");
  const brands = [...new Set(rawData.map(r=>r.Brand))].sort();
  brands.forEach(b=>{
    const o = document.createElement("option");
    o.value = b; o.textContent = b;
    sel.appendChild(o);
  });
}

function buildModalBrand(){
  const sel = document.getElementById("mBrand");
  sel.innerHTML = "";
  const brands = [...new Set(rawData.map(r=>r.Brand))].sort();
  brands.forEach(b=>{
    const o = document.createElement("option");
    o.value = b; o.textContent = b;
    sel.appendChild(o);
  });
}

// ── FILTERS ─────────────────────────────────────────────────────────────────
function applyFilters(){
  const q = document.getElementById("searchBox").value.toLowerCase().trim();
  const brand = document.getElementById("filterBrand").value;
  const asinF = document.getElementById("filterHasAsin").value;
  const invF  = document.getElementById("filterInventory").value;

  filtered = rawData.filter(r=>{
    if(brand && r.Brand !== brand) return false;
    if(asinF==="yes" && !r.Asin) return false;
    if(asinF==="no"  && r.Asin)  return false;
    const inv = Number(r["Pipeline Inventory"]||0);
    if(invF==="zero"   && inv !== 0)        return false;
    if(invF==="low"    && !(inv>=1&&inv<=100))   return false;
    if(invF==="medium" && !(inv>=101&&inv<=999)) return false;
    if(invF==="high"   && !(inv>=1000))          return false;
    if(q){
      const hay = COLS.map(c=>String(r[c]||"")).join(" ").toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });

  if(sortCol){
    filtered.sort((a,b)=>{
      let va=a[sortCol],vb=b[sortCol];
      if(typeof va==="number") return (va-vb)*sortDir;
      return String(va).localeCompare(String(vb))*sortDir;
    });
  }

  render(q);
  document.getElementById("rowCount").textContent = filtered.length + " / " + rawData.length + " rows";
  updateStats();
}

function clearFilters(){
  document.getElementById("searchBox").value="";
  document.getElementById("filterBrand").value="";
  document.getElementById("filterHasAsin").value="";
  document.getElementById("filterInventory").value="";
  applyFilters();
}

// ── RENDER ───────────────────────────────────────────────────────────────────
// ── DATE HELPERS ─────────────────────────────────────────────────────────────
function formatIndianDate(val){
  if(!val) return "";
  // val can be YYYY-MM-DD or DD-MM-YYYY or other
  let d;
  if(/^\d{4}-\d{2}-\d{2}$/.test(val)){
    const [y,m,day] = val.split("-");
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return `${day}-${months[parseInt(m)-1]}-${y}`;
  }
  return val;
}
function toInputDate(val){
  if(!val) return "";
  // If already YYYY-MM-DD return as is
  if(/^\d{4}-\d{2}-\d{2}$/.test(val)) return val;
  // If DD-MM-YYYY convert
  if(/^\d{2}-\d{2}-\d{4}$/.test(val)){
    const [d,m,y] = val.split("-");
    return `${y}-${m}-${d}`;
  }
  return "";
}

function render(q=""){
  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";
  document.getElementById("emptyState").style.display = filtered.length?"none":"block";

  filtered.forEach((row,i)=>{
    const tr = document.createElement("tr");
    if(row._new) tr.classList.add("new-row");
    if(row._edited) tr.classList.add("edited");

    COLS.forEach(col=>{
      const td = document.createElement("td");
      const val = row[col] ?? "";

      if(col==="SR NO"){
        td.className="srNo"; td.textContent = row["SR NO"];
      } else if(col==="Brand"){
        const span = document.createElement("span");
        span.className = "brand-badge " + brandClass(val);
        span.textContent = val;
        td.appendChild(span);
        td.className="editable"; td.dataset.col=col; td.dataset.idx=i;
        td.ondblclick = ()=>startEdit(td,i,col);
      } else if(col==="Asin"){
        if(val){
          const a = document.createElement("a");
          a.href="https://www.amazon.com/dp/"+val;
          a.target="_blank"; a.className="asin-link"; a.textContent=val;
          if(q && val.toLowerCase().includes(q)) a.innerHTML = highlight(val,q);
          td.appendChild(a);
        } else {
          td.innerHTML='<span style="color:var(--text2);opacity:.4">—</span>';
        }
        td.className="editable"; td.dataset.col=col; td.dataset.idx=i;
        td.ondblclick = ()=>startEdit(td,i,col);
      } else if(col==="Pipeline Inventory"||col==="Open Order"){
        td.className="numCell editable " + numClass(Number(val));
        td.dataset.col=col; td.dataset.idx=i;
        td.textContent = Number(val);
        td.ondblclick = ()=>startEdit(td,i,col);
        td.setAttribute("data-tip", col+": "+Number(val));
      } else if(col==="BL"){
        td.className="textCell editable";
        td.dataset.col=col; td.dataset.idx=i;
        if(val){
          const span = document.createElement("span");
          span.className = "bl-badge";
          span.textContent = val;
          td.appendChild(span);
        } else {
          td.innerHTML='<span class="empty-cell">—</span>';
        }
        td.ondblclick = ()=>startEdit(td,i,col);
      } else if(col==="ETA"){
        td.className="textCell eta-td";
        td.dataset.col=col; td.dataset.idx=i;
        // Show formatted date or dash
        const displayVal = val ? formatIndianDate(val) : "";
        const rawVal = val ? toInputDate(val) : "";
        td.innerHTML = `<div class="eta-wrap">
          ${displayVal ? `<span class="eta-badge">${displayVal}</span>` : '<span class="empty-cell">—</span>'}
          <input type="date" class="eta-picker" value="${rawVal}" data-rowidx="${rawData.indexOf(row)}" title="Pick ETA date">
        </div>`;
        td.querySelector(".eta-picker").addEventListener("change", function(){
          const ridx = parseInt(this.dataset.rowidx);
          pushUndo();
          rawData[ridx].ETA = this.value; // store as YYYY-MM-DD internally
          rawData[ridx]._edited = true;
          saveRemote();
          toast("ETA updated ✓","ok");
          applyFilters();
        });
      } else {
        td.className="editable"; td.dataset.col=col; td.dataset.idx=i;
        td.textContent = val;
        if(q && String(val).toLowerCase().includes(q))
          td.innerHTML = highlight(String(val),q);
        td.ondblclick = ()=>startEdit(td,i,col);
      }
      tr.appendChild(td);
    });

    // Remarks cell
    const ta = document.createElement("td");
    ta.className = "remarksTd";
    const rmk = row.Remarks || "";
    ta.innerHTML = `<div class="remarksWrap">
      <textarea class="remarksInput" rows="1" placeholder="Add remark…" data-idx="${rawData.indexOf(row)}">${rmk}</textarea>
      <div class="rowActions">
        <button class="rowBtn dup" onclick="dupRow(${i})" title="Duplicate">⧉</button>
        <button class="rowBtn del" onclick="delRow(${i})" title="Delete">✕</button>
      </div>
    </div>`;
    // save remarks on change
    ta.querySelector("textarea").addEventListener("change", function(){
      const ridx = parseInt(this.dataset.idx);
      pushUndo();
      rawData[ridx].Remarks = this.value;
      rawData[ridx]._edited = true;
      saveRemote();
      toast("Remark saved ✓","ok");
    });
    // auto-grow
    ta.querySelector("textarea").addEventListener("input", function(){
      this.style.height="auto";
      this.style.height=this.scrollHeight+"px";
    });
    tr.appendChild(ta);
    tbody.appendChild(tr);
  });
}

function highlight(text, q){
  if(!q) return text;
  const idx = text.toLowerCase().indexOf(q.toLowerCase());
  if(idx<0) return text;
  return text.slice(0,idx)+"<mark>"+text.slice(idx,idx+q.length)+"</mark>"+text.slice(idx+q.length);
}

function brandClass(b){
  const l = b.toLowerCase();
  if(l.includes("audio")) return "brand-audio";
  if(l.includes("nexlev")) return "brand-nexlev";
  if(l.includes("tonor")) return "brand-tonor";
  if(l.includes("white")) return "brand-white";
  return "brand-other";
}
function numClass(n){
  if(n===0) return "zero";
  if(n>=1000) return "high";
  if(n>=100) return "medium";
  return "low";
}

// ── INLINE EDIT ──────────────────────────────────────────────────────────────
function startEdit(td, filteredIdx, col){
  if(td.querySelector("input")) return;
  const row = filtered[filteredIdx];
  const rawIdx = rawData.indexOf(row);
  const orig = row[col];

  const input = document.createElement("input");
  input.className = "cellInput";
  input.value = orig;
  if(col==="Pipeline Inventory"||col==="Open Order") input.type="number";
  td.innerHTML=""; td.appendChild(input);
  input.focus(); input.select();

  const commit = ()=>{
    const nval = input.type==="number" ? Number(input.value) : input.value.trim();
    if(nval !== orig){
      pushUndo();
      rawData[rawIdx][col] = nval;
      rawData[rawIdx]._edited = true;
      saveRemote();
      toast("✓ Updated "+col, "ok");
    }
    applyFilters();
  };
  input.onblur = commit;
  input.onkeydown = e=>{
    if(e.key==="Enter") commit();
    if(e.key==="Escape"){ applyFilters(); }
  };
}

// ── SORT ─────────────────────────────────────────────────────────────────────
function sortBy(col){
  if(sortCol===col) sortDir*=-1; else { sortCol=col; sortDir=1; }
  document.querySelectorAll("thead th").forEach(th=>{
    th.classList.remove("asc","desc");
    if(th.dataset.col===col) th.classList.add(sortDir===1?"asc":"desc");
  });
  applyFilters();
}

// ── STATS ────────────────────────────────────────────────────────────────────
function updateStats(){
  const data = filtered.length ? filtered : rawData;
  const totalPipeline = data.reduce((s,r)=>s+Number(r["Pipeline Inventory"]||0),0);
  const totalOrder    = data.reduce((s,r)=>s+Number(r["Open Order"]||0),0);
  const brands = [...new Set(rawData.map(r=>r.Brand))].length;
  const noAsin = rawData.filter(r=>!r.Asin).length;
  const withStock = rawData.filter(r=>Number(r["Pipeline Inventory"]||0)>0).length;

  document.getElementById("statsBar").innerHTML = `
    <div class="statCard"><div class="label">📦 Total SKUs</div><div class="val">${rawData.length}</div><div class="sub">${brands} brands</div></div>
    <div class="statCard"><div class="label">🔄 Pipeline Inventory</div><div class="val">${totalPipeline}</div><div class="sub">units in pipeline</div></div>
    <div class="statCard"><div class="label">🛒 Open Orders</div><div class="val">${totalOrder}</div><div class="sub">pending fulfilment</div></div>
    <div class="statCard"><div class="label">✅ In Stock</div><div class="val">${withStock}</div><div class="sub">SKUs with inventory</div></div>
    <div class="statCard"><div class="label">⚠️ Missing ASIN</div><div class="val" style="-webkit-text-fill-color:var(--warn)">${noAsin}</div><div class="sub">needs attention</div></div>
  `;
  document.getElementById("headerMeta").textContent = "";
}

// ── ROW ACTIONS ──────────────────────────────────────────────────────────────
function delRow(filteredIdx){
  if(!confirm("Delete this row?")) return;
  pushUndo();
  const row = filtered[filteredIdx];
  const idx = rawData.indexOf(row);
  rawData.splice(idx,1);
  reindex();
  saveRemote();
  toast("Row deleted","info");
  applyFilters();
}

function dupRow(filteredIdx){
  pushUndo();
  const row = filtered[filteredIdx];
  const idx = rawData.indexOf(row);
  const copy = {...row, _new:true, _edited:false};
  rawData.splice(idx+1,0,copy);
  reindex();
  saveRemote();
  toast("Row duplicated","ok");
  applyFilters();
}

function reindex(){
  rawData.forEach((r,i)=>r["SR NO"]=i+1);
}

// ── ADD MODAL ────────────────────────────────────────────────────────────────
function showAddModal(){
  document.getElementById("addModal").classList.add("open");
  document.getElementById("mSku").focus();
}
function closeModal(){
  document.getElementById("addModal").classList.remove("open");
}
function addRow(){
  const brand = document.getElementById("mBrand").value;
  const sku   = document.getElementById("mSku").value.trim();
  const asin  = document.getElementById("mAsin").value.trim();
  const model = document.getElementById("mModel").value.trim();
  const pipe  = Number(document.getElementById("mPipeline").value)||0;
  const ord   = Number(document.getElementById("mOrder").value)||0;
  if(!sku){ toast("SKU is required","err"); return; }
  pushUndo();
  rawData.push({
    "SR NO": rawData.length+1,
    "Brand": brand, "SKU": sku, "Asin": asin,
    "Model Name": model, "Pipeline Inventory": pipe, "BL": document.getElementById("mBL").value||"", "ETA": document.getElementById("mETA").value||"", "Open Order": ord, "Remarks": document.getElementById("mRemarks").value||"",
    _new:true
  });
  saveRemote();
  toast("Row added ✓","ok");
  closeModal();
  // reset form
  document.getElementById("mSku").value="";
  document.getElementById("mAsin").value="";
  document.getElementById("mModel").value="";
  document.getElementById("mBL").value="";
  document.getElementById("mETA").value="";
  document.getElementById("mPipeline").value="0";
  document.getElementById("mOrder").value="0";
  applyFilters();
}

// ── UNDO / REDO ──────────────────────────────────────────────────────────────
function pushUndo(){
  undoStack.push(JSON.parse(JSON.stringify(rawData)));
  redoStack = [];
  if(undoStack.length>50) undoStack.shift();
}
function undo(){
  if(!undoStack.length){ toast("Nothing to undo","info"); return; }
  redoStack.push(JSON.parse(JSON.stringify(rawData)));
  rawData.length=0;
  undoStack.pop().forEach(r=>rawData.push(r));
  saveRemote(); applyFilters(); toast("Undone ↩","info");
}
function redo(){
  if(!redoStack.length){ toast("Nothing to redo","info"); return; }
  undoStack.push(JSON.parse(JSON.stringify(rawData)));
  rawData.length=0;
  redoStack.pop().forEach(r=>rawData.push(r));
  saveRemote(); applyFilters(); toast("Redone ↪","info");
}
function bindKeys(){
  document.addEventListener("keydown",e=>{
    if((e.ctrlKey||e.metaKey)&&e.key==="z"&&!e.shiftKey){ e.preventDefault(); undo(); }
    if((e.ctrlKey||e.metaKey)&&(e.key==="y"||(e.key==="z"&&e.shiftKey))){ e.preventDefault(); redo(); }
  });
}

// ── EXPORT ───────────────────────────────────────────────────────────────────
function exportCSV(){
  const data = filtered.length < rawData.length ? filtered : rawData;
  let csv = ALL_EXPORT_COLS.join(",") + "\n";
  data.forEach(r=>{
    csv += ALL_EXPORT_COLS.map(c=>{
      const v = String(r[c]||"").replace(/"/g,'""');
      return v.includes(",") ? `"${v}"` : v;
    }).join(",") + "\n";
  });
  dl(csv,"text/csv","cambium_export.csv");
  toast("CSV exported (" + data.length + " rows)","ok");
}
function exportJSON(){
  const data = filtered.length < rawData.length ? filtered : rawData;
  const clean = data.map(r=>{
    const o={};
    ALL_EXPORT_COLS.forEach(c=>o[c]=r[c]??null);
    return o;
  });
  dl(JSON.stringify(clean,null,2),"application/json","cambium_export.json");
  toast("JSON exported","ok");
}
function dl(content, mime, name){
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([content],{type:mime}));
  a.download=name; a.click();
}

// ── SAVE TO SERVER ────────────────────────────────────────────────────────────
async function saveRemote(){
  const clean = rawData.map(r=>{ const o={};COLS.forEach(c=>o[c]=r[c]??null);return o; });
  await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(clean)});
}

// ── TOAST ────────────────────────────────────────────────────────────────────
function toast(msg, type="ok"){
  const el=document.createElement("div");
  el.className="toastItem "+type; el.textContent=msg;
  document.getElementById("toast").appendChild(el);
  setTimeout(()=>el.remove(),2800);
}

// close modal on overlay click
document.getElementById("addModal").onclick = e=>{
  if(e.target===document.getElementById("addModal")) closeModal();
};

// auto-init if already logged in
if(sessionStorage.getItem("auth")==="1") init();
</script>
</body>
</html>
"""

# ── HTTP HANDLER ──────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass  # silence logs

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/","/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",len(body))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/data":
            self.send_json(DB)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/save":
            length = int(self.headers.get("Content-Length",0))
            body = self.rfile.read(length)
            new_data = json.loads(body)
            DB.clear()
            DB.extend(new_data)
            save_db()
            self.send_json({"ok":True})
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    import shutil
    # copy excel next to server
    if not os.path.exists(EXCEL_PATH):
        pass
    
    PORT = 8000
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"""
╔══════════════════════════════════════════════════╗
║      Cambium Import Details Tool  🚀             ║
║                                                  ║
║  URL:      http://localhost:{PORT}               ║
║  Password: hazique123                            ║
║                                                  ║
║  Press Ctrl+C to stop                            ║
╚══════════════════════════════════════════════════╝
""")
    server.serve_forever()



