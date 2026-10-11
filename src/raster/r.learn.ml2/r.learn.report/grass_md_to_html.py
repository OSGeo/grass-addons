#!/usr/bin/env python3
"""
grass_md_to_html.py

Convert a GRASS manual page written in Markdown into the HTML fragment style
used by GRASS manual pages (e.g. the i.omnicloudmask / r.omnicloudmask pages).

Conventions reproduced:
  - '##'  -> <h2>UPPERCASE-AS-WRITTEN</h2>, '###' -> <h3>...</h3>
  - The first paragraph after a heading has NO leading <p>; subsequent
    paragraphs open with a bare <p> on its own line, content on the next line,
    and NO closing </p>.
  - Fenced code blocks ```...``` -> <div class="code"><pre>...</pre></div>
  - Inline: *text* -> <i>text</i>, **text** -> <b>text</b>,
    `code` -> <tt>code</tt>
  - Markdown links [text](url) -> <a href="url">text</a>
  - Markdown tables -> <table border="1"> with <th> header row
  - '- ' / '* ' lists -> <ul><li>...</li></ul>
  - >=, <=, & escaped to &gt;=, &lt;=, &amp; *outside* code spans
    (inside <tt>/<pre> they are escaped too, since they are literal text).

Usage:
    python3 grass_md_to_html.py input.md [output.html]
    cat input.md | python3 grass_md_to_html.py - > output.html
"""

import re
import sys


# --------------------------------------------------------------------------- #
# Inline conversion
# --------------------------------------------------------------------------- #
def escape_html(text):
    """Escape &, <, > for literal text (used inside code spans / blocks)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def convert_inline(text):
    """Convert inline Markdown to HTML, protecting `code` spans first."""
    placeholders = []

    def stash(html):
        placeholders.append(html)
        return f"\x00{len(placeholders) - 1}\x00"

    # 1. Inline code `...` -> <tt>...</tt> (escaped, stashed so later rules skip)
    def code_repl(m):
        return stash("<tt>" + escape_html(m.group(1)) + "</tt>")

    text = re.sub(r"`([^`]+)`", code_repl, text)

    # 2. Links [text](url) -> <a href="url">text</a> (stash to protect content)
    def link_repl(m):
        label = m.group(1)
        url = m.group(2)
        return stash(f'<a href="{url}">{label}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)

    # 3. Escape bare &, <, > in the remaining prose
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 4. Bold **text** -> <b>text</b>  (before single-* emphasis)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    # 5. Emphasis *text* -> <i>text</i>
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)

    # 6. Restore stashed code/link placeholders
    def restore(m):
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00(\d+)\x00", restore, text)
    return text


# --------------------------------------------------------------------------- #
# Block-level conversion
# --------------------------------------------------------------------------- #
def split_table_row(line):
    """Split a Markdown table row into cell strings, honouring escaped pipes."""
    line = line.strip().strip("|")
    # split on unescaped pipes
    cells = re.split(r"(?<!\\)\|", line)
    return [c.replace("\\|", "|").strip() for c in cells]


def is_table_separator(line):
    return bool(re.match(r"^\s*\|?[\s:|-]+\|?\s*$", line)) and "-" in line


def convert(md_text):
    lines = md_text.splitlines()
    out = []
    i = 0
    n = len(lines)

    # Tracks whether the next paragraph directly follows a heading (no <p>).
    after_heading = False

    while i < n:
        line = lines[i]

        # ---- Fenced code block ------------------------------------------- #
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            i += 1
            code_lines = []
            while i < n and not re.match(r"^```\s*$", lines[i]):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append('<div class="code">')
            out.append("  <pre>")
            for cl in code_lines:
                out.append(escape_html(cl))
            out.append("</pre>")
            out.append("</div>")
            out.append("")
            after_heading = False
            continue

        # ---- Heading ----------------------------------------------------- #
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            tag = "h2" if level <= 2 else "h3" if level == 3 else "h4"
            out.append(f"<{tag}>{convert_inline(m.group(2).strip())}</{tag}>")
            out.append("")
            after_heading = True
            i += 1
            continue

        # ---- Blank line -------------------------------------------------- #
        if line.strip() == "":
            i += 1
            continue

        # ---- Table ------------------------------------------------------- #
        if "|" in line and i + 1 < n and is_table_separator(lines[i + 1]):
            header = split_table_row(line)
            i += 2  # skip header + separator
            body = []
            while i < n and "|" in lines[i] and lines[i].strip() != "":
                body.append(split_table_row(lines[i]))
                i += 1
            out.append('<table border="1">')
            out.append("  <tr>")
            for h in header:
                out.append(f"    <th>{convert_inline(h)}</th>")
            out.append("  </tr>")
            for row in body:
                out.append("  <tr>")
                for cell in row:
                    out.append(f"    <td>{convert_inline(cell)}</td>")
                out.append("  </tr>")
            out.append("</table>")
            out.append("")
            after_heading = False
            continue

        # ---- List -------------------------------------------------------- #
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                # gather continuation lines (indented, non-blank, not new item)
                item = re.sub(r"^\s*[-*]\s+", "", lines[i])
                i += 1
                while (
                    i < n
                    and lines[i].strip() != ""
                    and not re.match(r"^\s*[-*]\s+", lines[i])
                    and not re.match(r"^#{1,6}\s", lines[i])
                    and not re.match(r"^```", lines[i])
                ):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(item)
            out.append("<ul>")
            for it in items:
                out.append(f"  <li>{convert_inline(it)}</li>")
            out.append("</ul>")
            out.append("")
            after_heading = False
            continue

        # ---- Paragraph --------------------------------------------------- #
        para = [line]
        i += 1
        while (
            i < n
            and lines[i].strip() != ""
            and not re.match(r"^#{1,6}\s", lines[i])
            and not re.match(r"^```", lines[i])
            and not re.match(r"^\s*[-*]\s+", lines[i])
            and not ("|" in lines[i] and i + 1 < n and is_table_separator(lines[i + 1]))
        ):
            para.append(lines[i])
            i += 1
        para_html = convert_inline(" ".join(s.strip() for s in para))
        if not after_heading:
            out.append("<p>")
        out.append(para_html)
        out.append("")
        after_heading = False

    # collapse trailing blank lines to a single newline
    text = "\n".join(out).rstrip() + "\n"
    return text


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv):
    if len(argv) < 2:
        sys.stderr.write(
            "Usage: python grass_md_to_html.py input.md [output.html]\n"
            "       cat input.md | python grass_md_to_html.py - > output.html\n"
        )
        return 1

    src = argv[1]
    md_text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    html = convert(md_text)

    if len(argv) >= 3:
        with open(argv[2], "w", encoding="utf-8") as f:
            f.write(html)
    else:
        sys.stdout.write(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
