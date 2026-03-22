import sqlite3
import os
import webbrowser

DB_PATH = "phishguard.db"
OUTPUT_HTML = "db_viewer.html"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

def build_table_html(table_name):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]

    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [c[1] for c in cursor.fetchall()]

    cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 100")
    rows = cursor.fetchall()

    header_html = "".join(f"<th>{c}</th>" for c in cols)
    rows_html = ""
    if rows:
        for row in rows:
            cells = "".join(f"<td>{str(v) if v is not None else '<span class=\"null\">NULL</span>'}</td>" for v in row)
            rows_html += f"<tr>{cells}</tr>"
    else:
        rows_html = f'<tr><td colspan="{len(cols)}" class="empty">— No records —</td></tr>'

    return f"""
    <div class="table-section" id="table-{table_name}">
        <div class="table-header">
            <span class="table-icon">🗂</span>
            <span class="table-name">{table_name}</span>
            <span class="row-badge">{count} rows</span>
        </div>
        <div class="table-wrapper">
            <table>
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>
    """

nav_links = "".join(
    f'<a href="#table-{t}" class="nav-link">{t}</a>' for t in tables
)
tables_html = "".join(build_table_html(t) for t in tables)
conn.close()

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PhishGuard DB Viewer</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', sans-serif;
    background: #0d1117;
    color: #e6edf3;
    min-height: 100vh;
  }}

  .topbar {{
    background: linear-gradient(135deg, #1a2332, #0d1117);
    border-bottom: 1px solid #21262d;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
  }}

  .topbar .logo {{
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #bc8cff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
  }}

  .topbar .db-name {{
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 5px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #8b949e;
  }}

  .layout {{
    display: flex;
    min-height: calc(100vh - 61px);
  }}

  .sidebar {{
    width: 220px;
    background: #161b22;
    border-right: 1px solid #21262d;
    padding: 20px 0;
    position: sticky;
    top: 61px;
    height: calc(100vh - 61px);
    overflow-y: auto;
    flex-shrink: 0;
  }}

  .sidebar-title {{
    font-size: 11px;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0 20px 12px;
  }}

  .nav-link {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 20px;
    color: #c9d1d9;
    text-decoration: none;
    font-size: 13.5px;
    font-weight: 500;
    transition: all 0.15s;
    border-left: 2px solid transparent;
  }}

  .nav-link:hover {{
    background: #21262d;
    color: #58a6ff;
    border-left-color: #58a6ff;
  }}

  .nav-link::before {{
    content: '▸';
    font-size: 10px;
    color: #58a6ff;
    opacity: 0.6;
  }}

  .main {{
    flex: 1;
    padding: 32px;
    overflow: auto;
  }}

  .table-section {{
    margin-bottom: 40px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    overflow: hidden;
  }}

  .table-header {{
    padding: 16px 24px;
    background: linear-gradient(135deg, #1c2230, #161b22);
    border-bottom: 1px solid #21262d;
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .table-icon {{ font-size: 18px; }}

  .table-name {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 600;
    color: #58a6ff;
  }}

  .row-badge {{
    background: #1f6feb33;
    border: 1px solid #1f6feb66;
    color: #58a6ff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-left: auto;
  }}

  .table-wrapper {{
    overflow-x: auto;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}

  thead tr {{
    background: #0d1117;
  }}

  thead th {{
    padding: 12px 16px;
    text-align: left;
    font-size: 11.5px;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid #21262d;
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
  }}

  tbody tr {{
    border-bottom: 1px solid #21262d;
    transition: background 0.1s;
  }}

  tbody tr:last-child {{ border-bottom: none; }}

  tbody tr:hover {{ background: #1c2230; }}

  tbody td {{
    padding: 11px 16px;
    color: #e6edf3;
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
  }}

  .null {{
    color: #484f58;
    font-style: italic;
    font-family: 'Inter', sans-serif;
  }}

  .empty {{
    text-align: center;
    padding: 40px;
    color: #484f58;
    font-style: italic;
    font-family: 'Inter', sans-serif;
  }}
</style>
</head>
<body>
<div class="topbar">
  <div class="logo">⚡ PhishGuard</div>
  <div class="db-name">phishguard.db</div>
</div>
<div class="layout">
  <nav class="sidebar">
    <div class="sidebar-title">Tables</div>
    {nav_links}
  </nav>
  <main class="main">
    {tables_html}
  </main>
</div>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] Viewer saved to: {os.path.abspath(OUTPUT_HTML)}")
webbrowser.open("file:///" + os.path.abspath(OUTPUT_HTML).replace("\\", "/"))
print("[OK] Opened in browser!")
