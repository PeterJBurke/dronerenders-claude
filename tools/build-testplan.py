#!/usr/bin/env python3
"""Build fc/testplan.html from the StackF765 verification plan (Markdown).

    python3 tools/build-testplan.py /path/to/test-plan.md

Needs the Python `markdown` module. The page is static: all conversion happens here.
The summary and the prioritised work list are put first; the long sections follow,
each in a collapsible block. Server-local paths in the source are generalised.
"""
import html
import re
import sys
from pathlib import Path

import markdown

OUT = Path(__file__).resolve().parent.parent / "fc" / "testplan.html"

# Server-local paths in the source, replaced before conversion. Each must match exactly once.
PATH_EDITS = [
    ("as committed in `/root/fcclaude` (HEAD `0a44bf2`)",
     "as committed in the StackF765 design repository (HEAD `0a44bf2`)"),
    ("`/root/fcclaude-build/ardupilot`, commit `a995235`",
     "local checkout, commit `a995235`"),
    ("10-2020-q4 under `/root/fc/tools/` (read-only tree)",
     "10-2020-q4, in a separate read-only tools tree"),
    ("are in\n`/tmp/claude-0/-root-fcclaude/3115490e-4cef-411f-8226-519a0fbe1e45/scratchpad/testplan/` "
     "(`lower.py`, `upper.py`, `ngtest.py`).",
     "are in a temporary scratch folder on the build server, not in the repository "
     "(`lower.py`, `upper.py`, `ngtest.py`)."),
]

CSS = """
:root{--bg:#f7f8f9;--fg:#15181c;--muted:#4e5661;--panel:#fff;--line:#c3c8cf}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
body .page-links{position:static;display:flex;flex-wrap:wrap;gap:6px;padding:14px}
main{max-width:820px;margin:0 auto;padding:4px 16px 40px}
h1{font-size:24px;line-height:1.25;margin:10px 0 6px}
h2{font-size:18px;margin:30px 0 8px;padding-top:14px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:22px 0 6px}
p{margin:8px 0}
.lead{color:var(--muted)}
ol,ul{margin:8px 0;padding-left:24px}
li{margin:5px 0}
main a{color:#126596;overflow-wrap:anywhere}
code{font:13px ui-monospace,Menlo,Consolas,monospace;background:#e9edf1;padding:1px 4px;border-radius:3px;overflow-wrap:anywhere}
.scroll{overflow-x:auto;margin:10px 0;-webkit-overflow-scrolling:touch}
.scroll.wide{width:max(100%,min(1240px,calc(100vw - 48px)));margin-left:50%;transform:translateX(-50%)}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--panel)}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:#e6edf5;color:#29425b;font-weight:600}
table.c6{min-width:900px}
table.c8{min-width:1500px;font-size:13px}
table.c8 code{font-size:12px}
.warn{background:#fff0d5;color:#5c3400;border:1px solid #e3c48b;border-radius:6px;padding:9px 12px;margin:12px 0}
.small{font-size:13px;color:var(--muted)}
.tag{font-size:12px;color:#29425b;background:#e6edf5;border-radius:3px;padding:0 4px;white-space:nowrap}
.tag.inf{color:#5c3400;background:#fff0d5}
.tag.long{white-space:normal}
nav.toc{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:8px 12px;margin:12px 0;font-size:14px}
nav.toc ul{margin:4px 0;columns:2;column-gap:28px;list-style:none;padding-left:0}
nav.toc ul ul{columns:1;padding-left:14px}
nav.toc li{margin:3px 0;break-inside:avoid}
.tools{display:flex;gap:6px;margin:8px 0}
.tools button{font:12px system-ui;color:var(--fg);background:var(--panel);border:1px solid var(--line);padding:6px 10px;border-radius:6px;cursor:pointer}
details.sec{border-top:1px solid var(--line);margin:0;padding:10px 0}
details.sec.sub{border-top:1px dashed var(--line);padding:8px 0}
details.sec>summary{cursor:pointer;font-weight:600;font-size:18px;padding:4px 0}
details.sec.sub>summary{font-size:16px}
details.sec>summary:hover{color:#126596}
h2.group{margin-bottom:4px}
@media(max-width:600px){h1{font-size:21px}table{font-size:13px}th,td{padding:5px}nav.toc ul{columns:1}details.sec>summary{font-size:16px}details.sec.sub>summary{font-size:15px}}
@media print{details.sec>*{display:block}.tools{display:none}}
""".strip()

JS = """
(function(){
function openFor(id){var e=id&&document.getElementById(id);if(!e)return;
for(var d=e;d;d=d.parentElement){if(d.tagName==='DETAILS')d.open=true}
e.scrollIntoView()}
function fromHash(){openFor(decodeURIComponent(location.hash.slice(1)))}
addEventListener('hashchange',fromHash);if(location.hash)fromHash();
function all(v){document.querySelectorAll('details.sec').forEach(function(d){d.open=v})}
document.getElementById('openAll').onclick=function(){all(true)};
document.getElementById('closeAll').onclick=function(){all(false)};
})();
""".strip()

NAV = ('<div class="page-links"><a href="./">Drone</a><a href="board.html">Board</a>'
       '<a href="handsolder.html">Hand soldering</a>'
       '<a aria-current="page" href="testplan.html">Test plan</a></div>')

NOTICE = (
    '<div class="warn"><b>Status on 2026-11-25: this is a plan, not a set of results.</b> '
    'None of the analysis described here has been run, and no design file was changed. '
    'The “top risks” are one reviewer’s reading of the design files. '
    'They have not been confirmed by simulation, by measurement or by a second reviewer, '
    'and some may turn out to be wrong.</div>'
)


def convert(md_text):
    out = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    # Tables: scroll inside their own container; wide ones get a minimum width.
    def table(m):
        body = m.group(0)
        cols = body[: body.index("</tr>")].count("<th")
        cls = "c8" if cols >= 8 else "c6" if cols >= 6 else ""
        wrap = "scroll wide" if cols >= 6 else "scroll"
        if cls:
            body = body.replace("<table>", f'<table class="{cls}">', 1)
        return f'<div class="{wrap}">{body}</div>'
    out = re.sub(r"<table>.*?</table>", table, out, flags=re.S)
    # Bare URLs become links (the source has no Markdown links).
    out = re.sub(r'(?<!["=>])(https?://[^\s<]+)',
                 lambda m: f'<a href="{m.group(1)}" rel="noopener">{m.group(1)}</a>', out)
    # Evidence labels.
    def tag(m):
        cls = "tag"
        if m.group(1) == "inference":
            cls += " inf"
        if len(m.group(0)) > 24:
            cls += " long"
        return f'<span class="{cls}">{m.group(0)}</span>'
    out = re.sub(r"\[(measured|doc|inference|web|recall)\b(?:[^\]<]|<code>[^<]*</code>)*\]", tag, out)
    return out


def split(text, level):
    """Split on headings of the given level: [(title, body), ...] with a leading (None, preamble)."""
    parts = re.split(rf"^{'#' * level} (.+)$", text, flags=re.M)
    res = [(None, parts[0])]
    for i in range(1, len(parts), 2):
        res.append((parts[i].strip(), parts[i + 1]))
    return res


def clean(body):
    return re.sub(r"^---\s*$", "", body, flags=re.M).strip()


def inline(title):
    out = convert(re.sub(r"^(\d+)\. ", r"\1\\. ", title))  # not an ordered list
    assert out.startswith("<p>") and out.endswith("</p>"), out
    return out[3:-4]


def main():
    src = Path(sys.argv[1]).read_text(encoding="utf-8")
    for old, new in PATH_EDITS:
        if src.count(old) != 1:
            sys.exit(f"path edit does not match exactly once: {old!r}")
        src = src.replace(old, new)
    if re.search(r"/root/|/tmp/|/home/", src):
        sys.exit("server-local path left in the source")

    top = split(src, 2)
    preamble = clean(top[0][1])
    h1 = re.match(r"# (.+)\n", preamble).group(1)
    preamble = preamble[preamble.index("\n"):].strip()
    secs = {}
    for title, body in top[1:]:
        num = title.split(".")[0]
        secs[num] = (title, clean(body))

    page = []
    page.append(f"<h1>StackF765: {html.escape(h1.replace('StackF765 ', ''))}</h1>")
    page.append(NOTICE)
    page.append(convert(preamble))
    page.append('<p class="small">First on this page: the summary and the prioritised work list. '
                'The evidence and the detailed plan follow under <a href="#detail">Detailed sections</a>.</p>')

    # Shown in full: 1 (summary, top five risks, first five actions) and 3 (prioritised list).
    for num in ("1", "3"):
        title, body = secs[num]
        page.append(f'<h2 id="s{num}">{inline(title)}</h2>')
        body = re.sub(r"^### (\d\.\d) (.+)$", lambda m: f'<h3 id="s{m.group(1).replace(".", "-")}">{m.group(1)} {m.group(2)}</h3>',
                      body, flags=re.M)
        page.append(convert(body))

    # The rest: collapsible, with a table of contents.
    toc = []
    blocks = []
    for num in ("2", "4", "5", "6", "7", "8", "9", "10"):
        title, body = secs[num]
        if num == "5":
            subs = split(body, 3)
            toc.append(f'<li><a href="#s5">{inline(title)}</a><ul>')
            blocks.append(f'<h2 class="group" id="s5">{inline(title)}</h2>')
            blocks.append(convert(clean(subs[0][1])))
            for st, sb in subs[1:]:
                sid = "s" + st.split(" ")[0].replace(".", "").lower()  # s5a ...
                toc.append(f'<li><a href="#{sid}">{inline(st)}</a></li>')
                blocks.append(f'<details class="sec sub" id="{sid}"><summary>{inline(st)}</summary>'
                              f'{convert(clean(sb))}</details>')
            toc.append("</ul></li>")
        else:
            toc.append(f'<li><a href="#s{num}">{inline(title)}</a></li>')
            opened = " open" if num == "2" else ""
            blocks.append(f'<details class="sec" id="s{num}"{opened}><summary>{inline(title)}</summary>'
                          f'{convert(body)}</details>')

    page.append('<h2 id="detail">Detailed sections</h2>')
    page.append('<nav class="toc" aria-label="Detailed sections"><ul>' + "".join(toc) + "</ul></nav>")
    page.append('<div class="tools"><button id="openAll" type="button">Open all</button>'
                '<button id="closeAll" type="button">Close all</button></div>')
    page.extend(blocks)
    page.append('<p class="small">Section numbers are those of the original plan; sections 1 and 3 are at the top of this page. '
                'Design files: <a href="https://github.com/PeterJBurke/stackf765" rel="noopener">PeterJBurke/stackf765</a>. '
                'No hardware built yet.</p>')

    doc = (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/>'
        '<meta content="width=device-width,initial-scale=1" name="viewport"/>'
        '<title>StackF765 — Test plan</title>\n'
        f"<style>\n{CSS}\n</style>"
        '<link href="assets/controls.css" rel="stylesheet"/></head><body>\n'
        f"{NAV}\n<main>\n" + "\n".join(page) + f"\n</main>\n<script>\n{JS}\n</script>\n</body></html>\n"
    )
    if re.search(r"/root/|/tmp/claude", doc):
        sys.exit("server-local path left in the page")
    OUT.write_text(doc, encoding="utf-8")
    print(f"wrote {OUT} ({len(doc)} bytes)")


if __name__ == "__main__":
    main()
