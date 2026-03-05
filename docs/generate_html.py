"""Convert a Markdown file to printable HTML with Mermaid diagram support.

Usage: python generate_html.py [input.md]
Default: converts all .md files in the same directory.
"""
import re
import sys
import markdown
from pathlib import Path


def convert(md_path: Path):
    html_path = md_path.with_suffix(".html")
    md_text = md_path.read_text(encoding="utf-8")
    title = md_path.stem.replace("_", " ")

    # Extract mermaid blocks before markdown processing
    mermaid_blocks = {}
    counter = 0

    def replace_mermaid(match):
        nonlocal counter
        key = f"MERMAID_PLACEHOLDER_{counter}"
        mermaid_blocks[key] = match.group(1).strip()
        counter += 1
        return f"\n\n{key}\n\n"

    md_text = re.sub(r"```mermaid\n(.*?)```", replace_mermaid, md_text, flags=re.DOTALL)

    # Convert markdown to HTML
    html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])

    # Restore mermaid blocks as <pre class="mermaid"> elements
    for key, diagram in mermaid_blocks.items():
        html_body = html_body.replace(f"<p>{key}</p>", f'<pre class="mermaid">{diagram}</pre>')
        html_body = html_body.replace(key, f'<pre class="mermaid">{diagram}</pre>')

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px 40px;
    color: #24292e;
    line-height: 1.6;
    font-size: 14px;
  }}
  h1 {{ border-bottom: 2px solid #0366d6; padding-bottom: 8px; font-size: 28px; }}
  h2 {{ border-bottom: 1px solid #eaecef; padding-bottom: 6px; margin-top: 32px; font-size: 22px; color: #0366d6; }}
  h3 {{ margin-top: 24px; font-size: 17px; }}
  h4 {{ font-size: 15px; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 13px;
  }}
  th, td {{
    border: 1px solid #dfe2e5;
    padding: 6px 12px;
    text-align: left;
  }}
  th {{
    background: #f1f3f5;
    font-weight: 600;
  }}
  tr:nth-child(even) {{ background: #f8f9fa; }}
  code {{
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 13px;
  }}
  pre {{
    background: #f6f8fa;
    padding: 12px 16px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 13px;
    border: 1px solid #e1e4e8;
  }}
  pre.mermaid {{
    background: white;
    text-align: center;
    border: 1px solid #e1e4e8;
    padding: 20px;
  }}
  hr {{ border: none; border-top: 1px solid #eaecef; margin: 24px 0; }}

  @media print {{
    body {{ font-size: 11px; padding: 0; max-width: 100%; }}
    h1 {{ font-size: 22px; }}
    h2 {{ font-size: 17px; page-break-before: auto; }}
    h3 {{ font-size: 14px; }}
    table {{ font-size: 10px; }}
    pre {{ font-size: 10px; }}
    pre.mermaid {{ page-break-inside: avoid; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>

<div class="no-print" style="background:#0366d6;color:white;padding:12px 20px;border-radius:6px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;">
  <span>{title}</span>
  <button onclick="window.print()" style="background:white;color:#0366d6;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;font-weight:bold;">
    Imprimir / Guardar PDF
  </button>
</div>

{html_body}

<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose',
    flowchart: {{ useMaxWidth: true, htmlLabels: true }},
  }});
</script>
</body>
</html>
"""

    html_path.write_text(html_doc, encoding="utf-8")
    print(f"HTML generado: {html_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        convert(Path(sys.argv[1]))
    else:
        docs_dir = Path(__file__).parent
        for md in sorted(docs_dir.glob("*.md")):
            convert(md)
