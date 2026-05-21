#!/usr/bin/env python3
"""
F9: Container auto-shrink post-processor for .drawio files.

For each container cell (vertex=1 with children), shrinks width/height to
tightly wrap the children's bounding box plus padding. Respects swimlane
startSize (header reservation). Processes containers bottom-up so parent
shrink uses already-shrunken child bounds.

Only SHRINKS by default — never enlarges. Pass --also-grow to allow growing.
Container's absolute x/y position is never changed; only width/height adjust.

Pipeline position (after fit-fonts, before final validate):
    skill emits .drawio
    → scripts/elk-layout.py    (optional — moves/resizes cells)
    → scripts/fit-fonts.py     (optional — adjusts fontSize)
    → scripts/fit-containers.py  (THIS — shrinks containers to fit children)
    → scripts/validate.py      (Q404 area-utilization check)

Usage:
    python3 fit-containers.py diagram.drawio
    python3 fit-containers.py diagram.drawio --output shrunk.drawio
    python3 fit-containers.py diagram.drawio --padding 32
    python3 fit-containers.py diagram.drawio --also-grow
    python3 fit-containers.py diagram.drawio --dry-run
    python3 fit-containers.py diagram.drawio --min-container-size 120,60
    python3 fit-containers.py diagram.drawio --exclude-pattern layer1,bg
"""

import argparse
import fnmatch
import os
import re
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- constants

DEFAULT_PADDING = 24
DEFAULT_MIN_W = 160
DEFAULT_MIN_H = 80

OK = "\033[32m✓\033[0m"
WARN = "\033[33m⚠\033[0m"
ERR = "\033[31m✗\033[0m"
INFO = "\033[36m·\033[0m"

# ---------------------------------------------------------------- parsing

def load(path: str):
    try:
        tree = ET.parse(path)
        return tree, tree.getroot()
    except ET.ParseError as e:
        print(f"{ERR} E007: Malformed XML: {e}")
        sys.exit(2)
    except FileNotFoundError:
        print(f"{ERR} File not found: {path}")
        sys.exit(2)


def all_models(root):
    """Yield every mxGraphModel element (handles both bare and mxfile forms)."""
    for m in root.iter("mxGraphModel"):
        yield m


def iter_cells(model):
    """Yield mxCell elements, including those wrapped in <object>."""
    for r in model.iter("root"):
        for c in r.findall("mxCell"):
            yield c
        for obj in r.findall("object"):
            inner = obj.find("mxCell")
            if inner is not None:
                # propagate id so callers can use cell.get("id")
                if not inner.get("id"):
                    inner.set("id", obj.get("id", ""))
                yield inner

# ---------------------------------------------------------------- style helpers

def parse_style(style: str) -> dict:
    """Style string → dict."""
    kv = {}
    if not style:
        return kv
    for part in style.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
        else:
            kv[part] = "1"
    return kv


def get_start_size(style_kv: dict) -> float:
    """Return swimlane/table header reservation in px (0 if not a swimlane)."""
    if "swimlane" not in style_kv and "table" not in style_kv:
        return 0.0
    try:
        return float(style_kv.get("startSize", 20))
    except (TypeError, ValueError):
        return 20.0


def is_horizontal_header(style_kv: dict) -> bool:
    """True → header is on top (default); False → header is on left side."""
    return style_kv.get("horizontal", "1") != "0"

# ---------------------------------------------------------------- geometry

def get_geometry(cell) -> dict | None:
    """Return mxGeometry as dict {x, y, w, h} or None if absent/invalid."""
    geo = cell.find("mxGeometry")
    if geo is None:
        return None
    try:
        return {
            "x": float(geo.get("x", 0)),
            "y": float(geo.get("y", 0)),
            "w": float(geo.get("width", 0)),
            "h": float(geo.get("height", 0)),
            "_el": geo,
        }
    except (TypeError, ValueError):
        return None


def set_geometry(geo_el, w: float, h: float):
    geo_el.set("width", str(round(w, 2)))
    geo_el.set("height", str(round(h, 2)))

# ---------------------------------------------------------------- exclusion

def build_exclude_set(pattern_str: str) -> list:
    """Split comma-list of patterns; each may be an exact ID or a glob."""
    if not pattern_str:
        return []
    return [p.strip() for p in pattern_str.split(",") if p.strip()]


def is_excluded(cell_id: str, patterns: list) -> bool:
    for pat in patterns:
        if pat == cell_id or fnmatch.fnmatch(cell_id, pat):
            return True
    return False

# ---------------------------------------------------------------- depth computation

def build_depth_map(cells: list) -> dict:
    """Return {id: depth} for all cells. Root cells (parent=0 or 1) get depth 0."""
    parent_of = {}
    for c in cells:
        cid = c.get("id", "")
        pid = c.get("parent", "")
        parent_of[cid] = pid

    depth_cache = {}

    def depth(cid):
        if cid in depth_cache:
            return depth_cache[cid]
        pid = parent_of.get(cid, "")
        if not pid or pid in ("0", "1") or pid == cid:
            depth_cache[cid] = 0
            return 0
        d = depth(pid) + 1
        depth_cache[cid] = d
        return d

    for c in cells:
        depth(c.get("id", ""))

    return depth_cache

# ---------------------------------------------------------------- main algorithm

def process_model(model, padding: int, min_w: int, min_h: int,
                  also_grow: bool, dry_run: bool, exclude_patterns: list,
                  verbose: bool) -> tuple[int, float]:
    """
    Process one mxGraphModel. Returns (containers_changed, pixels_saved).
    """
    cells = list(iter_cells(model))

    # Build lookup tables
    cell_by_id: dict = {}
    children_of: dict = {}   # parent_id → [child_cell, ...]

    for c in cells:
        cid = c.get("id", "")
        if cid:
            cell_by_id[cid] = c
        pid = c.get("parent", "")
        if pid:
            children_of.setdefault(pid, []).append(c)

    # Identify containers: vertex=1 AND has at least one child
    def is_container(c) -> bool:
        cid = c.get("id", "")
        if c.get("vertex") != "1":
            return False
        return bool(children_of.get(cid))

    containers = [c for c in cells if is_container(c)]

    if not containers:
        return 0, 0.0

    # Sort deepest-first so child containers shrink before their parents
    depth_map = build_depth_map(cells)
    containers_sorted = sorted(
        containers,
        key=lambda c: depth_map.get(c.get("id", ""), 0),
        reverse=True,
    )

    changed = 0
    total_pixels_saved = 0.0

    for container in containers_sorted:
        cid = container.get("id", "")

        if is_excluded(cid, exclude_patterns):
            if verbose:
                print(f"  {INFO} Skip (excluded): {cid!r}")
            continue

        geo = get_geometry(container)
        if geo is None:
            continue

        style_kv = parse_style(container.get("style", ""))
        start_size = get_start_size(style_kv)
        horiz_header = is_horizontal_header(style_kv)

        # Gather children (skip edge cells; skip fixed "layer" pseudo-cells)
        kids = children_of.get(cid, [])
        vertex_kids = [
            k for k in kids
            if k.get("vertex") == "1" and k.get("id") not in ("0", "1")
        ]

        if not vertex_kids:
            # No drawable children — skip (don't shrink to 0)
            continue

        # Compute children bbox in container-local coords
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for kid in vertex_kids:
            kg = get_geometry(kid)
            if kg is None:
                continue
            kx, ky, kw, kh = kg["x"], kg["y"], kg["w"], kg["h"]
            min_x = min(min_x, kx)
            min_y = min(min_y, ky)
            max_x = max(max_x, kx + kw)
            max_y = max(max_y, ky + kh)

        if min_x == float("inf"):
            continue  # no valid child geometry

        # Target size: bbox + padding on each side, plus header on the relevant axis
        if horiz_header:
            # top header → startSize reserved at top of content area
            # children y coords start at 0 relative to content area (below header)
            # but in draw.io, children y=0 is below the header already
            target_w = (max_x - min_x) + padding * 2
            target_h = (max_y - min_y) + padding * 2 + start_size
        else:
            # left header → startSize on left
            target_w = (max_x - min_x) + padding * 2 + start_size
            target_h = (max_y - min_y) + padding * 2

        # Apply minimum container size
        target_w = max(target_w, min_w)
        target_h = max(target_h, min_h)

        cur_w = geo["w"]
        cur_h = geo["h"]

        # Determine if a change is warranted
        new_w = cur_w
        new_h = cur_h

        if target_w < cur_w:
            new_w = target_w
        elif also_grow and target_w > cur_w:
            new_w = target_w

        if target_h < cur_h:
            new_h = target_h
        elif also_grow and target_h > cur_h:
            new_h = target_h

        w_changed = abs(new_w - cur_w) > 0.5
        h_changed = abs(new_h - cur_h) > 0.5

        if not w_changed and not h_changed:
            if verbose:
                # Report if shrink would be needed but was rejected
                if target_w > cur_w or target_h > cur_h:
                    label = container.get("value") or cid
                    print(f"  {WARN} Would GROW {label!r} — skipped (pass --also-grow)")
            continue

        pixels_saved = (cur_w * cur_h) - (new_w * new_h)
        total_pixels_saved += pixels_saved
        label = container.get("value") or cid

        if dry_run:
            direction = "grow" if pixels_saved < 0 else "shrink"
            print(
                f"  {INFO} [{direction}] {label!r}: "
                f"{cur_w:.0f}×{cur_h:.0f} → {new_w:.0f}×{new_h:.0f} "
                f"(Δ {abs(pixels_saved):.0f}px²)"
            )
        else:
            set_geometry(geo["_el"], new_w, new_h)
            direction = "grow" if pixels_saved < 0 else "shrink"
            if verbose:
                print(
                    f"  {OK} [{direction}] {label!r}: "
                    f"{cur_w:.0f}×{cur_h:.0f} → {new_w:.0f}×{new_h:.0f} "
                    f"(Δ {abs(pixels_saved):.0f}px²)"
                )

        changed += 1

    return changed, total_pixels_saved


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="Container auto-shrink post-processor for .drawio files"
    )
    ap.add_argument("input", help="Source .drawio file")
    ap.add_argument("output", nargs="?", help="Output path (default: in-place)")
    ap.add_argument(
        "--padding", type=int, default=DEFAULT_PADDING, metavar="INT",
        help=f"Inner padding around children bbox (default: {DEFAULT_PADDING}px)"
    )
    ap.add_argument(
        "--min-container-size", default=f"{DEFAULT_MIN_W},{DEFAULT_MIN_H}",
        metavar="W,H",
        help=f"Minimum container dimensions (default: {DEFAULT_MIN_W},{DEFAULT_MIN_H})"
    )
    ap.add_argument(
        "--also-grow", action="store_true",
        help="Also enlarge containers that are too small for their children"
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Report changes without writing the file"
    )
    ap.add_argument(
        "--exclude-pattern", default="", metavar="STR",
        help="Comma-list of container IDs or glob patterns to skip"
    )
    ap.add_argument(
        "--verbose", action="store_true",
        help="Print per-container detail even when not dry-run"
    )
    args = ap.parse_args()

    # Parse min container size
    try:
        min_parts = args.min_container_size.split(",")
        min_w = int(min_parts[0].strip())
        min_h = int(min_parts[1].strip()) if len(min_parts) > 1 else min_w
    except (ValueError, IndexError):
        print(f"{ERR} --min-container-size must be W,H integers")
        sys.exit(1)

    exclude_patterns = build_exclude_set(args.exclude_pattern)

    tree, root = load(args.input)

    total_changed = 0
    total_pixels = 0.0

    for model in all_models(root):
        n, px = process_model(
            model,
            padding=args.padding,
            min_w=min_w,
            min_h=min_h,
            also_grow=args.also_grow,
            dry_run=args.dry_run,
            exclude_patterns=exclude_patterns,
            verbose=args.verbose or args.dry_run,
        )
        total_changed += n
        total_pixels += px

    if args.dry_run:
        print(f"\n(dry-run — no file written)")
        print(
            f"Summary: would change {total_changed} containers, "
            f"total area delta: {abs(total_pixels):.0f}px²"
        )
        return

    out_path = args.output or args.input
    tree.write(out_path, encoding="utf-8", xml_declaration=False)

    pixels_saved = total_pixels
    print(
        f"{OK} Shrunk: {total_changed} containers, "
        f"total pixels saved: {abs(pixels_saved):.0f}px²"
        + (f" → {out_path}" if args.output else "")
    )


if __name__ == "__main__":
    main()
