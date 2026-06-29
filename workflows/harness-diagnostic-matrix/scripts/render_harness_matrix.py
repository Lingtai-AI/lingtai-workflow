#!/usr/bin/env python3
"""Render a harness diagnostic matrix JSON into a self-contained HTML diagram.

Usage:
    python scripts/render_harness_matrix.py input.json output.html

This script is intentionally dependency-free (Python standard library only) and
does no network access. It reads a diagnosis JSON object, validates required
fields lightly, and writes a single self-contained HTML file (no external JS or
CSS) that presents the diagnosis as a matrix diagram.

Design contract (see SKILL.md):
    The matrix is for DIAGNOSIS only. It maps symptom -> system site ->
    evidence -> likely cause/problem hypothesis -> differentials -> next
    minimal evidence/question, with severity / confidence / insufficient-
    evidence flags. It must NOT contain implementation plans, fix steps, PR
    sequences, or action cards. Any forward-looking field is phrased as the
    next diagnostic evidence to collect, never as a repair step.
"""

import html
import json
import sys


REQUIRED_TOP = ["harness", "rows"]
REQUIRED_ROW = ["symptom", "site", "evidence", "hypothesis"]

# Diagnostic fields only. There is deliberately no "fix" / "action" / "plan"
# field anywhere in the rendered output.
ROW_COLUMNS = [
    ("symptom", "症状 / 主诉"),
    ("site", "系统节点 / 病位"),
    ("evidence", "证据指针"),
    ("hypothesis", "可能原因 / 问题假设"),
    ("differentials", "鉴别 / 竞争假设"),
    ("next_evidence", "下一步最小证据 / 问题"),
    ("severity", "严重度"),
    ("confidence", "置信度"),
]

SEVERITY_CLASS = {
    "high": "sev-high",
    "medium": "sev-med",
    "low": "sev-low",
    "高": "sev-high",
    "中": "sev-med",
    "低": "sev-low",
}

CONF_CLASS = {
    "high": "conf-high",
    "medium": "conf-med",
    "low": "conf-low",
    "insufficient": "conf-insuf",
    "unknown": "conf-insuf",
    "高": "conf-high",
    "中": "conf-med",
    "低": "conf-low",
    "证据不足": "conf-insuf",
    "未知": "conf-insuf",
}


def esc(value):
    """HTML-escape a scalar; join lists with separators; pass through blanks."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        parts = [esc(v) for v in value if v is not None and str(v) != ""]
        return "<br>· ".join(parts) if parts else ""
    return html.escape(str(value))


def validate(data):
    """Light validation. Returns a list of human-readable problem strings."""
    problems = []
    if not isinstance(data, dict):
        return ["top-level JSON must be an object"]
    for key in REQUIRED_TOP:
        if key not in data:
            problems.append("missing top-level field: %s" % key)
    rows = data.get("rows")
    if not isinstance(rows, list):
        problems.append("'rows' must be a list")
        return problems
    if not rows:
        problems.append("'rows' is empty; a matrix needs at least one row")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            problems.append("row %d is not an object" % i)
            continue
        for key in REQUIRED_ROW:
            if not row.get(key):
                problems.append("row %d missing required field: %s" % (i, key))
        # Evidence gate: a hypothesis with no evidence pointer and not flagged
        # as insufficient is a guess, which this matrix forbids.
        conf = str(row.get("confidence", "")).lower()
        flagged = row.get("insufficient_evidence") or conf in (
            "insufficient",
            "unknown",
            "证据不足",
            "未知",
        )
        if row.get("hypothesis") and not row.get("evidence") and not flagged:
            problems.append(
                "row %d has a hypothesis but no evidence and is not flagged "
                "insufficient (evidence gate)" % i
            )
    return problems


def render_node_strip(rows):
    """Render the distinct system sites as a top strip of node chips."""
    seen = []
    for row in rows:
        site = row.get("site")
        sites = site if isinstance(site, list) else [site]
        for s in sites:
            if s and s not in seen:
                seen.append(s)
    chips = "".join("<span class='node'>%s</span>" % esc(s) for s in seen)
    return "<div class='nodestrip'>%s</div>" % chips


def render_rows(rows):
    out = []
    for row in rows:
        sev_key = str(row.get("severity", "")).lower()
        conf_key = str(row.get("confidence", "")).lower()
        sev_cls = SEVERITY_CLASS.get(sev_key, "")
        conf_cls = CONF_CLASS.get(conf_key, "")
        if row.get("insufficient_evidence"):
            conf_cls = "conf-insuf"
        cells = []
        for field, _label in ROW_COLUMNS:
            val = esc(row.get(field))
            cls = ""
            if field == "severity":
                cls = sev_cls
            elif field == "confidence":
                cls = conf_cls
                if not val:
                    val = "证据不足 / insufficient"
                    cls = "conf-insuf"
            if field in ("differentials", "next_evidence") and val:
                val = "· " + val
            cells.append("<td class='%s'>%s</td>" % (cls, val))
        out.append("<tr>%s</tr>" % "".join(cells))
    return "\n".join(out)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg:#0f1419; --panel:#161c24; --line:#2a3340; --ink:#e6edf3;
    --muted:#8a98a8; --accent:#5ab0a8; --high:#e06c75; --med:#d8a657;
    --low:#7a8896; --insuf:#9a86c4;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;
    font-size:14px; line-height:1.55;
  }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:28px 22px 40px; }}
  .banner {{
    background:var(--panel); border:1px solid var(--accent);
    border-radius:10px; padding:14px 18px; margin-bottom:18px;
    font-size:15px; letter-spacing:.5px; color:var(--ink);
  }}
  .banner b {{ color:var(--accent); }}
  h1 {{ font-size:20px; margin:6px 0 2px; }}
  .meta {{ color:var(--muted); font-size:13px; margin-bottom:18px; }}
  .meta span {{ margin-right:16px; }}
  .nodestrip {{
    display:flex; flex-wrap:wrap; gap:8px; margin:0 0 20px;
  }}
  .node {{
    background:var(--panel); border:1px solid var(--line); color:var(--accent);
    border-radius:7px; padding:6px 12px; font-size:13px; font-weight:600;
  }}
  table {{
    width:100%; border-collapse:collapse; background:var(--panel);
    border:1px solid var(--line); border-radius:10px; overflow:hidden;
  }}
  th, td {{
    border:1px solid var(--line); padding:9px 11px; vertical-align:top;
    text-align:left; font-size:13px;
  }}
  th {{ background:#1d2530; color:var(--muted); font-weight:600; white-space:nowrap; }}
  td.sev-high {{ color:var(--high); font-weight:700; }}
  td.sev-med {{ color:var(--med); font-weight:700; }}
  td.sev-low {{ color:var(--low); font-weight:700; }}
  td.conf-high {{ color:var(--accent); font-weight:600; }}
  td.conf-med {{ color:var(--med); font-weight:600; }}
  td.conf-low {{ color:var(--low); font-weight:600; }}
  td.conf-insuf {{ color:var(--insuf); font-weight:600; }}
  .legend {{
    margin-top:18px; color:var(--muted); font-size:12px;
    display:flex; flex-wrap:wrap; gap:18px;
  }}
  .legend b {{ color:var(--ink); }}
  .note {{
    margin-top:22px; padding:14px 16px; background:var(--panel);
    border:1px solid var(--line); border-left:3px solid var(--insuf);
    border-radius:8px; color:var(--muted); font-size:12.5px;
  }}
  .note b {{ color:var(--ink); }}
  footer {{ margin-top:24px; color:var(--muted); font-size:11.5px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner"><b>矩阵在于诊断；如何做，是人的事。</b></div>
  <h1>{title}</h1>
  <div class="meta">{meta}</div>
  {nodestrip}
  <table>
    <thead><tr>{headers}</tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <div class="legend">
    <span><b>严重度</b> 高 / 中 / 低</span>
    <span><b>置信度</b> 高 / 中 / 低 / 证据不足</span>
    <span><b>· </b>列前缀表示多条目</span>
  </div>
  <div class="note">
    <b>诊断边界：</b>本矩阵只做问题定位 —— 症状、病位、证据、可能原因、鉴别、下一步取证。
    它不包含修复方案、实施计划、PR 顺序或操作卡片。凡“下一步”一栏均为应收集的诊断证据或应回答的问题，
    不是修复步骤。每条原因假设都须带证据指针；证据不足者标注为“证据不足 / insufficient”，不臆测成结论。
  </div>
  <footer>{footer}</footer>
</div>
</body>
</html>
"""


def render(data):
    rows = data.get("rows", [])
    title = esc(data.get("title") or ("%s 诊断矩阵" % data.get("harness", "Harness")))
    meta_bits = []
    if data.get("harness"):
        meta_bits.append("Harness: %s" % esc(data["harness"]))
    if data.get("date"):
        meta_bits.append("日期: %s" % esc(data["date"]))
    if data.get("scope"):
        meta_bits.append("范围: %s" % esc(data["scope"]))
    meta = "".join("<span>%s</span>" % b for b in meta_bits)
    headers = "".join("<th>%s</th>" % esc(label) for _f, label in ROW_COLUMNS)
    footer = esc(
        data.get("footer")
        or "本文件为静态诊断图示，不构成自动诊断结论；低置信项请按证据预算补证。"
    )
    return HTML_TEMPLATE.format(
        title=title,
        meta=meta,
        nodestrip=render_node_strip(rows),
        headers=headers,
        rows=render_rows(rows),
        footer=footer,
    )


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(
            "usage: python render_harness_matrix.py input.json output.html\n"
        )
        return 2
    in_path, out_path = argv[1], argv[2]
    try:
        with open(in_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.stderr.write("error reading JSON: %s\n" % exc)
        return 1

    problems = validate(data)
    if problems:
        sys.stderr.write("validation problems:\n")
        for p in problems:
            sys.stderr.write("  - %s\n" % p)
        # Hard-fail only on missing structure; evidence-gate problems are
        # warnings so a partly-filled matrix can still render with its flags.
        hard = [p for p in problems if "missing" in p or "must be" in p or "empty" in p]
        if hard:
            return 1

    out_html = render(data)
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(out_html)
    except OSError as exc:
        sys.stderr.write("error writing HTML: %s\n" % exc)
        return 1
    sys.stderr.write("wrote %s (%d rows)\n" % (out_path, len(data.get("rows", []))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
