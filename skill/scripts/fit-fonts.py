#!/usr/bin/env python3
"""
F8: Lightweight font-fit post-processor for .drawio files.

Scans every vertex cell, estimates whether the current `fontSize` causes text
to overflow the cell's geometry, and steps the fontSize down until the text
fits (or floor `--min` is hit). With `--mode grow` it also steps up when
the cell has spare room — useful for diagrams where ELK enlarged shapes.

Approach: character-width approximation. Assumes sans-serif default font,
treats `char_width ≈ 0.55 × fontSize` and `line_height ≈ 1.2 × fontSize`.
No PIL, no glyph metrics, no browser. Stdlib-only.

Pipeline order (per F5/F2 setup):
    skill emits .drawio
    → scripts/elk-layout.py    (optional — changes cell w/h)
    → scripts/fit-fonts.py     (THIS — shrinks/grows font and/or cell)
    → scripts/validate.py      (Q405 catches anything still overflowing)

Usage:
    python3 fit-fonts.py diagram.drawio                       # in-place, mode=auto
    python3 fit-fonts.py diagram.drawio --mode grow           # allow grow too
    python3 fit-fonts.py diagram.drawio --min 8 --max 18      # bounds
    python3 fit-fonts.py diagram.drawio --output fitted.drawio
    python3 fit-fonts.py diagram.drawio --features font_fit=off    # no-op
    python3 fit-fonts.py diagram.drawio --dry-run             # report, don't write

    # Layout-mode-aware (new):
    python3 fit-fonts.py diagram.drawio --layout-mode off     # expand cells first, then shrink fonts
    python3 fit-fonts.py diagram.drawio --layout-mode neato   # same pre-pass as off
    python3 fit-fonts.py diagram.drawio --layout-mode elk     # back-compat: shrink only (or grow)
    python3 fit-fonts.py diagram.drawio --layout-mode auto    # infer from diagram (default)

    # With precomputed metrics from text-metrics.js:
    python3 fit-fonts.py diagram.drawio --layout-mode off --metrics diagram.annotated.plan.json

Modes (--mode):
    off      no changes
    auto     shrink only (default; respects designer intent, fixes overflow)
    grow     shrink and grow (use after ELK enlarges shapes)

Layout modes (--layout-mode):
    elk      ELK ran first — cells already optimally sized → shrink fonts only (back-compat)
    off      No layout optimizer ran — prefer expanding cells over shrinking fonts
    neato    Same as off (neato does overlap-removal, not size optimization)
    graphviz Same as off
    auto     (default) infer from diagram marker; fall back to elk for back-compat

CJK / emoji:
    The char-width heuristic mirrors the codepoint ranges in text-metrics.js
    (CJK ≈ 1.0 em, emoji ≈ 1.2 em). Provide --metrics for more accurate sizing.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import unicodedata


# ----- char-width heuristic -----
CHAR_W_RATIO = 0.55     # average sans-serif Latin char width as fraction of fontSize
LINE_H_RATIO = 1.2      # line height = 1.2 × fontSize

# CJK / emoji: (lo, hi, width_ratio_relative_to_fontSize)
# Mirrors CJK_RANGES in text-metrics.js (factor/11 × fontSize gives px width)
_CJK_RANGES = [
    (0x3040, 0x309F, 1.0),    # Hiragana
    (0x30A0, 0x30FF, 1.0),    # Katakana
    (0x3400, 0x4DBF, 1.0),    # CJK Extension A
    (0x4E00, 0x9FFF, 1.0),    # CJK Unified Ideographs
    (0xAC00, 0xD7AF, 1.0),    # Hangul Syllables
    (0xFF00, 0xFFEF, 1.0),    # Fullwidth Forms
    (0x2600, 0x27BF, 1.2),    # Misc Symbols / Dingbats
    (0x1F300, 0x1F9FF, 1.2),  # Emoji
]


def _char_width_ratio(ch):
    """Return width ratio (relative to fontSize) for a single character."""
    cp = ord(ch)
    for lo, hi, ratio in _CJK_RANGES:
        if lo <= cp <= hi:
            return ratio
    return CHAR_W_RATIO


def char_px_width(text, font_size):
    """Estimate pixel width of text at given fontSize."""
    return sum(_char_width_ratio(ch) * font_size for ch in text)


# ----- style helpers -----

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


# ----- text fitting -----

def text_fits(lines, font_size, width, height, wrap):
    """True if all lines fit at given fontSize inside (width, height)."""
    if not lines:
        return True
    line_h = font_size * LINE_H_RATIO
    if line_h <= 0:
        return False

    if wrap:
        total = 0
        for line in lines:
            line_px = char_px_width(line, font_size)
            visual_lines = max(1, -(-int(line_px) // max(1, int(width))))  # ceil div on px
            total += visual_lines
        return (total * line_h) <= height
    else:
        if len(lines) * line_h > height:
            return False
        for line in lines:
            if char_px_width(line, font_size) > width:
                return False
        return True


def required_dims(lines, font_size, wrap):
    """Compute (required_w, required_h) for text at given fontSize (no padding included)."""
    if not lines:
        return 0.0, 0.0
    line_h = font_size * LINE_H_RATIO

    if wrap:
        # Required width = longest line width (no wrapping floor)
        req_w = max(char_px_width(l, font_size) for l in lines)
        req_h = len(lines) * line_h
    else:
        req_w = max(char_px_width(l, font_size) for l in lines) if lines else 0.0
        req_h = len(lines) * line_h

    return req_w, req_h


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


# ----- metrics lookup -----

def load_metrics(metrics_path):
    """
    Load annotated plan JSON from text-metrics.js --out.
    Returns dict: {shape_id: {min_w: float, min_h: float}} for shapes and containers.
    Shape id in plan == mxCell id in .drawio (by convention).
    """
    if not metrics_path:
        return {}
    try:
        with open(metrics_path, encoding="utf-8") as f:
            plan = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: could not load metrics file {metrics_path!r}: {e}", file=sys.stderr)
        return {}

    result = {}
    for kind in ("shapes", "containers"):
        for el in plan.get(kind, []):
            eid = el.get("id")
            ts = el.get("text_safe")
            if eid and ts:
                result[eid] = {
                    "min_w": ts.get("min_width", 0),
                    "min_h": ts.get("min_height", 0),
                }
    return result


# ----- pipeline marker -----

def infer_layout_mode_from_xml(root):
    """
    Look for a pipeline marker comment written by elk-layout.py.
    Returns 'elk' | 'neato' | 'graphviz' | None.
    """
    # elk-layout.py may write a processing instruction or comment
    for elem in root.iter():
        marker = elem.get("data-layout-engine")
        if marker:
            return marker.lower()
    return None


# ----- main cell processing -----

def try_expand_cell(cell, g, lines, avail_w, avail_h, font_size, max_grow_ratio, metrics_map, dry_run):
    """
    Pre-pass: try to grow the cell's geometry so labels fit at current fontSize.
    Returns True if cell was expanded (or would be in dry_run), False otherwise.

    Strategy:
    1. If metrics_map has precomputed min_w/min_h for this cell, use those.
    2. Otherwise compute from heuristic.
    In both cases: only expand if ratio ≤ max_grow_ratio.
    """
    cell_id = cell.get("id", "")
    style = cell.get("style", "") or ""
    style_kv = parse_style(style)
    sl, sr, st, sb = cell_padding(style_kv)
    hdr = header_offset(style_kv)
    wrap = style_kv.get("whiteSpace") == "wrap"

    try:
        cur_w = float(g.get("width", 0))
        cur_h = float(g.get("height", 0))
    except (TypeError, ValueError):
        return False

    if cur_w <= 0 or cur_h <= 0:
        return False

    # Determine required content dims
    if cell_id in metrics_map:
        needed_w = metrics_map[cell_id]["min_w"]
        needed_h = metrics_map[cell_id]["min_h"]
    else:
        req_content_w, req_content_h = required_dims(lines, font_size, wrap)
        needed_w = req_content_w + sl + sr
        needed_h = req_content_h + hdr + st + sb

    expanded = False

    if needed_w > cur_w:
        ratio = needed_w / cur_w
        if ratio <= max_grow_ratio:
            if not dry_run:
                g.set("width", f"{needed_w:.1f}")
            expanded = True
        # else: ratio too large — let font shrink handle it

    if needed_h > cur_h:
        ratio = needed_h / cur_h
        if ratio <= max_grow_ratio:
            if not dry_run:
                g.set("height", f"{needed_h:.1f}")
            expanded = True

    return expanded


def fit_one_cell(cell, mode, layout_mode, min_size, max_size, max_grow_ratio, metrics_map, dry_run=False):
    """
    Adjust fontSize (and possibly geometry) of one cell.
    Returns (old_font, new_font, cell_expanded: bool) or (None, None, False) if skipped.

    layout_mode in {'elk', 'off', 'neato', 'graphviz'}:
      - elk: shrink fonts only (back-compat)
      - off/neato/graphviz: run cell-expansion pre-pass first; only shrink if expansion refused
    """
    style = cell.get("style", "") or ""
    if not style:
        return None, None, False
    style_kv = parse_style(style)
    value = cell.get("value", "") or ""
    if not value.strip():
        return None, None, False

    g = cell.find("mxGeometry")
    if g is None:
        return None, None, False
    try:
        gw = float(g.get("width", 0))
        gh = float(g.get("height", 0))
    except (TypeError, ValueError):
        return None, None, False

    geom = (float(g.get("x", 0)), float(g.get("y", 0)), gw, gh)
    if is_skippable(style_kv, geom):
        return None, None, False

    # Wrap behavior
    wrap = style_kv.get("whiteSpace") == "wrap"

    # Available text area (re-read after possible expansion)
    sl, sr, st, sb = cell_padding(style_kv)
    hdr = header_offset(style_kv)

    lines = split_lines(value)
    if not lines:
        return None, None, False

    try:
        cur = int(float(style_kv.get("fontSize", 12)))
    except (TypeError, ValueError):
        cur = 12

    cell_expanded = False

    # Pre-pass cell expansion for non-elk modes
    if layout_mode != "elk":
        avail_w = max(1.0, gw - sl - sr)
        avail_h = max(1.0, gh - hdr - st - sb)
        if not text_fits(lines, cur, avail_w, avail_h, wrap):
            cell_expanded = try_expand_cell(
                cell, g, lines, avail_w, avail_h, cur, max_grow_ratio, metrics_map, dry_run
            )

    # Re-read geometry (may have been expanded)
    try:
        gw2 = float(g.get("width", 0))
        gh2 = float(g.get("height", 0))
    except (TypeError, ValueError):
        gw2, gh2 = gw, gh

    avail_w = max(1.0, gw2 - sl - sr)
    avail_h = max(1.0, gh2 - hdr - st - sb)

    new = cur
    if not text_fits(lines, cur, avail_w, avail_h, wrap):
        # Shrink
        while new > min_size and not text_fits(lines, new, avail_w, avail_h, wrap):
            new -= 1
    elif mode == "grow" and layout_mode == "elk":
        # Grow — only when ELK has already enlarged shapes (explicit opt-in)
        while new < max_size:
            candidate = new + 1
            if text_fits(lines, candidate, avail_w * 0.85, avail_h * 0.85, wrap):
                new = candidate
            else:
                break
    elif mode == "grow" and layout_mode != "elk":
        # Grow via cell expansion preferred; font grow only as fallback
        while new < max_size:
            candidate = new + 1
            if text_fits(lines, candidate, avail_w * 0.85, avail_h * 0.85, wrap):
                new = candidate
            else:
                break

    if new != cur:
        if not dry_run:
            cell.set("style", set_style_kv(style, "fontSize", str(new)))

    return cur, new, cell_expanded


def resolve_layout_mode(requested, root):
    """
    Resolve --layout-mode auto → concrete mode.
    'auto': check for pipeline marker, default 'elk' for back-compat.
    """
    if requested != "auto":
        return requested
    inferred = infer_layout_mode_from_xml(root)
    if inferred in ("elk", "off", "neato", "graphviz"):
        return inferred
    return "elk"  # back-compat default


def main():
    ap = argparse.ArgumentParser(description="Lightweight font-fit post-processor for .drawio files")
    ap.add_argument("input", help="Source .drawio file")
    ap.add_argument("output", nargs="?", help="Output path (default: in-place)")
    ap.add_argument("--mode", choices=["off", "auto", "grow"], default="auto",
                    help="off: no-op; auto (default): shrink only; grow: shrink + grow")
    ap.add_argument("--layout-mode", choices=["off", "elk", "neato", "graphviz", "auto"],
                    default="auto", dest="layout_mode",
                    help=(
                        "Layout mode for pre-pass cell expansion. "
                        "elk: ELK ran first, back-compat shrink-only behavior. "
                        "off/neato/graphviz: prefer growing cells over shrinking fonts. "
                        "auto (default): infer from diagram marker, fall back to elk."
                    ))
    ap.add_argument("--metrics", default=None, dest="metrics",
                    help="Path to annotated plan JSON from text-metrics.js --out (enables accurate min_w/min_h lookup)")
    ap.add_argument("--max-grow-ratio", type=float, default=1.5, dest="max_grow_ratio",
                    help="Max ratio of required/current cell dimension before falling back to font shrink (default 1.5)")
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

    # Load optional precomputed metrics
    metrics_map = load_metrics(args.metrics)

    tree = ET.parse(args.input)
    root = tree.getroot()

    # Resolve layout mode
    layout_mode = resolve_layout_mode(args.layout_mode, root)
    print(f"layout_mode={layout_mode}  mode={mode}  max_grow_ratio={args.max_grow_ratio}")
    if metrics_map:
        print(f"metrics loaded: {len(metrics_map)} shapes from {args.metrics!r}")

    n_scanned = 0
    n_shrunk = 0
    n_grew = 0
    n_expanded = 0
    n_unchanged = 0

    for cell in root.iter("mxCell"):
        if cell.get("vertex") != "1":
            continue
        old, new, cell_expanded = fit_one_cell(
            cell, mode, layout_mode,
            args.min_size, args.max_size,
            args.max_grow_ratio, metrics_map,
            dry_run=args.dry_run,
        )
        if old is None:
            continue
        n_scanned += 1
        label = strip_html(cell.get("value", ""))[:40]
        cid = cell.get("id", "")
        if cell_expanded:
            n_expanded += 1
            print(f"  expand {cid:<24} geometry grown             ({label})")
        if new == old:
            n_unchanged += 1
        elif new < old:
            n_shrunk += 1
            print(f"  shrink {cid:<24} {old} → {new}  ({label})")
        else:
            n_grew += 1
            print(f"  grow   {cid:<24} {old} → {new}  ({label})")

    print()
    print(f"Scanned: {n_scanned}   Expanded: {n_expanded}   Shrunk: {n_shrunk}   Grew: {n_grew}   Unchanged: {n_unchanged}")

    if args.dry_run:
        print("(dry-run — no file written)")
        sys.exit(0)

    out_path = args.output or args.input
    tree.write(out_path, encoding="utf-8", xml_declaration=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
