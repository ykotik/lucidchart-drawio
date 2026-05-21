#!/usr/bin/env python3
"""
route-edges.py — obstacle-push edge routing for .drawio files.

Detects edge segments that intersect unrelated vertex AABBs and inserts
orthogonal waypoints to steer the edge around the blocking shape via the
shortest detour (above / below / left / right).

Runs after elk-layout.py, before fit-fonts.py. Controlled by the
`edge_routing` feature flag (auto | on | script | off).

Usage:
    python3 scripts/route-edges.py path/to/diagram.drawio
    python3 scripts/route-edges.py in.drawio out.drawio
    python3 scripts/route-edges.py diagram.drawio --dry-run
    python3 scripts/route-edges.py diagram.drawio --clearance 30
    python3 scripts/route-edges.py diagram.drawio --features edge_routing=off
"""

import sys
import argparse
import xml.etree.ElementTree as ET

DEFAULT_CLEARANCE = 20   # px gap between edge path and shape border
DEFAULT_THRESHOLD = 15   # minimum edge count to auto-activate


# ── geometry helpers ────────────────────────────────────────────────────────

def _parse_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except ValueError:
        return default


def _geom_of(cell):
    """Return (x, y, w, h) from the mxGeometry child, or None."""
    for ch in cell:
        if ch.tag == "mxGeometry" and ch.get("as") == "geometry":
            return (
                _parse_float(ch.get("x")),
                _parse_float(ch.get("y")),
                _parse_float(ch.get("width")),
                _parse_float(ch.get("height")),
            )
    return None


def _collect_cells(model):
    """Return (by_id, parents) dicts for one mxGraphModel."""
    by_id = {}
    parents = {}
    for cell in model.iter("mxCell"):
        cid = cell.get("id")
        if cid:
            by_id[cid] = cell
            parents[cid] = cell.get("parent", "1")
    return by_id, parents


def _abs_origin(cid, by_id, parents, abs_cache):
    """Resolve absolute canvas (x, y) of cell cid by walking the parent chain."""
    if cid in abs_cache:
        return abs_cache[cid]
    ax, ay = 0.0, 0.0
    pid = parents.get(cid)
    while pid and pid not in ("0", "1"):
        pg = _geom_of(by_id[pid]) if pid in by_id else None
        if pg:
            ax += pg[0]
            ay += pg[1]
        pid = parents.get(pid)
    abs_cache[cid] = (ax, ay)
    return ax, ay


def _abs_geom(cid, by_id, parents, abs_cache):
    """Return absolute (x, y, w, h) for vertex cid, or None."""
    cell = by_id.get(cid)
    if not cell:
        return None
    g = _geom_of(cell)
    if not g or g[2] <= 0 or g[3] <= 0:
        return None
    ox, oy = _abs_origin(cid, by_id, parents, abs_cache)
    return (ox + g[0], oy + g[1], g[2], g[3])


# ── intersection detection ───────────────────────────────────────────────────

def _expand(x, y, w, h, pad):
    """Return expanded AABB (x1, y1, x2, y2)."""
    return (x - pad, y - pad, x + w + pad, y + h + pad)


def _segment_hits_aabb(p1, p2, aabb):
    """
    True if line segment p1→p2 intersects axis-aligned box aabb=(x1,y1,x2,y2).
    Uses parametric clipping (Liang-Barsky).
    """
    x1, y1, x2, y2 = aabb
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    t_min, t_max = 0.0, 1.0

    for p, q in [
        (-dx, p1[0] - x1),
        ( dx, x2 - p1[0]),
        (-dy, p1[1] - y1),
        ( dy, y2 - p1[1]),
    ]:
        if abs(p) < 1e-9:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t_min = max(t_min, t)
            else:
                t_max = min(t_max, t)
            if t_min > t_max:
                return False
    return True


# ── detour computation ───────────────────────────────────────────────────────

def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _shortest_detour(p1, p2, aabb):
    """
    Return 1 waypoint that routes around aabb with the shortest Manhattan detour.
    Tries four bypass points (above / below / left / right of aabb midpoint).
    """
    x1, y1, x2, y2 = aabb
    mx = (p1[0] + p2[0]) / 2
    my = (p1[1] + p2[1]) / 2

    candidates = [
        (mx, y1),   # above
        (mx, y2),   # below
        (x1, my),   # left
        (x2, my),   # right
    ]

    def cost(wp):
        return _manhattan(p1, wp) + _manhattan(wp, p2)

    return min(candidates, key=cost)


# ── XML patching ─────────────────────────────────────────────────────────────

def _get_or_create_geom(cell):
    """Return the mxGeometry child of an edge cell, creating it if absent."""
    for ch in cell:
        if ch.tag == "mxGeometry" and ch.get("relative") == "1":
            return ch
    geom = ET.SubElement(cell, "mxGeometry")
    geom.set("relative", "1")
    geom.set("as", "geometry")
    return geom


def _set_waypoints(geom_el, waypoints):
    """Replace the <Array as='points'> child with the given waypoints list."""
    for arr in list(geom_el):
        if arr.tag == "Array" and arr.get("as") == "points":
            geom_el.remove(arr)
    if not waypoints:
        return
    arr = ET.SubElement(geom_el, "Array")
    arr.set("as", "points")
    for wx, wy in waypoints:
        pt = ET.SubElement(arr, "mxPoint")
        pt.set("x", str(round(wx)))
        pt.set("y", str(round(wy)))


# ── per-model processing ─────────────────────────────────────────────────────

def process_model(model, clearance, threshold, feature_value):
    """
    Process one mxGraphModel. Returns (fixed, skipped_dense) counts.
    fixed        — edges that had waypoints inserted.
    skipped      — edges that still intersect after detour (logged as warnings).
    """
    if feature_value == "off":
        return 0, 0

    by_id, parents = _collect_cells(model)
    abs_cache = {}

    # Build absolute geometry map for all vertices
    vertex_geoms = {}   # id -> (ax, ay, w, h)
    for cid, cell in by_id.items():
        if cell.get("vertex") == "1" and cid not in ("0", "1"):
            g = _abs_geom(cid, by_id, parents, abs_cache)
            if g:
                vertex_geoms[cid] = g

    edges = [c for c in by_id.values() if c.get("edge") == "1"]

    # Auto threshold check
    if feature_value == "auto" and len(edges) < threshold:
        return 0, 0

    fixed = 0
    skipped = 0

    for cell in edges:
        src_id = cell.get("source")
        tgt_id = cell.get("target")
        if not src_id or not tgt_id:
            continue
        sg = vertex_geoms.get(src_id)
        tg = vertex_geoms.get(tgt_id)
        if not sg or not tg:
            continue

        # Centre-to-centre straight-line path
        p1 = (sg[0] + sg[2] / 2, sg[1] + sg[3] / 2)
        p2 = (tg[0] + tg[2] / 2, tg[1] + tg[3] / 2)

        # Collect intersecting blocker shapes
        blockers = []
        for vid, vg in vertex_geoms.items():
            if vid in (src_id, tgt_id):
                continue
            aabb = _expand(vg[0], vg[1], vg[2], vg[3], clearance)
            if _segment_hits_aabb(p1, p2, aabb):
                # Sort by distance from p1 so we process in path order
                mid = (vg[0] + vg[2] / 2, vg[1] + vg[3] / 2)
                blockers.append((_manhattan(p1, mid), aabb))

        if not blockers:
            continue

        blockers.sort()

        # Build waypoint list by detouring around each blocker in order
        waypoints = []
        cur = p1
        for _, aabb in blockers:
            if _segment_hits_aabb(cur, p2, aabb):
                wp = _shortest_detour(cur, p2, aabb)
                waypoints.append(wp)
                cur = wp

        if not waypoints:
            continue

        geom_el = _get_or_create_geom(cell)
        _set_waypoints(geom_el, waypoints)
        fixed += 1

        # Verify the detour actually cleared the blockers (log if not)
        still_blocked = any(
            _segment_hits_aabb(waypoints[i] if i > 0 else p1,
                               waypoints[i + 1] if i + 1 < len(waypoints) else p2,
                               aabb)
            for i, (_, aabb) in enumerate(blockers)
            if i < len(waypoints)
        )
        if still_blocked:
            skipped += 1
            label = cell.get("value", cell.get("id", "?"))
            print(f"  WARN W110: edge '{label}' — detour did not fully clear all blockers "
                  f"(diagram may be too dense — consider auto_layout=elk)", file=sys.stderr)

    return fixed, skipped


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Obstacle-push edge routing for .drawio files (F7 edge_routing)"
    )
    ap.add_argument("input", help="Input .drawio file")
    ap.add_argument("output", nargs="?", help="Output path (default: overwrite input)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Detect intersections and report without writing changes")
    ap.add_argument("--clearance", type=int, default=DEFAULT_CLEARANCE,
                    help=f"Minimum px gap between edge and shape border (default: {DEFAULT_CLEARANCE})")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help=f"Min edges to activate in auto mode (default: {DEFAULT_THRESHOLD})")
    ap.add_argument("--features", default="",
                    help="Feature overrides e.g. 'edge_routing=on'")
    args = ap.parse_args()

    # Parse feature overrides
    feature_value = "auto"
    for part in args.features.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() == "edge_routing":
                feature_value = v.strip()

    try:
        tree = ET.parse(args.input)
    except ET.ParseError as e:
        print(f"ERROR: Cannot parse {args.input}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    root = tree.getroot()
    total_fixed = 0
    total_skipped = 0

    for model in root.iter("mxGraphModel"):
        f, s = process_model(model, args.clearance, args.threshold, feature_value)
        total_fixed += f
        total_skipped += s

    if total_fixed == 0:
        print(f"route-edges: 0 intersections found — {args.input} unchanged")
        return

    if args.dry_run:
        print(f"route-edges [dry-run]: would fix {total_fixed} edge(s) "
              f"({total_skipped} partially blocked) in {args.input}")
        return

    out_path = args.output or args.input
    tree.write(out_path, encoding="unicode", xml_declaration=False)
    msg = f"route-edges: fixed {total_fixed} edge(s)"
    if total_skipped:
        msg += f", {total_skipped} partially blocked (see W110 warnings above)"
    msg += f" → {out_path}"
    print(msg)


if __name__ == "__main__":
    main()
