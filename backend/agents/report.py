"""
Report Generator Agent
──────────────────────
Analyzes converted files and produces a self-contained report.html
inside each module's output folder. Includes confidence scores,
Chart.js visualizations, test cases, and .NET compatibility checks.
"""

import os
import re
import json
from datetime import datetime
from typing import Any


# ── File category detector ────────────────────────────────────────────────────
def _categorize(path: str) -> str:
    p = path.lower()
    if "controller" in p:               return "controller"
    if "viewmodel" in p or "model" in p: return "viewmodel"
    if ".cshtml" in p or "/view" in p:  return "view"
    if "service" in p or "interface" in p or "interop" in p: return "interop"
    return "other"


# ── Static analyzers ──────────────────────────────────────────────────────────
def _analyze(content: str) -> dict:
    lines    = content.splitlines()
    warnings = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "TODO"                    in stripped: warnings.append({"line": i, "type": "TODO",    "text": stripped[:120]})
        if "FIXME"                   in stripped: warnings.append({"line": i, "type": "FIXME",   "text": stripped[:120]})
        if "NotImplementedException" in stripped: warnings.append({"line": i, "type": "logic",   "text": "Not-implemented method body"})
        if "throw new Exception("    in stripped: warnings.append({"line": i, "type": "logic",   "text": "Generic exception throw (use specific type)"})
        if re.search(r"catch\s*\(\s*Exception\s*\)", stripped): warnings.append({"line": i, "type": "syntax", "text": "Catching base Exception (too broad)"})

    return {
        "namespaces":  re.findall(r"namespace\s+([\w.]+)", content),
        "classes":     re.findall(r"class\s+(\w+)", content),
        "http_actions":re.findall(r"\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)\]", content),
        "usings":      re.findall(r"^using\s+(.+);", content, re.MULTILINE),
        "properties":  re.findall(r"public\s+\w[\w<>, ]*\s+\w+\s*\{\s*get;\s*set;\s*\}", content),
        "annotations": re.findall(r"\[(?:Required|Range|StringLength|Display|MaxLength|EmailAddress|RegularExpression)", content),
        "brace_balance": content.count("{") - content.count("}"),
        "line_count":  len(lines),
        "warnings":    warnings,
    }


def _score_controller(a: dict) -> tuple[int, list[str]]:
    s, notes = 0, []
    if a["namespaces"]:   s += 15; notes.append("Namespace declared")
    if a["classes"]:      s += 15; notes.append(f"Class: {a['classes'][0]}")
    if a["http_actions"]: s += 25; notes.append(f"{len(a['http_actions'])} HTTP action(s) found")
    if a["brace_balance"] == 0: s += 20; notes.append("Braces balanced")
    mvc = any("Mvc" in u or "AspNetCore" in u for u in a["usings"])
    if mvc:               s += 15; notes.append("MVC namespace imported")
    if a["properties"] or len(a["classes"]) > 0: s += 10
    return min(s, 100), notes

def _score_view(a: dict, content: str) -> tuple[int, list[str]]:
    s, notes = 0, []
    if "@model"           in content: s += 25; notes.append("@model directive present")
    if "BeginForm"        in content or "<form" in content: s += 20; notes.append("Form element found")
    if "@Html."           in content or "asp-for" in content: s += 20; notes.append("HTML helpers / tag helpers")
    if "ViewBag"          in content or "ViewData" in content: s += 10; notes.append("ViewBag/ViewData used")
    if "@{"               in content: s += 10; notes.append("Razor code block present")
    if "form-control"     in content or "asp-validation" in content: s += 15; notes.append("Bootstrap / validation CSS")
    return min(s, 100), notes

def _score_viewmodel(a: dict, content: str) -> tuple[int, list[str]]:
    s, notes = 0, []
    if a["namespaces"]:   s += 15; notes.append("Namespace declared")
    if a["classes"]:      s += 20; notes.append(f"Class: {a['classes'][0]}")
    if a["properties"]:   s += 25; notes.append(f"{len(a['properties'])} propert(y/ies)")
    if a["annotations"]:  s += 25; notes.append(f"{len(a['annotations'])} data annotation(s)")
    if a["brace_balance"] == 0: s += 15; notes.append("Braces balanced")
    return min(s, 100), notes

def _score_interop(a: dict, content: str) -> tuple[int, list[str]]:
    s, notes = 0, []
    if "interface"        in content.lower(): s += 30; notes.append("Service interface defined")
    if a["namespaces"]:   s += 15; notes.append("Namespace declared")
    methods = re.findall(r"\w[\w<>, ]*\s+\w+\s*\(", content)
    if methods:           s += 25; notes.append(f"{len(methods)} method signature(s)")
    if a["brace_balance"] == 0: s += 15; notes.append("Braces balanced")
    if "Task" in content or "async" in content or "Result" in content:
        s += 15; notes.append("Async/Result patterns")
    return min(s, 100), notes


def _score_file(path: str, content: str) -> tuple[str, int, list[str]]:
    cat = _categorize(path)
    a   = _analyze(content)
    if cat == "controller": sc, notes = _score_controller(a)
    elif cat == "view":     sc, notes = _score_view(a, content)
    elif cat == "viewmodel":sc, notes = _score_viewmodel(a, content)
    elif cat == "interop":  sc, notes = _score_interop(a, content)
    else:                   sc, notes = 50, ["Generic file — no category-specific scoring"]
    return cat, sc, notes


# ── Test-case generator ───────────────────────────────────────────────────────
def _generate_tests(files: list[dict]) -> list[dict]:
    tests = []
    for f in files:
        content, path = f.get("content", ""), f.get("path", "")
        if "controller" not in path.lower(): continue
        for http_method, action in re.findall(
            r"\[(Http\w+)\]\s*(?:\[.*?\]\s*)*public\s+\w[\w<>]*\s+(\w+)\s*\(", content
        ):
            tests += [
                {"name": f"{action}_Returns_View",
                 "desc": f"{http_method} /{action} returns a ViewResult",
                 "expl": f"Đảm bảo Action {action} () phản hồi đúng giao diện cho người dùng thay vì lỗi 500 hoặc dữ liệu thô.",
                 "kind": "unit", "pass": None},
                {"name": f"{action}_ModelState_Valid",
                 "desc": f"ModelState is valid for {action}",
                 "expl": f"Kiểm tra xem dữ liệu submit lên {action} có thỏa mãn các Validation Rules (Required, StringLength...) trước khi xử lý không.",
                 "kind": "unit", "pass": None},
            ]

    # Structural / compatibility tests
    for f in files:
        content, path = f.get("content", ""), f.get("path", "")
        if not path.endswith(".cs"): continue
        name = os.path.basename(path)
        bal = content.count("{") - content.count("}")
        tests.append({
            "name": f"{name}_BraceBalance",
            "desc": "Curly braces are balanced (compilation prerequisite)",
            "expl": "Kiểm tra dấu ngoặc nhọn `{ }` trong code có mở/đóng đầy đủ hay không. Nếu thiếu, code sẽ không thể biên dịch.",
            "kind": "compatibility",
            "pass": bal == 0,
        })
        has_ns = bool(re.search(r"namespace\s+\S+", content))
        if name == "Program.cs":
            # Program.cs in modern .NET Core uses Top-level statements, so namespace isn't required
            has_ns = True
            
        tests.append({
            "name": f"{name}_HasNamespace",
            "desc": "File declares a namespace",
            "expl": f"Đảm bảo file {name} có khai báo namespace hợp lệ (hoặc là Top-level script), tránh lỗi xung đột class khi .NET build project.",
            "kind": "structure",
            "pass": has_ns,
        })

    # De-duplicate
    seen = set()
    unique = []
    for t in tests:
        if t["name"] not in seen:
            seen.add(t["name"]); unique.append(t)
    return unique


# ── .NET compatibility checklist ──────────────────────────────────────────────
def _dotnet_checks(files: list[dict]) -> list[dict]:
    checks = []
    for f in files:
        content, path = f.get("content", ""), f.get("path", "")
        if not path.endswith(".cs"): continue
        name = os.path.basename(path)
        bal  = content.count("{") - content.count("}")
        has_ns  = bool(re.search(r"namespace\s+\S+", content))
        has_cls = bool(re.search(r"class\s+\w+", content))
        has_mvc = "Microsoft.AspNetCore.Mvc" in content or "System.Web.Mvc" in content
        has_stubs = bool(re.search(r"TODO|NotImplementedException", content))

        checks += [
            {"file": name, "check": "Namespace declaration",     "ok": has_ns,    "sev": "error"   if not has_ns    else "ok"},
            {"file": name, "check": "Class declaration",         "ok": has_cls,   "sev": "error"   if not has_cls   else "ok"},
            {"file": name, "check": "Balanced braces",           "ok": bal == 0,  "sev": "error"   if bal != 0      else "ok",
             "detail": f"Δ={bal:+d}" if bal != 0 else ""},
            {"file": name, "check": "MVC namespace imported",    "ok": has_mvc,   "sev": "warning" if not has_mvc   else "ok"},
            {"file": name, "check": "No stub / TODO code",       "ok": not has_stubs, "sev": "warning" if has_stubs else "ok"},
        ]
    return checks


# ── HTML report builder ───────────────────────────────────────────────────────
def generate_report(module_name: str, files: list[dict], qa_result: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Score every file
    scored   = {}  # cat → list of (filename, score, notes)
    all_warn = []
    for f in files:
        path, content = f.get("path", ""), f.get("content", "")
        cat, sc, notes = _score_file(path, content)
        scored.setdefault(cat, []).append((os.path.basename(path), sc, notes))
        a = _analyze(content)
        for w in a["warnings"]:
            w["file"] = os.path.basename(path)
            all_warn.append(w)

    # Category confidence: average within each category
    cat_conf = {}
    for cat in ["controller", "view", "viewmodel", "interop"]:
        items = scored.get(cat, [])
        cat_conf[cat] = round(sum(s for _, s, _ in items) / len(items)) if items else 0

    overall = round(sum(cat_conf.values()) / max(len([v for v in cat_conf.values() if v > 0]), 1))

    tests  = _generate_tests(files)
    checks = _dotnet_checks(files)

    passed_tests  = sum(1 for t in tests if t["pass"] is True)
    failed_tests  = sum(1 for t in tests if t["pass"] is False)
    pending_tests = sum(1 for t in tests if t["pass"] is None)
    total_tests   = len(tests)

    ok_checks  = sum(1 for c in checks if c["ok"])
    err_checks = sum(1 for c in checks if not c["ok"] and c["sev"] == "error")
    wrn_checks = sum(1 for c in checks if not c["ok"] and c["sev"] == "warning")

    status = "SUCCESS" if qa_result.get("valid") else "PARTIAL"
    status_color = "#10b981" if status == "SUCCESS" else "#f59e0b"

    def bar(score, color):
        return f"""<div style="background:#1f2937;border-radius:6px;height:10px;flex:1;">
          <div style="background:{color};height:10px;border-radius:6px;width:{score}%;transition:width 0.6s;"></div></div>"""

    def cat_row(label, cat, color):
        items = scored.get(cat, [])
        score = cat_conf[cat]
        files_str = ", ".join(n for n, _, _ in items) if items else "—"
        notes_str = "; ".join(note for _, _, ns in items for note in ns[:2]) if items else "No file found"
        return f"""
        <tr>
          <td style="padding:10px 12px;font-weight:600;color:{color}">{label}</td>
          <td style="padding:10px 12px">
            <div style="display:flex;align-items:center;gap:10px">
              {bar(score, color)}
              <span style="font-size:18px;font-weight:700;color:{color};min-width:48px">{score}%</span>
            </div>
          </td>
          <td style="padding:10px 12px;color:#9ca3af;font-size:12px">{files_str}</td>
          <td style="padding:10px 12px;color:#6b7280;font-size:11px">{notes_str}</td>
        </tr>"""

    def test_rows():
        rows = []
        for t in tests:
            if t["pass"] is True:    badge = '<span style="background:#14532d;color:#86efac;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">✅ PASS</span>'
            elif t["pass"] is False: badge = '<span style="background:#450a0a;color:#fca5a5;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">❌ FAIL</span>'
            else:                    badge = '<span style="background:#1c1917;color:#a8a29e;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">⏳ PENDING</span>'
            kind_color = {"unit":"#818cf8","integration":"#38bdf8","compatibility":"#34d399","structure":"#fb923c"}.get(t["kind"],"#6b7280")
            rows.append(f"""
            <tr style="border-bottom:1px solid #1f2937">
              <td style="padding:12px 12px;font-family:monospace;font-size:13px;color:#e5e7eb;font-weight:600">{t['name']}</td>
              <td style="padding:12px 12px;font-size:13px;color:#9ca3af">{t['desc']}</td>
              <td style="padding:12px 12px;font-size:12px;color:#a78bfa;font-style:italic;max-width:300px;line-height:1.4">{t.get('expl', '')}</td>
              <td style="padding:12px 12px;text-align:center"><span style="color:{kind_color};font-size:11px;font-weight:700;letter-spacing:0.5px">{t['kind'].upper()}</span></td>
              <td style="padding:12px 12px;text-align:center">{badge}</td>
            </tr>""")
        return "".join(rows)

    def check_rows():
        rows = []
        for c in checks:
            if c["ok"]:   icon, bg = "✅", "#064e3b"
            elif c["sev"] == "error":   icon, bg = "❌", "#450a0a"
            else:                       icon, bg = "⚠️", "#422006"
            detail = c.get("detail", "")
            rows.append(f"""
            <tr style="border-bottom:1px solid #1f2937">
              <td style="padding:8px 12px;font-family:monospace;font-size:12px;color:#9ca3af">{c['file']}</td>
              <td style="padding:8px 12px;font-size:12px;color:#e5e7eb">{c['check']}</td>
              <td style="padding:8px 12px;text-align:center;font-size:14px">{icon}</td>
              <td style="padding:8px 12px;font-size:11px;color:#6b7280">{detail}</td>
            </tr>""")
        return "".join(rows)

    def warn_rows():
        if not all_warn:
            return '<tr><td colspan="4" style="padding:16px;text-align:center;color:#4b5563">No warnings found ✅</td></tr>'
        rows = []
        colors = {"TODO":"#fbbf24","FIXME":"#f87171","logic":"#f87171","syntax":"#fb923c"}
        for w in all_warn[:50]:
            c = colors.get(w["type"], "#9ca3af")
            rows.append(f"""
            <tr style="border-bottom:1px solid #1f2937">
              <td style="padding:8px 12px;font-family:monospace;font-size:12px;color:#9ca3af">{w['file']}</td>
              <td style="padding:8px 12px;text-align:center;color:#6b7280;font-size:12px">L{w['line']}</td>
              <td style="padding:8px 12px"><span style="background:{c}22;color:{c};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">{w['type'].upper()}</span></td>
              <td style="padding:8px 12px;font-size:12px;font-family:monospace;color:#d1d5db">{w['text'][:100]}</td>
            </tr>""")
        return "".join(rows)

    chart_data = json.dumps({
        "labels":       ["Controller","View","ViewModel","Interop"],
        "scores":       [cat_conf["controller"],cat_conf["view"],cat_conf["viewmodel"],cat_conf["interop"]],
        "colors":       ["#60a5fa","#34d399","#a78bfa","#fbbf24"],
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Migration Report — {module_name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',system-ui,sans-serif;line-height:1.5}}
  h2{{font-size:14px;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px}}
  table{{width:100%;border-collapse:collapse}}
  th{{text-align:left;padding:9px 12px;font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid #21262d}}
  .card{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px;margin-bottom:20px}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:6px;font-size:12px;font-weight:700}}
</style>
</head>
<body>
<!-- Header -->
<div style="background:linear-gradient(135deg,#161b22 0%,#0d1117 100%);border-bottom:1px solid #21262d;padding:28px 40px">
  <div style="max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between">
    <div>
      <div style="font-size:11px;color:#6b7280;margin-bottom:4px;text-transform:uppercase;letter-spacing:.1em">Migration Report</div>
      <h1 style="font-size:26px;font-weight:800;color:#e6edf3">{module_name}</h1>
      <div style="font-size:12px;color:#6b7280;margin-top:4px">Generated: {now}</div>
    </div>
    <div style="text-align:right">
      <span class="badge" style="background:{status_color}22;color:{status_color};font-size:16px;padding:8px 20px">{status}</span>
      <div style="font-size:13px;color:#6b7280;margin-top:8px">{len(files)} file(s) generated</div>
    </div>
  </div>
</div>

<div style="max-width:1200px;margin:0 auto;padding:28px 40px">

  <!-- Summary cards -->
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px">
    {"".join([
      f'<div class="card" style="text-align:center"><div style="font-size:32px;font-weight:800;color:{c}">{v}</div><div style="font-size:12px;color:#6b7280;margin-top:4px">{l}</div></div>'
      for v, l, c in [
        (len(files),     "Files Generated",    "#60a5fa"),
        (f"{overall}%",  "Avg Confidence",     "#a78bfa"),
        (passed_tests,   "Tests Passed",       "#10b981"),
        (ok_checks,      "Compat Checks OK",   "#34d399"),
      ]
    ])}
  </div>

  <!-- Charts row -->
  <div style="display:grid;grid-template-columns:1fr 2fr;gap:20px;margin-bottom:24px">
    <div class="card" style="display:flex;flex-direction:column;align-items:center">
      <h2>Overall Confidence</h2>
      <div style="position:relative;width:200px;height:200px">
        <canvas id="doughnut"></canvas>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center">
          <div style="font-size:32px;font-weight:800;color:#a78bfa">{overall}%</div>
          <div style="font-size:11px;color:#6b7280">confidence</div>
        </div>
      </div>
    </div>
    <div class="card">
      <h2>Per-Category Confidence</h2>
      <canvas id="barChart" height="120"></canvas>
    </div>
  </div>

  <!-- Confidence table -->
  <div class="card" style="margin-bottom:24px">
    <h2>Confidence Scores</h2>
    <table>
      <thead><tr>
        <th style="width:140px">Category</th>
        <th>Score</th>
        <th>Files</th>
        <th>Notes</th>
      </tr></thead>
      <tbody>
        {cat_row("Controller",  "controller",  "#60a5fa")}
        {cat_row("View",        "view",        "#34d399")}
        {cat_row("ViewModel",   "viewmodel",   "#a78bfa")}
        {cat_row("Interop",     "interop",     "#fbbf24")}
      </tbody>
    </table>
  </div>

  <!-- Test cases -->
  <div class="card" style="margin-bottom:24px">
    <h2 style="margin-bottom:10px">Generated Test Cases
      <span style="font-size:12px;font-weight:400;margin-left:10px">
        <span style="color:#10b981">{passed_tests} passed</span> ·
        <span style="color:#ef4444">{failed_tests} failed</span> ·
        <span style="color:#6b7280">{pending_tests} pending</span>
      </span>
    </h2>
    <table style="table-layout:fixed; width:100%">
      <thead><tr>
        <th style="width:25%">Test Name</th>
        <th style="width:25%">Description</th>
        <th style="width:30%">Ý nghĩa (Explanation)</th>
        <th style="text-align:center;width:10%">Type</th>
        <th style="text-align:center;width:10%">Result</th>
      </tr></thead>
      <tbody>{test_rows()}</tbody>
    </table>
  </div>

  <!-- .NET Compatibility -->
  <div class="card" style="margin-bottom:24px">
    <h2 style="margin-bottom:10px">.NET Compatibility
      <span style="font-size:12px;font-weight:400;margin-left:10px">
        <span style="color:#10b981">{ok_checks} ok</span> ·
        <span style="color:#ef4444">{err_checks} error</span> ·
        <span style="color:#f59e0b">{wrn_checks} warning</span>
      </span>
    </h2>
    <table>
      <thead><tr>
        <th>File</th>
        <th>Check</th>
        <th style="text-align:center;width:60px">Status</th>
        <th>Detail</th>
      </tr></thead>
      <tbody>{check_rows()}</tbody>
    </table>
  </div>

  <!-- Warnings -->
  <div class="card">
    <h2 style="margin-bottom:10px">Code Warnings
      <span style="font-size:12px;font-weight:400;margin-left:10px;color:#6b7280">{len(all_warn)} total</span>
    </h2>
    <table>
      <thead><tr>
        <th>File</th>
        <th style="width:60px">Line</th>
        <th style="width:100px">Type</th>
        <th>Description</th>
      </tr></thead>
      <tbody>{warn_rows()}</tbody>
    </table>
  </div>

  <!-- QA Result section -->
  <div class="card" style="margin-top:20px">
    <h2>QA Agent Result</h2>
    <div style="display:flex;gap:20px;margin-top:10px;flex-wrap:wrap">
      <div>
        <div style="font-size:11px;color:#6b7280;margin-bottom:4px">STATUS</div>
        <span class="badge" style="background:{'#14532d' if qa_result.get('valid') else '#450a0a'};color:{'#86efac' if qa_result.get('valid') else '#fca5a5'}">
          {'✅ VALID' if qa_result.get('valid') else '❌ INVALID'}
        </span>
      </div>
      {"".join([f'<div><div style="font-size:11px;color:#ef4444;margin-bottom:4px">ERROR</div><div style="font-size:12px;color:#fca5a5">{e}</div></div>' for e in qa_result.get('errors',[])])}
      {"".join([f'<div><div style="font-size:11px;color:#f59e0b;margin-bottom:4px">WARNING</div><div style="font-size:12px;color:#fde68a">{w}</div></div>' for w in qa_result.get('warnings',[])])}
    </div>
  </div>

</div>

<script>
const d = {chart_data};

// Doughnut chart
new Chart(document.getElementById('doughnut'), {{
  type: 'doughnut',
  data: {{
    labels: d.labels,
    datasets: [{{ data: d.scores, backgroundColor: d.colors.map(c => c+'bb'), borderColor: d.colors, borderWidth: 2 }}]
  }},
  options: {{
    cutout: '72%', plugins: {{ legend: {{ display: false }} }},
    animation: {{ animateRotate: true, duration: 1000 }}
  }}
}});

// Bar chart
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: {{
    labels: d.labels,
    datasets: [{{ data: d.scores, backgroundColor: d.colors.map(c=>c+'99'), borderColor: d.colors, borderWidth: 2, borderRadius: 6 }}]
  }},
  options: {{
    indexAxis: 'y',
    scales: {{
      x: {{ min:0, max:100, grid:{{ color:'#21262d' }}, ticks:{{ color:'#6b7280' }} }},
      y: {{ grid:{{ display:false }}, ticks:{{ color:'#9ca3af', font:{{ weight:'600' }} }} }}
    }},
    plugins: {{ legend:{{ display:false }}, tooltip:{{
      callbacks:{{ label: ctx => ` ${{ctx.parsed.x}}% confidence` }}
    }} }},
    animation: {{ duration: 800 }}
  }}
}});
</script>
</body>
</html>"""
    return html


def save_report(output_dir: str, module_name: str, files: list[dict], qa_result: dict) -> str:
    """Generate and save report.html into the module's output folder."""
    html    = generate_report(module_name, files, qa_result)
    outpath = os.path.join(output_dir, "report.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)
    return outpath
