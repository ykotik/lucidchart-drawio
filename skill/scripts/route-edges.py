#!/usr/bin/env python3
"""
route-edges.py — obstacle-push edge routing for .drawio files.

Detects edge segments that intersect unrelated vertex AABBs and inserts
orthogonal waypoints to steer the edge around the blocking shape via the
shortest detour (above / below / left / right).

Also runs an edge-bundling pass after obstacle routing: parallel edges
(same source/target region or co-linear mid-segment) are spread apart by
a perpendicular stride so they do not visually stack on top of each other.

Runs after elk-layout.py, before fit-fonts.py. Controlled by the
`edge_routing` feature flag (auto | on | script | off).

Usage:
    python3 scripts/route-edges.py path/to/diagram.drawio
    python3 scripts/route-edges.py in.drawio out.drawio
    python3 scripts/route-edges.py diagram.drawio --dry-run
    python3 scripts/route-edges.py diagram.drawio --clearance 30
    python3 scripts/route-edges.py diagram.drawio --features edge_routing=off
    python3 scripts/route-edges.py diagram.drawio --bundle-stride 12
    python3 scripts/route-edges.py diagram.drawio --no-bundle
"""

import sys
import argparse
import xml.etree.ElementTree as ET

DEFAULT_CLEARANCE = 20    # px gap between edge path and shape border
DEFAULT_THRESHOLD = 15    # minimum edge count to auto-activate
DEFAULT_BUNDLE_STRIDE = 8  # px perpendicular offset between bundled parallel edges
_BUNDLE_ANCHOR_TOL = 12   # px tolerance for grouping by endpoint proximity
_BUNDLE_COLINEAR_TOL = 4   # px tolerance for detecting co-linear mid-segments


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
    if cell is None:
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


def _route_with_retry(p1, p2, blocker_aabbs, max_iter=4):
    """
    Build a waypoint list from p1 to p2 that avoids all blocker_aabbs.

    Strategy: walk the current path segment-by-segment; whenever a segment
    still hits a blocker, insert a detour waypoint and re-check the resulting
    sub-segments against the *full* blocker list.  Bound at max_iter total
    inserted waypoints.

    Returns (waypoints, retries_used, exhausted):
        waypoints    — List[Point] (may be empty when no blockers hit)
        retries_used — int, number of extra waypoints inserted beyond the
                       first-pass ones (i.e. iterations consumed by retry)
        exhausted    — True when max_iter was reached and blockers remain
    """
    # Build initial path: one waypoint per blocker encountered in order
    # from p1, using the existing single-pass strategy.
    waypoints = []
    cur = p1
    for aabb in blocker_aabbs:
        if _segment_hits_aabb(cur, p2, aabb):
            wp = _shortest_detour(cur, p2, aabb)
            waypoints.append(wp)
            cur = wp

    retries_used = 0
    exhausted = False

    # Iterative retry: walk every sub-segment of the current path and check
    # it against ALL blockers.  If any sub-segment still hits, insert one
    # more detour waypoint at that position and restart the walk.
    iteration = 0
    while iteration < max_iter:
        path = [p1] + waypoints + [p2]
        inserted = False
        for i in range(len(path) - 1):
            seg_a, seg_b = path[i], path[i + 1]
            for aabb in blocker_aabbs:
                if _segment_hits_aabb(seg_a, seg_b, aabb):
                    wp = _shortest_detour(seg_a, seg_b, aabb)
                    waypoints.insert(i, wp)
                    retries_used += 1
                    inserted = True
                    break
            if inserted:
                break
        if not inserted:
            break  # all segments clear
        iteration += 1
    else:
        # Check if blockers remain after exhausting iterations
        path = [p1] + waypoints + [p2]
        for i in range(len(path) - 1):
            for aabb in blocker_aabbs:
                if _segment_hits_aabb(path[i], path[i + 1], aabb):
                    exhausted = True
                    break
            if exhausted:
                break

    return waypoints, retries_used, exhausted


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


# ── edge bundling ────────────────────────────────────────────────────────────

def _snap(v, tol):
    """Snap value v to grid of size tol for proximity grouping."""
    return round(v / tol) * tol


def _edge_endpoints(cell, vertex_geoms):
    """
    Return (p1, p2) centre points for an edge, or None if geometry missing.
    p1 = source centre, p2 = target centre (absolute canvas coords).
    """
    src_id = cell.get("source")
    tgt_id = cell.get("target")
    if not src_id or not tgt_id:
        return None
    sg = vertex_geoms.get(src_id)
    tg = vertex_geoms.get(tgt_id)
    if not sg or not tg:
        return None
    p1 = (sg[0] + sg[2] / 2, sg[1] + sg[3] / 2)
    p2 = (tg[0] + tg[2] / 2, tg[1] + tg[3] / 2)
    return p1, p2


def _existing_waypoints(cell):
    """Return list of (x, y) waypoints already set on this edge cell, or []."""
    for ch in cell:
        if ch.tag == "mxGeometry" and ch.get("relative") == "1":
            for arr in ch:
                if arr.tag == "Array" and arr.get("as") == "points":
                    return [(float(pt.get("x", 0)), float(pt.get("y", 0)))
                            for pt in arr if pt.tag == "mxPoint"]
    return []


def _primary_direction(p1, p2):
    """
    Return 'H' (horizontal-primary) or 'V' (vertical-primary) based on
    which axis dominates the p1→p2 vector.
    """
    dx = abs(p2[0] - p1[0])
    dy = abs(p2[1] - p1[1])
    return "H" if dx >= dy else "V"


def _mid_segment_coord(p1, p2, waypoints):
    """
    For an edge from p1 to p2 with optional waypoints, return the coordinate
    value of the middle segment along the non-primary axis (used for co-linear
    detection of orthogonal edges).

    For a horizontal-primary edge the middle segment is expected to run
    vertically; its shared x-value identifies co-linear edges.
    For a vertical-primary edge the shared y-value is used.

    Returns (axis, value) where axis is 'x' or 'y'.
    """
    direction = _primary_direction(p1, p2)
    path = [p1] + list(waypoints) + [p2]
    if len(path) < 3:
        # No waypoints — use midpoint of direct segment
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        return ("x", mx) if direction == "V" else ("y", my)
    # Middle segment index
    mid_i = len(path) // 2
    seg_a = path[mid_i - 1]
    seg_b = path[mid_i]
    if direction == "H":
        # Middle segment is the vertical connecting segment — group by x
        return ("x", (seg_a[0] + seg_b[0]) / 2)
    else:
        # Middle segment is the horizontal connecting segment — group by y
        return ("y", (seg_a[1] + seg_b[1]) / 2)


def _bundle_parallel_edges(edges, vertex_geoms, stride=DEFAULT_BUNDLE_STRIDE):
    """
    Detect parallel edges (same source-region → same target-region, or co-linear
    mid-segment on orthogonal edges) and apply a perpendicular offset so they
    spread apart visually instead of stacking.

    Grouping:
      1. Anchor-proximity: snap each endpoint to a grid of BUNDLE_ANCHOR_TOL px;
         edges with matching (snapped_p1, snapped_p2) OR (snapped_p2, snapped_p1)
         are in the same directional bundle.
      2. Co-linear mid-segment: within each anchor-proximity group, sub-group by
         snapped mid-segment coordinate (within BUNDLE_COLINEAR_TOL) so only
         edges that truly overlap get offset.

    Offset rule:
      - Edges within a group of size n are assigned perpendicular offset
        (i - (n-1)/2) * stride, where i is the sorted position by edge id.
      - For orthogonal edges (have waypoints or are H/V dominant):
          offset the middle segment only (shift both bracketing waypoints).
      - For diagonal / straight edges:
          offset all waypoints (and conceptual endpoints) perpendicularly.

    Returns (updated_edges, groups_offset, edges_offset):
        updated_edges  — list of (cell, new_waypoints) for all modified edges
        groups_offset  — number of groups that had >1 edge
        edges_offset   — total number of edge instances that were shifted
    """
    # Build a list of (cell, p1, p2, waypoints, direction) for edges with valid geom
    annotated = []
    for cell in edges:
        ep = _edge_endpoints(cell, vertex_geoms)
        if ep is None:
            continue
        p1, p2 = ep
        wps = _existing_waypoints(cell)
        direction = _primary_direction(p1, p2)
        annotated.append((cell, p1, p2, wps, direction))

    # ── Group by anchor proximity ──
    # Key: (snapped_p1, snapped_p2) normalised so smaller comes first
    tol = _BUNDLE_ANCHOR_TOL

    def anchor_key(p1, p2):
        sp1 = (_snap(p1[0], tol), _snap(p1[1], tol))
        sp2 = (_snap(p2[0], tol), _snap(p2[1], tol))
        # Normalise direction so A→B and B→A land in the same group
        return (min(sp1, sp2), max(sp1, sp2))

    anchor_groups = {}
    for item in annotated:
        cell, p1, p2, wps, direction = item
        key = anchor_key(p1, p2)
        anchor_groups.setdefault(key, []).append(item)

    updated_edges = []
    groups_offset = 0
    edges_offset = 0

    for key, group in anchor_groups.items():
        if len(group) < 2:
            continue  # nothing to bundle

        # ── Sub-group by co-linear mid-segment ──
        colinear_tol = _BUNDLE_COLINEAR_TOL
        sub_groups = {}
        for item in group:
            cell, p1, p2, wps, direction = item
            axis, val = _mid_segment_coord(p1, p2, wps)
            sub_key = (axis, _snap(val, colinear_tol))
            sub_groups.setdefault(sub_key, []).append(item)

        for sub_key, sub in sub_groups.items():
            if len(sub) < 2:
                continue

            # Sort by edge id for deterministic ordering
            sub.sort(key=lambda x: x[0].get("id", ""))
            n = len(sub)
            groups_offset += 1

            for i, (cell, p1, p2, wps, direction) in enumerate(sub):
                offset = (i - (n - 1) / 2) * stride
                if abs(offset) < 0.5:
                    continue  # centre edge — no shift needed

                # Determine perpendicular axis: if edge is H-primary, perp is Y
                # If edge is V-primary, perp is X
                perp_axis = "y" if direction == "H" else "x"

                new_wps = _apply_bundle_offset(p1, p2, wps, direction, perp_axis, offset)
                updated_edges.append((cell, new_wps))
                edges_offset += 1

    return updated_edges, groups_offset, edges_offset


def _apply_bundle_offset(p1, p2, waypoints, direction, perp_axis, offset):
    """
    Apply a perpendicular offset to the middle segment of an orthogonal edge,
    or to all waypoints for diagonal/straight edges.

    For orthogonal edges (waypoints present OR strongly H/V dominant):
      Shift only the middle-segment bracket waypoints by `offset` on `perp_axis`.

    For diagonal/straight edges (no waypoints):
      Return a pair of synthetic waypoints offset from the midpoint.

    Returns: new list of (x, y) waypoints.
    """
    path = [p1] + list(waypoints) + [p2]
    is_orthogonal = len(waypoints) > 0

    if is_orthogonal:
        # Shift the bracket of the middle segment
        mid_i = len(path) // 2
        new_path = list(path)  # mutable copy of all points
        # Offset waypoints bracketing the mid-segment (indices mid_i-1 and mid_i)
        # But only if they are interior waypoints (not p1 or p2)
        for idx in (mid_i - 1, mid_i):
            if 1 <= idx <= len(path) - 2:  # interior waypoints only
                x, y = new_path[idx]
                if perp_axis == "y":
                    new_path[idx] = (x, y + offset)
                else:
                    new_path[idx] = (x + offset, y)
        # Return only the interior waypoints (strip p1 and p2)
        return new_path[1:-1]
    else:
        # Straight / diagonal edge — insert two synthetic waypoints offset from midpoint
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        # Create two waypoints around the midpoint for a slight jog
        quarter_x = (p1[0] + mx) / 2
        quarter_y = (p1[1] + my) / 2
        three_q_x = (mx + p2[0]) / 2
        three_q_y = (my + p2[1]) / 2
        if perp_axis == "y":
            return [(quarter_x, quarter_y + offset),
                    (three_q_x, three_q_y + offset)]
        else:
            return [(quarter_x + offset, quarter_y),
                    (three_q_x + offset, three_q_y)]


# ── per-model processing ─────────────────────────────────────────────────────

def process_model(model, clearance, threshold, feature_value,
                  bundle_stride=DEFAULT_BUNDLE_STRIDE, do_bundle=True):
    """
    Process one mxGraphModel.

    Returns (fixed, skipped, total_retries, groups_offset, edges_offset):
        fixed          — edges that had obstacle-avoidance waypoints inserted.
        skipped        — edges that still intersect after retry exhaustion (W110).
        total_retries  — sum of routing.retries_used across all processed edges.
        groups_offset  — number of parallel-edge groups that received offsets.
        edges_offset   — total edges shifted by the bundling pass.
    """
    if feature_value == "off":
        return 0, 0, 0, 0, 0

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
        return 0, 0, 0, 0, 0

    fixed = 0
    skipped = 0
    total_retries = 0

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

        # Collect intersecting blocker shapes (sorted by distance from p1)
        blocker_aabbs = []
        for vid, vg in vertex_geoms.items():
            if vid in (src_id, tgt_id):
                continue
            aabb = _expand(vg[0], vg[1], vg[2], vg[3], clearance)
            if _segment_hits_aabb(p1, p2, aabb):
                mid = (vg[0] + vg[2] / 2, vg[1] + vg[3] / 2)
                blocker_aabbs.append((_manhattan(p1, mid), aabb))

        if not blocker_aabbs:
            continue

        blocker_aabbs.sort()
        sorted_aabbs = [aabb for _, aabb in blocker_aabbs]

        # Iterative retry routing
        waypoints, retries_used, exhausted = _route_with_retry(
            p1, p2, sorted_aabbs, max_iter=4
        )
        total_retries += retries_used

        if not waypoints:
            continue

        geom_el = _get_or_create_geom(cell)
        _set_waypoints(geom_el, waypoints)
        fixed += 1

        if exhausted:
            skipped += 1
            label = cell.get("value", cell.get("id", "?"))
            print(f"  WARN W110: edge '{label}' — detour did not fully clear all blockers "
                  f"after {4 + retries_used} waypoint(s) "
                  f"(diagram may be too dense — consider auto_layout=elk)", file=sys.stderr)

    # ── Edge bundling pass (runs after obstacle routing) ──────────────────────
    groups_offset = 0
    edges_offset = 0
    if do_bundle:
        updated, groups_offset, edges_offset = _bundle_parallel_edges(
            edges, vertex_geoms, stride=bundle_stride
        )
        for cell, new_wps in updated:
            geom_el = _get_or_create_geom(cell)
            _set_waypoints(geom_el, new_wps)

    return fixed, skipped, total_retries, groups_offset, edges_offset


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
    ap.add_argument("--bundle-stride", type=int, default=DEFAULT_BUNDLE_STRIDE,
                    help=f"Perpendicular px offset per parallel edge in a bundle (default: {DEFAULT_BUNDLE_STRIDE})")
    ap.add_argument("--no-bundle", action="store_true",
                    help="Disable the edge-bundling (parallel-edge separation) pass")
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
    total_retries = 0
    total_groups_offset = 0
    total_edges_offset = 0

    do_bundle = not args.no_bundle

    for model in root.iter("mxGraphModel"):
        f, s, r, go, eo = process_model(
            model, args.clearance, args.threshold, feature_value,
            bundle_stride=args.bundle_stride, do_bundle=do_bundle
        )
        total_fixed += f
        total_skipped += s
        total_retries += r
        total_groups_offset += go
        total_edges_offset += eo

    nothing_done = total_fixed == 0 and total_edges_offset == 0
    if nothing_done:
        print(f"route-edges: 0 intersections found, 0 bundles detected — {args.input} unchanged")
        return

    if args.dry_run:
        print(f"route-edges [dry-run]: would fix {total_fixed} edge(s) "
              f"({total_skipped} partially blocked, {total_retries} retry waypoints), "
              f"bundling.groups_offset={total_groups_offset}, "
              f"edges_offset={total_edges_offset} "
              f"in {args.input}")
        return

    out_path = args.output or args.input
    tree.write(out_path, encoding="unicode", xml_declaration=False)
    msg = f"route-edges: fixed {total_fixed} edge(s)"
    if total_retries:
        msg += f", routing.retries_used={total_retries}"
    if total_skipped:
        msg += f", {total_skipped} partially blocked (see W110 warnings above)"
    if do_bundle:
        msg += (f", bundling.groups_offset={total_groups_offset},"
                f" edges_offset={total_edges_offset}")
    msg += f" → {out_path}"
    print(msg)


if __name__ == "__main__":
    main()
