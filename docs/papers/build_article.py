#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the 6,000-word article's HTML from markdown, reusing the stylesheet
(and the base64-embedded Vazirmatn fonts) of the long-form paper.

Usage: python3 build_article.py <source.md> <out.html> [<style-source.html>]
"""
import html
import os
import re
import sys

SRC = sys.argv[1]
OUT = sys.argv[2]
STYLE_SRC = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "selective-citation-pathology.html")

KIND_LINE = "پژوهش\u200cنامهٔ علمی–پژوهشی · روش\u200cشناسیِ استناد به متنِ مقدس"


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    return t


def convert(md):
    lines = md.split("\n")
    out, toc, i, n = [], [], 0, 0
    in_quote = in_ul = in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>"); in_ul = False
        if in_ol:
            out.append("</ol>"); in_ol = False

    def special(s):
        return (not s.strip() or s.startswith("#") or s.startswith(">") or s.startswith("|")
                or re.match(r"^---+\s*$", s) or re.match(r"^[-*]\s+", s)
                or re.match(r"^([۰-۹0-9]+)[.)]\s+", s))

    while i < len(lines):
        raw = lines[i].rstrip()

        # ---- table
        if raw.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-\|]+\|$", lines[i + 1].strip()):
            close_lists()
            head = [c.strip() for c in raw.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            # merge blank leading cells so group labels span their rows
            spans, skip, k = {}, set(), 0
            while k < len(rows):
                if rows[k] and rows[k][0]:
                    n = 1
                    while k + n < len(rows) and (not rows[k + n] or not rows[k + n][0]):
                        n += 1
                    spans[k] = n
                    skip.update(range(k + 1, k + n))
                    k += n
                else:
                    k += 1
            t = ["<table><thead><tr>"]
            t += ["<th>%s</th>" % inline(c) for c in head]
            t.append("</tr></thead><tbody>")
            for ri, r in enumerate(rows):
                if ri in skip:
                    r = r[1:]
                cells = ["<td>%s</td>" % inline(c) for c in r]
                if ri in spans and spans[ri] > 1:
                    cells[0] = '<td rowspan="%d" class="grp">%s</td>' % (
                        spans[ri], inline(r[0]))
                t.append("<tr>" + "".join(cells) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            i = j
            continue

        # ---- heading
        m = re.match(r"^(#{1,4})\s+(.*)$", raw)
        if m:
            close_lists()
            level, txt = len(m.group(1)), m.group(2).strip()
            n += 1
            anchor = "h%d" % n
            if level in (3, 4):
                toc.append((level, txt, anchor))
            out.append('<h%d id="%s">%s</h%d>' % (level, anchor, inline(txt), level))
            i += 1
            continue

        if re.match(r"^---+\s*$", raw):
            close_lists()
            i += 1
            continue

        # ---- blockquote
        if raw.startswith(">"):
            if not in_quote:
                close_lists()
                out.append("<blockquote>")
                in_quote = True
            content = raw[1:].strip()
            if content:
                out.append("<p>%s</p>" % inline(content))
            i += 1
            continue
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

        # ---- lists
        mub = re.match(r"^[-*]\s+(.*)$", raw)
        mob = re.match(r"^([۰-۹0-9]+)[.)]\s+(.*)$", raw)
        if mub:
            if not in_ul:
                close_lists(); out.append("<ul>"); in_ul = True
            out.append("<li>%s</li>" % inline(mub.group(1)))
            i += 1
            continue
        if mob:
            if not in_ol:
                close_lists(); out.append("<ol>"); in_ol = True
            out.append('<li><span class="num">%s.</span> %s</li>' % (mob.group(1), inline(mob.group(2))))
            i += 1
            continue

        close_lists()
        if not raw.strip():
            i += 1
            continue

        # ---- paragraph
        buf, j = [raw.strip()], i + 1
        while j < len(lines) and not special(lines[j].rstrip()):
            buf.append(lines[j].strip())
            j += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
        i = j

    if in_quote:
        out.append("</blockquote>")
    close_lists()
    return "\n".join(out), toc


def main():
    md = open(SRC, encoding="utf-8").read()
    body, toc = convert(md)

    m = re.search(r'<h1 id="[^"]*">(.*?)</h1>', body)
    title = m.group(1) if m else "مقاله"
    body = body[:m.start()] + body[m.end():]

    sub_m = re.search(r'<h2 id="[^"]*">(.*?)</h2>', body)
    subtitle = sub_m.group(1) if sub_m else ""
    if sub_m:
        body = body[:sub_m.start()] + body[sub_m.end():]

    # table of contents: sections (h3) bold, subsections (h4) indented; skip subtitle
    plain_sub = re.sub("<[^>]+>", "", subtitle)
    items = []
    for level, txt, anchor in toc:
        if txt == plain_sub:
            continue
        items.append((level, txt, anchor))
    toc_html = ['<nav class="toc"><h2>فهرست مطالب</h2>']
    for level, txt, anchor in items:
        cls = ' class="l3"' if level == 4 else ""
        toc_html.append('<a href="#%s"%s>%s</a>' % (anchor, cls, inline(txt)))
    toc_html.append("</nav>")

    style = open(STYLE_SRC, encoding="utf-8").read()
    s_i, s_j = style.find("<style>"), style.find("</style>") + len("</style>")
    style_block = style[s_i:s_j]

    doc = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>

<title>%s</title>
%s
</head>
<body>
<div class="page">
<header class="title-block">
<h1>%s</h1>
<div class="sub">%s</div>
<div class="kind">%s</div>
</header>
%s
%s
</div>
</body>
</html>
""" % (re.sub("<[^>]+>", "", title), style_block, title, subtitle, KIND_LINE,
       "\n".join(toc_html), body)

    # table overrides — must come after the inherited stylesheet
    doc = doc.replace("</head>", """<style>
/* tables: right-to-left grid, right-aligned cells */
table{direction:rtl;table-layout:auto}
th,td{text-align:right}
th{text-align:right}
td.grp{font-weight:600;background:#f6f9f8;vertical-align:middle;text-align:right}
</style>
</head>""", 1)

    # English abstract in LTR box
    idx = doc.find(">Abstract</h2>")
    if idx != -1:
        start = doc.rfind('<h2 id="', 0, idx)
        head, tail = doc[:start], doc[start:]
        tail = tail.replace("</div>\n</body>\n</html>\n", "")
        doc = (head + '<div class="ltr">' + tail
               + "</div>\n</div>\n</body>\n</html>\n")

    open(OUT, "w", encoding="utf-8").write(doc)
    print("wrote", OUT, os.path.getsize(OUT), "bytes;", len(items), "toc entries")


if __name__ == "__main__":
    main()
