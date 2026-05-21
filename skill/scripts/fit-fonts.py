#!/usr/bin/env python3
"""
F8: Lightweight font-fit post-processor for .drawio files.

Scans every vertex cell, estimates whether the current `fontSize` causes text
to overflow the cell's geometry, and steps the fontSize down until the text
fits (or floor `--min` is hit). With `--mode grow` it also steps up when
the cell has spare room — useful for diagrams where ELK enlarged shapes.

Approach: character-width approximation. Assumes sans-serif default font,
treats `char_width ≈ 0.55 × fontSize` and `line_height ≈ 1.2 × fontSize`.
No PIL, no glyph metrics, no browser. ~150 LOC stdlib-only.

Pipeline order (per F5/F2 setup):
    skill emits .drawio
    → scripts/elk-layout.py    (changes cell w/h)
    → scripts/fit-fonts.py     (THIS — shrinks font to new size)
    → scripts/validate.py      (Q405 catches anything still overflowing)

Usage:
    python3 fit-fonts.py diagram.drawio                       # in-place, mode=auto
    python3 fit-fonts.py diagram.drawio --mode grow           # allow grow too
    python3 fit-fonts.py diagram.drawio --min 8 --max 18      # bounds
    python3 fit-fonts.py diagram.drawio --output fitted.drawio
    python3 fit-fonts.py diagram.drawio --features font_fit=off    # no-op
    python3 fit-fonts.py diagram.drawio --dry-run             # report, don't write

Modes:
    off      no changes
    auto     shrink only (default; respects designer intent, fixes overflow)
    grow     shrink and grow (use after ELK enlarges shapes)
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET


# ----- char-width heuristic -----
CHAR_W_RATIO = 0.55     # average sans-serif char width as fraction of fontSize
LINE_H_RATIO = 1.2      # line height = 1.2 × fontSize


def parse_style(style):
    """style string → dict."""
    kv = {}
    if not style:
        return kv
    for part in style.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
        elif part.strip():
            kv[part.strip()] = "1"
    return kv


def serialize_style(kv):
    return ";".join(f"{k}={v}" if v != "1" or k in ("html", "rounded", "html")
                    else k for k, v in kv.items())


def set_style_kv(style, key, value):
    """Set or replace a single key in a style string, preserving order."""
    parts = []
    found = False
    for part in style.split(";"):
        if not part:
            parts.append(part)
            continue
        if "=" in part:
            k, _ = part.split("=", 1)
            if k.strip() == key:
                parts.append(f"{key}={value}")
                found = True
                continue
        parts.append(part)
    if not found:
        parts.append(f"{key}={value}")
    return ";".join(parts)


def strip_html(s):
    """Remove HTML tags + entities, return plain text."""
    if not s:
        return ""
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&nbsp;", " ")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&[a-z]+;|&#x?[0-9a-f]+;", "", s, flags=re.IGNORECASE)
    return s.strip()


def split_lines(value):
    """Split label value on <br/>, <br>, \\n. Returns list of plain-text lines."""
    if not value:
        return []
    parts = re.split(r"<br\s*/?>|\n", value, flags=re.IGNORECASE)
    return [strip_html(p) for p in parts if strip_html(p)]


def cell_padding(style_kv):
    """Estimate inner padding from style — uses spacingLeft/Right/Top/Bottom or `spacing`."""
    sp = float(style_kv.get("spacing", 2))
    sl = float(style_kv.get("spacingLeft", sp))
    sr = float(style_kv.get("spacingRight", sp))
    st = float(style_kv.get("spacingTop", sp))
    sb = float(style_kv.get("spacingBottom", sp))
    return sl, sr, st, sb


def header_offset(style_kv):
    """Return reserved pixels for container header (swimlane / table startSize)."""
    if "swimlane" not in style_kv:
        return 0
    try:
        return float(style_kv.get("startSize", 20))
    except (TypeError, ValueError):
        return 20


def text_fits(lines, font_size, width, height, wrap):
    """True if all lines fit at given fontSize inside (width, height)."""
    if not lines:
        return True
    char_w = font_size * CHAR_W_RATIO
    line_h = font_size * LINE_H_RATIO
    if char_w <= 0 or line_h <= 0:
        return False

    if wrap:
        # Estimate wrapped line count per logical line
        total = 0
        max_chars_per_visual_line = max(1, int(width / char_w))
        for line in lines:
            chars = len(line)
            visual_lines = max(1, -(-chars // max_chars_per_visual_line))  # ceil div
            total += visual_lines
        return (total * line_h) <= height
    else:
        # No wrap: each logical line must fit on one row + total height OK
        if len(lines) * line_h > height:
            return False
        for line in lines:
            if len(line) * char_w > width:
                return False
        return True


def is_skippable(style_kv, geom):
    """Skip decorative text, edge labels, and zero-geom cells."""
    if not geom or geom[2] <= 0 or geom[3] <= 0:
        return True
    # style="text;..." → titles, chrome
    if "text" in style_kv and style_kv.get("text") == "1":
        return True
    # edgeLabel cells
    if style_kv.get("edgeLabel") == "1":
        return True
    return False


def fit_one_cell(cell, mode, min_size, max_size):
    """Adjust fontSize of one cell. Return (old_size, new_size) or (None, None) if skipped."""
    style = cell.get("style", "") or ""
    if not style:
        return None, None
    style_kv = parse_style(style)
    value = cell.get("value", "") or ""
    if not value.strip():
        return None, None

    g = cell.find("mxGeometry")
    if g is None:
        return None, None
    try:
        gw = float(g.get("width", 0))
        gh = float(g.get("height", 0))
    except (TypeError, ValueError):
        return None, None

    geom = (float(g.get("x", 0)), float(g.get("y", 0)), gw, gh)
    if is_skippable(style_kv, geom):
        return None, None

    # Wrap behavior
    wrap = style_kv.get("whiteSpace") == "wrap"

    # Available text area
    sl, sr, st, sb = cell_padding(style_kv)
    hdr = header_offset(style_kv)
    horizontal = style_kv.get("horizontal", "1") != "0"
    if "swimlane" in style_kv and not horizontal:
        avail_w = max(1.0, gw - hdr - sl - sr)
        avail_h = max(1.0, gh - st - sb)
    else:
        avail_w = max(1.0, gw - sl - sr)
        avail_h = max(1.0, gh - hdr - st - sb)

    lines = split_lines(value)
    if not lines:
        return None, None

    try:
        cur = int(float(style_kv.get("fontSize", 12)))
    except (TypeError, ValueError):
        cur = 12

    new = cur
    if not text_fits(lines, cur, avail_w, avail_h, wrap):
        # Shrink
        while new > min_size and not text_fits(lines, new, avail_w, avail_h, wrap):
            new -= 1
    elif mode == "grow":
        # Try grow — keep stepping up while still fits with 25% headroom
        while new < max_size:
            candidate = new + 1
            # Require room to spare so we don't bump up to edge of fit
            if text_fits(lines, candidate, avail_w * 0.85, avail_h * 0.85, wrap):
                new = candidate
            else:
                break

    if new == cur:
        return cur, cur
    cell.set("style", set_style_kv(style, "fontSize", str(new)))
    return cur, new


def main():
    ap = argparse.ArgumentParser(description="Lightweight font-fit post-processor for .drawio files")
    ap.add_argument("input", help="Source .drawio file")
    ap.add_argument("output", nargs="?", help="Output path (default: in-place)")
    ap.add_argument("--mode", choices=["off", "auto", "grow"], default="auto",
                    help="off: no-op; auto (default): shrink only; grow: shrink + grow")
    ap.add_argument("--min", type=int, default=8, dest="min_size")
    ap.add_argument("--max", type=int, default=18, dest="max_size")
    ap.add_argument("--features", default="",
                    help="Feature overrides: 'font_fit=off|auto|grow'")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report changes without writing")
    args = ap.parse_args()

    # --features overrides --mode
    mode = args.mode
    for part in args.features.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() == "font_fit":
                mode = v.strip()

    if mode == "off":
        print("font_fit=off — no-op.")
        sys.exit(0)
    if mode not in ("auto", "grow"):
        print(f"Unknown font_fit mode: {mode}", file=sys.stderr)
        sys.exit(2)

    tree = ET.parse(args.input)
    root = tree.getroot()

    n_scanned = 0
    n_shrunk = 0
    n_grew = 0
    n_unchanged = 0
    for cell in root.iter("mxCell"):
        if cell.get("vertex") != "1":
            continue
        old, new = fit_one_cell(cell, mode, args.min_size, args.max_size)
        if old is None:
            continue
        n_scanned += 1
        if new == old:
            n_unchanged += 1
        elif new < old:
            n_shrunk += 1
            print(f"  shrink {cell.get('id'):<24} {old} → {new}  ({strip_html(cell.get('value',''))[:40]})")
        else:
            n_grew += 1
            print(f"  grow   {cell.get('id'):<24} {old} → {new}  ({strip_html(cell.get('value',''))[:40]})")

    print()
    print(f"Scanned: {n_scanned}   Shrunk: {n_shrunk}   Grew: {n_grew}   Unchanged: {n_unchanged}")

    if args.dry_run:
        print("(dry-run — no file written)")
        sys.exit(0)

    out_path = args.output or args.input
    tree.write(out_path, encoding="utf-8", xml_declaration=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
