"""
src/build_website.py — Multi-theme website builder
Every project number maps to a unique visual theme.
"""

import base64, os
from pathlib import Path

THEMES = {
    "dark_teal":       {"bg":"#0f1117","surface":"#1a1d27","card":"#20232f","border":"#2e3244","text":"#e8eaf0","muted":"#6b7280","accent":"#2dd4a0","accent2":"#60a5fa","danger":"#f87171","warn":"#fbbf24","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "ocean_blue":      {"bg":"#020f1e","surface":"#041830","card":"#072244","border":"#0e3a6e","text":"#e0f2fe","muted":"#7fb3d3","accent":"#38bdf8","accent2":"#06b6d4","danger":"#f87171","warn":"#fbbf24","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "deep_navy":       {"bg":"#0a0f1e","surface":"#111827","card":"#1e2a3a","border":"#2d3f55","text":"#e2e8f0","muted":"#94a3b8","accent":"#f6c90e","accent2":"#38bdf8","danger":"#fb7185","warn":"#fb923c","hfont":"Bebas Neue","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap"},
    "forest_green":    {"bg":"#0d1f0f","surface":"#132216","card":"#1a2e1d","border":"#2d4a32","text":"#e8f0e9","muted":"#8aaa8d","accent":"#4ade80","accent2":"#86efac","danger":"#f87171","warn":"#fbbf24","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "sunset_warm":     {"bg":"#1c0f05","surface":"#271508","card":"#321c0b","border":"#4a2e15","text":"#fef3e2","muted":"#b08060","accent":"#fb923c","accent2":"#fbbf24","danger":"#f87171","warn":"#facc15","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "midnight_purple": {"bg":"#0e0817","surface":"#150d24","card":"#1e1333","border":"#342052","text":"#ede9fe","muted":"#9478c4","accent":"#a78bfa","accent2":"#c084fc","danger":"#f87171","warn":"#fbbf24","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "crimson_bold":    {"bg":"#f8f9fa","surface":"#ffffff","card":"#ffffff","border":"#dee2e6","text":"#212529","muted":"#6c757d","accent":"#dc3545","accent2":"#0d6efd","danger":"#dc3545","warn":"#fd7e14","hfont":"Oswald","dark":False,"font_url":"https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Source+Sans+3:wght@300;400;600&family=JetBrains+Mono:wght@400;500&display=swap"},
    "light_editorial": {"bg":"#fafaf8","surface":"#ffffff","card":"#ffffff","border":"#e5e2d9","text":"#1a1a18","muted":"#6b6860","accent":"#c0392b","accent2":"#2c3e50","danger":"#e74c3c","warn":"#f39c12","hfont":"Playfair Display","dark":False,"font_url":"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Serif+4:wght@300;400;600&family=JetBrains+Mono:wght@400;500&display=swap"},
    "slate_minimal":   {"bg":"#f1f5f9","surface":"#ffffff","card":"#ffffff","border":"#e2e8f0","text":"#0f172a","muted":"#64748b","accent":"#0f172a","accent2":"#334155","danger":"#ef4444","warn":"#f59e0b","hfont":"DM Sans","dark":False,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
    "amber_retro":     {"bg":"#1a1200","surface":"#241900","card":"#2e2000","border":"#4a3500","text":"#fef9e7","muted":"#a08040","accent":"#f59e0b","accent2":"#fcd34d","danger":"#f87171","warn":"#fb923c","hfont":"DM Sans","dark":True,"font_url":"https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap"},
}

PROJECT_THEMES = {
    5:"dark_teal", 6:"ocean_blue", 7:"deep_navy", 8:"forest_green",
    9:"sunset_warm", 10:"midnight_purple", 11:"crimson_bold",
    12:"light_editorial", 13:"slate_minimal", 14:"amber_retro",
    15:"dark_teal", 16:"ocean_blue", 17:"deep_navy", 18:"forest_green",
    19:"sunset_warm", 20:"midnight_purple",
}

def img_to_b64(path):
    try:
        with open(path,"rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

def build(project_title, project_subtitle, repo_name, github_user,
          data_source, data_source_url, key_findings, chart_paths,
          summary_text, project_number, tools,
          output_dir="docs", theme_name=None):

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if theme_name is None:
        theme_name = PROJECT_THEMES.get(project_number, "dark_teal")
    t = THEMES[theme_name]
    dark = t["dark"]
    fg_on_accent = "#000" if not dark else t["bg"]

    kpi_html = ""
    for f in key_findings:
        c = f.get("color","var(--accent)")
        kpi_html += f'<div class="kpi" style="border-top:3px solid {c}"><div class="kpi-label">{f["label"]}</div><div class="kpi-value" style="color:{c}">{f["value"]}</div></div>'

    chart_html = ""
    for ch in chart_paths:
        b64 = img_to_b64(ch["path"])
        if b64:
            chart_html += f'<div class="chart-card"><div class="chart-header"><div class="chart-title">{ch["title"]}</div><div class="chart-sub">{ch.get("subtitle","")}</div></div><img src="data:image/png;base64,{b64}" alt="{ch["title"]}" loading="lazy"></div>'

    tool_html = " ".join(f'<span class="tool-badge">{x}</span>' for x in tools)
    card_shadow = "box-shadow:0 1px 3px rgba(0,0,0,.4);" if dark else "box-shadow:0 1px 4px rgba(0,0,0,.08);"
    overlay_bg  = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.03)"
    badge_bg    = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.05)"
    github_url  = f"https://github.com/{github_user}/{repo_name}"
    pages_url   = f"https://{github_user.lower()}.github.io/{repo_name}/"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{project_title} — {project_subtitle}</title>
<link href="{t['font_url']}" rel="stylesheet">
<style>
:root{{--bg:{t['bg']};--surface:{t['surface']};--card:{t['card']};--border:{t['border']};--text:{t['text']};--muted:{t['muted']};--accent:{t['accent']};--danger:{t['danger']};--warn:{t['warn']};}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'{t['hfont']}','DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:15px;line-height:1.65}}
.header{{background:var(--surface);border-bottom:1px solid var(--border);padding:0 32px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}}
.header-left{{display:flex;align-items:center;gap:14px}}
.proj-badge{{width:38px;height:38px;background:var(--accent);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:{fg_on_accent}}}
.header-title{{font-size:15px;font-weight:600}}
.header-title span{{color:var(--muted);font-weight:400;font-size:12px;margin-left:8px}}
.nav-links{{display:flex;gap:8px}}
.btn{{padding:5px 14px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;text-decoration:none;font-family:inherit;transition:all .15s;border:1px solid var(--border);color:var(--muted);background:transparent}}
.btn:hover{{border-color:var(--accent);color:var(--accent)}}
.hero{{padding:52px 32px 44px;border-bottom:1px solid var(--border);background:var(--surface);position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-80px;right:-80px;width:320px;height:320px;background:var(--accent);opacity:.05;border-radius:50%;pointer-events:none}}
.hero-inner{{max-width:880px;margin:0 auto;position:relative}}
.data-badge{{display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:600;background:{badge_bg};color:var(--accent);border:1px solid var(--accent);padding:3px 11px;border-radius:99px;margin-bottom:16px;text-transform:uppercase;letter-spacing:.6px}}
.hero h1{{font-size:clamp(1.8rem,4vw,2.6rem);font-weight:700;line-height:1.15;margin-bottom:10px;color:var(--text)}}
.hero p{{font-size:1rem;color:var(--muted);max-width:680px;margin-bottom:20px;line-height:1.7}}
.tools{{display:flex;gap:7px;flex-wrap:wrap}}
.tool-badge{{font-size:10.5px;font-weight:500;padding:2px 9px;border-radius:99px;background:{badge_bg};border:1px solid var(--border);color:var(--muted)}}
.container{{max-width:880px;margin:0 auto;padding:34px 32px}}
.finding-box{{padding:16px 20px;margin-bottom:30px;border-radius:0 10px 10px 0;border-left:4px solid var(--accent);background:{overlay_bg};border-top:1px solid var(--border);border-right:1px solid var(--border);border-bottom:1px solid var(--border);font-size:13px;line-height:1.7;color:var(--muted)}}
.finding-box strong{{color:var(--accent)}}
.section-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:12px}}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:11px;margin-bottom:34px}}
.kpi{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 18px;{card_shadow}}}
.kpi-label{{font-size:9.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:500;margin-bottom:7px}}
.kpi-value{{font-size:1.65rem;font-weight:700;line-height:1.1}}
.charts-grid{{display:grid;grid-template-columns:1fr;gap:16px;margin-bottom:34px}}
.chart-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;{card_shadow}}}
.chart-header{{padding:14px 18px 0}}
.chart-title{{font-size:13px;font-weight:600;color:var(--text);margin-bottom:2px}}
.chart-sub{{font-size:10.5px;color:var(--muted);margin-bottom:10px}}
.chart-card img{{width:100%;display:block}}
.source-box{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px 22px;margin-bottom:22px;{card_shadow}}}
.source-box h3{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin-bottom:8px}}
.source-box p{{font-size:12.5px;color:var(--muted);line-height:1.7}}
.source-box a{{color:var(--accent);text-decoration:none}}
footer{{text-align:center;padding:22px;font-size:11px;color:var(--muted);border-top:1px solid var(--border)}}
footer a{{color:var(--accent);text-decoration:none}}
::-webkit-scrollbar{{width:4px}}
::-webkit-scrollbar-track{{background:var(--bg)}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
</style>
</head>
<body>
<header class="header">
  <div class="header-left">
    <div class="proj-badge">P{project_number}</div>
    <div class="header-title">{project_title} <span>{project_subtitle}</span></div>
  </div>
  <nav class="nav-links">
    <a href="{github_url}" target="_blank" class="btn">GitHub</a>
    <a href="{data_source_url}" target="_blank" class="btn">Data Source</a>
  </nav>
</header>
<section class="hero">
  <div class="hero-inner">
    <div class="data-badge">Real Gov Data — {data_source}</div>
    <h1>{project_title}</h1>
    <p>{summary_text}</p>
    <div class="tools">{tool_html}</div>
  </div>
</section>
<div class="container">
  <div class="finding-box"><strong>Summary:</strong> {summary_text}</div>
  <div class="section-label">Key Findings</div>
  <div class="kpi-grid">{kpi_html}</div>
  <div class="section-label">Charts &amp; Analysis</div>
  <div class="charts-grid">{chart_html}</div>
  <div class="source-box">
    <h3>Data Source</h3>
    <p><strong>{data_source}</strong> — <a href="{data_source_url}" target="_blank">{data_source_url}</a><br>
    All data is real, publicly available government data. Free to download and verify independently.</p>
  </div>
</div>
<footer>
  <a href="{github_url}" target="_blank">GitHub</a> &nbsp;·&nbsp;
  Data: <a href="{data_source_url}" target="_blank">{data_source}</a> (public domain) &nbsp;·&nbsp;
  Divyadhole &nbsp;·&nbsp; Project {project_number} of 40
</footer>
</body>
</html>"""

    out = f"{output_dir}/index.html"
    with open(out,"w") as f: f.write(html)
    print(f"  ✓ Website → {out}  [theme: {theme_name}]")
    print(f"  ✓ Live at: {pages_url}")
    return out
