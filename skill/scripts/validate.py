#!/usr/bin/env python3
"""
drawio-architect validator (v2)

Pre-flight checks for .drawio files produced by the drawio-architect skill.

Usage:
    python3 validate.py path/to/diagram.drawio
    python3 validate.py path/to/diagram.drawio --mode strict
    python3 validate.py path/to/diagram.drawio --mode loose

Modes:
    strict   — errors AND warnings fail (exit 1)
    standard — errors fail; warnings print but exit 0  (default)
    loose    — only errors fail; warnings suppressed

Exit codes:
    0  — diagram passes
    1  — validation failures
    2  — could not read/parse the file
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


# ---------------------------------------------------------------- diagnostics
ERR = "ERROR"
WRN = "WARN "
INF = "INFO "


class Diag:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.infos = []

    def err(self, code, msg):
        self.errors.append((code, msg))

    def warn(self, code, msg):
        self.warnings.append((code, msg))

    def info(self, code, msg):
        self.infos.append((code, msg))

    def print(self, mode):
        for code, msg in self.errors:
            print(f"{ERR} {code}: {msg}")
        if mode != "loose":
            for code, msg in self.warnings:
                print(f"{WRN} {code}: {msg}")
        for code, msg in self.infos:
            print(f"{INF} {code}: {msg}")

        n_e = len(self.errors)
        n_w = len(self.warnings) if mode != "loose" else 0
        n_i = len(self.infos)
        print(f"\nSummary: {n_e} errors, {n_w} warnings, {n_i} infos")

        if mode == "strict":
            return 0 if (n_e == 0 and n_w == 0) else 1
        return 0 if n_e == 0 else 1


# ----------------------------------------------------------------- parsing
def load(path):
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as e:
        print(f"{ERR} E007: Malformed XML: {e}")
        sys.exit(2)
    except FileNotFoundError:
        print(f"{ERR} File not found: {path}")
        sys.exit(2)


def all_models(root):
    """Yield each <mxGraphModel> element."""
    for m in root.iter("mxGraphModel"):
        yield m


def iter_cells(model):
    for r in model.iter("root"):
        for c in r.findall("mxCell"):
            yield c
        for c in r.findall("object"):
            inner = c.find("mxCell")
            if inner is not None:
                # objects wrap mxCell; carry id from object
                inner.set("id", c.get("id", inner.get("id", "")))
                yield inner


# --------------------------------------------------------------- geometry
def geom_of(cell):
    g = cell.find("mxGeometry")
    if g is None:
        return None
    try:
        x = float(g.get("x", 0))
        y = float(g.get("y", 0))
        w = float(g.get("width", 0))
        h = float(g.get("height", 0))
        return (x, y, w, h)
    except (TypeError, ValueError):
        return None


def style_kv(cell):
    """Parse style string `k1=v1;k2=v2;` into dict."""
    s = cell.get("style", "") or ""
    kv = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
        elif part.strip():
            kv[part.strip()] = "1"
    return kv


# ----------------------------------------------------------- main checks
def validate_model(model, diag, features=None):
    features = features or {}
    cells = list(iter_cells(model))
    if not cells:
        return

    by_id = {}
    parents = {}
    is_vertex = {}
    is_edge = {}
    geoms = {}
    styles = {}

    # Pass 1: index
    for c in cells:
        cid = c.get("id")
        if cid is None:
            continue
        if cid in by_id:
            diag.err("E001", f"Duplicate id '{cid}'")
        else:
            by_id[cid] = c
        parents[cid] = c.get("parent")
        is_vertex[cid] = c.get("vertex") == "1"
        is_edge[cid] = c.get("edge") == "1"
        geoms[cid] = geom_of(c)
        styles[cid] = style_kv(c)

    # Pass 2: per-cell checks
    for cid, c in by_id.items():
        p = parents[cid]

        # E003 parent exists (parent='0' / '1' are roots; both fine)
        if p is not None and p not in by_id and p not in ("0", "1"):
            # Some plain drawio files omit '0' and '1' as mxCells with id=0,1
            # Check if there is *any* mxCell with id=0 or id=1
            if p in ("0", "1"):
                pass  # ok
            else:
                diag.err("E003", f"Cell '{cid}' parent '{p}' does not exist")

        # E002, E008 geometry presence
        if is_edge[cid]:
            if geoms[cid] is None:
                diag.err("E002", f"Edge '{cid}' missing <mxGeometry> child")
        if is_vertex[cid]:
            if geoms[cid] is None:
                diag.err("E008", f"Vertex '{cid}' has no <mxGeometry>")

        # E004, E005 edge endpoints
        if is_edge[cid]:
            src = c.get("source")
            tgt = c.get("target")
            if src is not None and src not in by_id:
                diag.err("E004", f"Edge '{cid}' source '{src}' does not exist")
            if tgt is not None and tgt not in by_id:
                diag.err("E005", f"Edge '{cid}' target '{tgt}' does not exist")

        # E009 swimlane container missing startSize
        st = styles[cid]
        if "swimlane" in st and "startSize" not in st:
            diag.warn("W105", f"Container '{cid}' uses swimlane style without explicit startSize")

    # ---------------- warnings ----------------

    # W101 shape extends beyond parent
    for cid, geom in geoms.items():
        if geom is None or not is_vertex[cid]:
            continue
        p = parents[cid]
        if p in by_id:
            pg = geoms.get(p)
            if pg is None:
                continue
            _, _, pw, ph = pg
            x, y, w, h = geom
            # Children use relative coords inside containers
            pst = styles[p]
            is_container = ("swimlane" in pst or pst.get("container") == "1")
            if is_container and (x + w > pw + 1 or y + h > ph + 1):
                diag.warn("W101", f"Shape '{cid}' extends beyond parent '{p}' bounds")

    # W103 child overlaps container header (y < startSize)
    for cid, geom in geoms.items():
        if geom is None or not is_vertex[cid]:
            continue
        p = parents[cid]
        if p in by_id:
            pst = styles[p]
            if "swimlane" in pst:
                start_size = float(pst.get("startSize", 20))
                horizontal = pst.get("horizontal", "1") != "0"
                _, y, _, _ = geom
                x = geom[0]
                if horizontal and y < start_size - 1:
                    diag.warn("W103", f"Shape '{cid}' overlaps container '{p}' header (y={y} < startSize={start_size})")
                if not horizontal and x < start_size - 1:
                    diag.warn("W103", f"Shape '{cid}' overlaps container '{p}' header (x={x} < startSize={start_size})")

    # W112 container dead space > 30% of usable height/width
    for cid in by_id:
        if not is_vertex[cid]:
            continue
        st = styles[cid]
        if "swimlane" not in st and st.get("container") != "1":
            continue
        g = geoms.get(cid)
        if g is None:
            continue
        _, _, cw, ch = g
        start_size = float(st.get("startSize", 26))
        horizontal = st.get("horizontal", "1") != "0"
        usable = (ch - start_size) if horizontal else (cw - start_size)
        if usable < 100:  # skip tiny containers — rounding noise dominates
            continue
        children = [
            k for k, v in parents.items()
            if v == cid and is_vertex.get(k) and geoms.get(k) is not None
        ]
        if not children:
            continue
        if horizontal:
            max_extent = max(geoms[k][1] + geoms[k][3] for k in children)
        else:
            max_extent = max(geoms[k][0] + geoms[k][2] for k in children)
        used_frac = max_extent / usable if usable > 0 else 1.0
        dead_pct = (1.0 - used_frac) * 100.0
        if dead_pct > 30:
            suggested_h = int(max_extent + start_size + 60)
            diag.warn(
                "W112",
                f"Container '{cid}' has {dead_pct:.0f}% dead space "
                f"(content uses {used_frac * 100:.0f}% of {usable:.0f}px usable space). "
                f"Shrink height to ~{suggested_h}px."
            )

    # W113 orphan external shapes when primary container present
    canvas_containers = [
        cid for cid in by_id
        if is_vertex.get(cid)
        and parents.get(cid) == "1"
        and ("swimlane" in styles.get(cid, {}) or styles.get(cid, {}).get("container") == "1")
    ]
    if len(canvas_containers) >= 1:
        canvas_orphans = [
            cid for cid in by_id
            if is_vertex.get(cid)
            and parents.get(cid) == "1"
            and "swimlane" not in styles.get(cid, {})
            and styles.get(cid, {}).get("container") != "1"
        ]
        if len(canvas_orphans) >= 2:
            sample = ", ".join(f"'{c}'" for c in canvas_orphans[:5])
            diag.warn(
                "W113",
                f"{len(canvas_orphans)} shapes sit directly on canvas alongside "
                f"{len(canvas_containers)} container(s) — group them in a labelled "
                f"dashed boundary (e.g. 'Internet Layer', 'External Services'): {sample}"
            )

    # W104 edge parent should be lowest common ancestor of source/target
    def ancestors(cell_id):
        """Return list of ancestor ids from cell up to root."""
        out = []
        cur = cell_id
        seen = set()
        while cur and cur not in seen:
            seen.add(cur)
            p = parents.get(cur)
            if p is None:
                break
            out.append(p)
            cur = p
        return out

    # Identify "layer" cells (children of root '0') — these are intentional edge layers
    layer_ids = {cid for cid, p in parents.items() if p == "0"}

    for cid, c in by_id.items():
        if not is_edge[cid]:
            continue
        src = c.get("source")
        tgt = c.get("target")
        if not src or not tgt or src not in by_id or tgt not in by_id:
            continue
        ans_s = [src] + ancestors(src)
        ans_t = set([tgt] + ancestors(tgt))
        lca = next((a for a in ans_s if a in ans_t), None)
        if lca is None:
            continue
        ep = parents.get(cid)
        if ep is None or ep == lca:
            continue
        # Allow edge.parent to be a layer (child of root '0') — two-layer rendering pattern
        if ep in layer_ids:
            continue
        # Allow edge.parent to be any ancestor of LCA (i.e., containing LCA)
        if ep in ancestors(lca) or ep == "1":
            continue
        diag.warn("W104", f"Edge '{cid}' parent '{ep}' is not LCA '{lca}' or an ancestor of LCA — source '{src}' target '{tgt}'")

    # W102 same-tier vertex overlap
    siblings = defaultdict(list)
    for cid in by_id:
        if not is_vertex[cid]:
            continue
        if geoms[cid] is None:
            continue
        p = parents.get(cid, "1")
        siblings[p].append(cid)

    def aabb(cid):
        return geoms[cid]

    def overlaps(a, b, tol=4):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return (ax + aw > bx + tol and bx + bw > ax + tol and
                ay + ah > by + tol and by + bh > ay + tol)

    for p, sibs in siblings.items():
        for i in range(len(sibs)):
            for j in range(i + 1, len(sibs)):
                a, b = sibs[i], sibs[j]
                ga = aabb(a); gb = aabb(b)
                if ga and gb and overlaps(ga, gb):
                    diag.warn("W102", f"Shape '{a}' overlaps shape '{b}' (siblings under '{p}')")

    # I201 too many nodes
    n_vertices = sum(1 for c in by_id if is_vertex[c])
    if n_vertices > 40:
        diag.info("I201", f"Diagram has {n_vertices} vertices — consider splitting into pages")

    # I203 empty container
    for cid in by_id:
        st = styles[cid]
        if "swimlane" in st or st.get("container") == "1":
            children = [k for k, v in parents.items() if v == cid]
            if not children:
                diag.info("I203", f"Container '{cid}' is empty")

    # F2 quality gate — runs only if feature flag is on
    quality_metrics(by_id, parents, is_vertex, is_edge, geoms, styles, diag, features)


# ============================================================ F2: quality gate
# Feature flag: quality_gate. Disable with --features quality_gate=off
#
# Metrics (classical layout-aesthetics literature, see compass_research2.md):
#   Q401 edge crossings           — # of intersecting straight-line edge segments
#   Q402 orthogonality conformance — % of edges using edgeStyle=orthogonalEdgeStyle
#   Q403 edge length variance      — coefficient of variation (CV) of edge lengths
#   Q404 area utilization          — bounding-box of nodes / canvas area
#
# Each metric emits a warning above a threshold; raw value always printed as INFO.


def _resolve_canvas_xy(cid, geoms, parents, by_id):
    """Walk parent chain summing offsets to get canvas-absolute (x,y) of a cell."""
    if cid not in geoms or geoms[cid] is None:
        return None
    x, y, w, h = geoms[cid]
    p = parents.get(cid)
    while p and p in by_id and p not in ("0", "1"):
        pg = geoms.get(p)
        if pg is None:
            break
        px, py, _, _ = pg
        # Account for swimlane startSize offset on the parent's content origin
        ps = (by_id[p].get("style", "") or "")
        if "swimlane" in ps:
            # Parse startSize if present (default 20)
            ss = 20
            for kv in ps.split(";"):
                if kv.startswith("startSize="):
                    try:
                        ss = float(kv.split("=", 1)[1])
                    except ValueError:
                        pass
                    break
            # Horizontal default true; vertical strip if horizontal=0
            horizontal = True
            for kv in ps.split(";"):
                if kv.startswith("horizontal="):
                    horizontal = (kv.split("=", 1)[1] != "0")
                    break
            if horizontal:
                py += ss
            else:
                px += ss
        x += px
        y += py
        p = parents.get(p)
    return (x, y, w, h)


def _segment_intersects_aabb(p1, p2, bx, by, bw, bh):
    """Return True if segment p1–p2 crosses the interior of AABB (bx,by,bw,bh).

    Checks all 4 sides of the box. Also returns True if either endpoint is
    strictly inside the box. Callers must exclude source/target shapes themselves.
    """
    corners = [
        (bx,      by     ),
        (bx + bw, by     ),
        (bx + bw, by + bh),
        (bx,      by + bh),
    ]
    for i in range(4):
        if _segments_intersect(p1, p2, corners[i], corners[(i + 1) % 4]):
            return True
    def _inside(p):
        return bx < p[0] < bx + bw and by < p[1] < by + bh
    return _inside(p1) or _inside(p2)


def _segments_intersect(a1, a2, b1, b2):
    """Return True if segments a1-a2 and b1-b2 properly cross (not touching at endpoints)."""
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])

    # Reject if endpoints coincide (these are not "crossings" — they share a vertex)
    if a1 == b1 or a1 == b2 or a2 == b1 or a2 == b2:
        return False
    d1 = ccw(b1, b2, a1)
    d2 = ccw(b1, b2, a2)
    d3 = ccw(a1, a2, b1)
    d4 = ccw(a1, a2, b2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def quality_metrics(by_id, parents, is_vertex, is_edge, geoms, styles, diag, features):
    if features.get("quality_gate", "on") != "on":
        return

    # Build canvas-absolute centers for each vertex
    centers = {}
    for cid in by_id:
        if not is_vertex[cid]:
            continue
        ab = _resolve_canvas_xy(cid, geoms, parents, by_id)
        if ab is None:
            continue
        x, y, w, h = ab
        centers[cid] = (x + w / 2.0, y + h / 2.0)

    # ---------- Q401 edge crossings (straight-line proxy) ----------
    edge_segments = []
    for cid, c in by_id.items():
        if not is_edge[cid]:
            continue
        src = c.get("source")
        tgt = c.get("target")
        if src in centers and tgt in centers:
            edge_segments.append((cid, centers[src], centers[tgt]))
    n_cross = 0
    for i in range(len(edge_segments)):
        for j in range(i + 1, len(edge_segments)):
            _, a1, a2 = edge_segments[i]
            _, b1, b2 = edge_segments[j]
            if _segments_intersect(a1, a2, b1, b2):
                n_cross += 1
    diag.info("Q401", f"Edge crossings (straight-line proxy): {n_cross}")
    if len(edge_segments) >= 6 and n_cross > max(2, len(edge_segments) // 4):
        diag.warn(
            "Q401",
            f"High edge-crossing count: {n_cross} crossings over {len(edge_segments)} edges "
            f"(threshold = max(2, edges/4) = {max(2, len(edge_segments) // 4)}) — "
            f"run scripts/route-edges.py (F7) then re-validate; "
            f"for structural overlaps also run scripts/elk-layout.py (F4)"
        )

    # ---------- Q402 orthogonality conformance ----------
    n_edges = sum(1 for cid in by_id if is_edge[cid])
    n_ortho = sum(
        1
        for cid in by_id
        if is_edge[cid]
        and "orthogonalEdgeStyle" in (styles[cid].get("edgeStyle", "") or "")
    )
    if n_edges > 0:
        pct = (n_ortho / n_edges) * 100.0
        diag.info("Q402", f"Orthogonality conformance: {n_ortho}/{n_edges} = {pct:.0f}%")
        if pct < 80.0 and n_edges >= 4:
            diag.warn(
                "Q402",
                f"Low orthogonality ({pct:.0f}%) — architecture diagrams read cleanest at >=80% "
                f"orthogonal. Add edgeStyle=orthogonalEdgeStyle to remaining edges."
            )

    # ---------- Q403 edge-length variance (coefficient of variation) ----------
    lengths = []
    for cid, a, b in edge_segments:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        lengths.append((dx * dx + dy * dy) ** 0.5)
    if len(lengths) >= 3:
        mean = sum(lengths) / len(lengths)
        var = sum((L - mean) ** 2 for L in lengths) / len(lengths)
        std = var ** 0.5
        cv = (std / mean) if mean > 1e-6 else 0.0
        diag.info("Q403", f"Edge-length CV: {cv:.2f} (mean={mean:.0f}px, std={std:.0f}px)")
        if cv > 1.2:
            diag.warn(
                "Q403",
                f"High edge-length variance (CV={cv:.2f}). One or two edges dominate — "
                f"consider re-grouping shapes or running auto_layout=elk."
            )

    # ---------- Q404 area utilization ----------
    if centers:
        all_geoms = [_resolve_canvas_xy(cid, geoms, parents, by_id) for cid in centers]
        all_geoms = [g for g in all_geoms if g is not None]
        if all_geoms:
            min_x = min(g[0] for g in all_geoms)
            min_y = min(g[1] for g in all_geoms)
            max_x = max(g[0] + g[2] for g in all_geoms)
            max_y = max(g[1] + g[3] for g in all_geoms)
            bbox_w = max(1.0, max_x - min_x)
            bbox_h = max(1.0, max_y - min_y)
            bbox_area = bbox_w * bbox_h
            node_area = sum(g[2] * g[3] for g in all_geoms)
            util = node_area / bbox_area
            diag.info("Q404", f"Area utilization: {util * 100:.1f}% (nodes/bbox)")
            if util < 0.10 and len(all_geoms) >= 6:
                diag.warn(
                    "Q404",
                    f"Low area utilization ({util * 100:.1f}%) — shapes are spread thin. "
                    f"Tighten spacing or scale canvas down."
                )
            if util > 0.65:
                diag.warn(
                    "Q404",
                    f"High area utilization ({util * 100:.1f}%) — diagram is crowded. "
                    f"Add gutter or scale canvas up."
                )

    # ---------- Q405 text overflow at current fontSize ----------
    # Same char-width heuristic as scripts/fit-fonts.py (0.55 × fontSize)
    import re as _re
    def _strip(s):
        if not s:
            return ""
        s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&nbsp;", " ")
        return _re.sub(r"<[^>]+>|&[a-z]+;|&#x?[0-9a-f]+;", "", s, flags=_re.IGNORECASE).strip()

    n_overflow = 0
    for cid in by_id:
        if not is_vertex.get(cid):
            continue
        c = by_id[cid]
        st = styles.get(cid, {})
        if st.get("text") == "1" or st.get("edgeLabel") == "1":
            continue
        value = c.get("value", "") or ""
        if not value.strip():
            continue
        g = geoms.get(cid)
        if not g:
            continue
        gw, gh = g[2], g[3]
        if gw <= 0 or gh <= 0:
            continue
        try:
            fs = float(st.get("fontSize", 12))
        except (TypeError, ValueError):
            fs = 12.0
        # Available area (matching fit-fonts.py)
        sp = float(st.get("spacing", 2))
        sl = float(st.get("spacingLeft", sp))
        sr = float(st.get("spacingRight", sp))
        stp = float(st.get("spacingTop", sp))
        sb = float(st.get("spacingBottom", sp))
        hdr = float(st.get("startSize", 0)) if "swimlane" in st else 0
        horizontal = st.get("horizontal", "1") != "0"
        if "swimlane" in st and not horizontal:
            avail_w = max(1.0, gw - hdr - sl - sr)
            avail_h = max(1.0, gh - stp - sb)
        else:
            avail_w = max(1.0, gw - sl - sr)
            avail_h = max(1.0, gh - hdr - stp - sb)
        wrap = st.get("whiteSpace") == "wrap"
        lines = [_strip(p) for p in _re.split(r"<br\s*/?>|\n", value, flags=_re.IGNORECASE) if _strip(p)]
        if not lines:
            continue
        char_w = fs * 0.55
        line_h = fs * 1.2
        if wrap:
            max_chars = max(1, int(avail_w / char_w))
            total = sum(max(1, -(-len(L) // max_chars)) for L in lines)
            fits = total * line_h <= avail_h
        else:
            fits = (len(lines) * line_h <= avail_h) and all(len(L) * char_w <= avail_w for L in lines)
        if not fits:
            n_overflow += 1
            if n_overflow <= 5:  # cap noisy output
                diag.warn(
                    "Q405",
                    f"Cell '{cid}' text overflows at fontSize={int(fs)} (w={gw:.0f} h={gh:.0f}, label='{_strip(value)[:40]}'). Run scripts/fit-fonts.py."
                )
    if n_overflow > 0:
        diag.info("Q405", f"Text overflow: {n_overflow} cell(s) at current fontSize")

    # ---------- W111 convergence node: >3 edges, no port constraints ----------
    edge_count_per_node: dict = defaultdict(int)
    node_has_port: dict = defaultdict(bool)

    for cid, c in by_id.items():
        if not is_edge[cid]:
            continue
        src = c.get("source")
        tgt = c.get("target")
        style_str = c.get("style") or ""
        has_port = any(k in style_str for k in ("exitX=", "exitY=", "entryX=", "entryY="))
        for node in (src, tgt):
            if node and node in by_id:
                edge_count_per_node[node] += 1
                if has_port:
                    node_has_port[node] = True

    for node_id, count in edge_count_per_node.items():
        if count > 3 and not node_has_port.get(node_id, False):
            diag.warn(
                "W111",
                f"Vertex '{node_id}' has {count} edges but none specify exitX/Y or entryX/Y "
                f"— all edges exit from the center, causing label pile-up and line crossing. "
                f"Assign staggered exitX/entryX values (e.g. 0.25, 0.5, 0.75) per edge."
            )

    # ---------- W109 edge label midpoint intersects non-endpoint shape ----------
    for cid, c in by_id.items():
        if not is_edge[cid]:
            continue
        label = (c.get("value") or "").strip()
        if not label:
            continue
        src = c.get("source")
        tgt = c.get("target")
        if not src or not tgt or src not in centers or tgt not in centers:
            continue
        # Check for label offset on mxGeometry
        g = c.find("mxGeometry")
        if g is not None:
            lx = float(g.get("x") or 0)
            ly = float(g.get("y") or 0)
            if abs(lx) > 5 or abs(ly) > 5:
                continue  # offset present — label is repositioned
        sx, sy = centers[src]
        tx, ty = centers[tgt]
        mx, my = (sx + tx) / 2.0, (sy + ty) / 2.0
        for shape_id in by_id:
            if not is_vertex[shape_id] or shape_id in (src, tgt):
                continue
            ab = _resolve_canvas_xy(shape_id, geoms, parents, by_id)
            if ab is None:
                continue
            bx, by_, bw, bh = ab
            if bx <= mx <= bx + bw and by_ <= my <= by_ + bh:
                diag.warn(
                    "W109",
                    f"Edge '{cid}' label midpoint ({mx:.0f},{my:.0f}) falls inside shape '{shape_id}' "
                    f"— add x/y offset to mxGeometry: "
                    f'<mxGeometry relative="1" x="0" y="-15" as="geometry"/>'
                )
                break

    # ---------- W110 edge straight-line path passes through non-endpoint shape ----------
    for cid, c in by_id.items():
        if not is_edge[cid]:
            continue
        src = c.get("source")
        tgt = c.get("target")
        if not src or not tgt or src not in centers or tgt not in centers:
            continue
        p1 = centers[src]
        p2 = centers[tgt]
        for shape_id in by_id:
            if not is_vertex[shape_id] or shape_id in (src, tgt):
                continue
            ab = _resolve_canvas_xy(shape_id, geoms, parents, by_id)
            if ab is None:
                continue
            bx, by_, bw, bh = ab
            if _segment_intersects_aabb(p1, p2, bx, by_, bw, bh):
                diag.warn(
                    "W110",
                    f"Edge '{cid}' straight-line path passes through shape '{shape_id}' "
                    f"— add waypoints or port constraints to route around it, "
                    f"or run scripts/route-edges.py (F7)"
                )
                break


# ============================================================ F3: grounding
# Feature flag: grounding_manifest. Disable with --features grounding_manifest=off
#
# Reads an optional plan JSON (alongside the .drawio or via --plan PATH) and
# requires every container / shape / edge to have a non-empty 'cite' field.
#
#   G501 ERROR — element has no cite (or empty / whitespace)
#   G502 WARN  — element's cite starts with 'assumption:' (review before delivery)
#   G503 INFO  — coverage summary


def grounding_check(plan, diag, features):
    if features.get("grounding_manifest", "on") != "on":
        return
    if not plan:
        return

    n_cited = 0
    n_assumptions = 0
    n_missing = 0
    for kind in ("containers", "shapes", "edges"):
        for el in plan.get(kind, []) or []:
            eid = el.get("id", "<no-id>")
            cite = (el.get("cite") or "").strip()
            if not cite:
                diag.err("G501", f"{kind[:-1]} '{eid}' has no 'cite' field (grounding required)")
                n_missing += 1
                continue
            n_cited += 1
            if cite.startswith("assumption:"):
                diag.warn("G502", f"{kind[:-1]} '{eid}' is an assumption: {cite[11:].strip()}")
                n_assumptions += 1

    total = n_cited + n_missing
    if total:
        diag.info(
            "G503",
            f"Grounding: {n_cited}/{total} cited, {n_assumptions} assumptions, {n_missing} missing"
        )


# ============================================================ T8: text metrics
# Feature flag: text_metrics.  Disable with --features text_metrics=off
#
# Reads an annotated plan JSON produced by scripts/text-metrics.js and checks
# that every shape/container's mxGeometry dimensions are at least as large as
# the safe dimensions computed from label measurement.
#
#   W106 WARN — node width  < text_safe.min_width  (label may overflow horizontally)
#   W107 WARN — node height < text_safe.min_height (label may clip vertically)
#   W108 WARN — swimlane startSize < text_safe.min_startSize (header clips label)
#   T801 INFO — summary (N elements checked, M overflows found)
#
# In --mode strict, W106/W107/W108 are promoted to errors.
# Auto-detects <name>.annotated.plan.json sibling; or pass --annotated-plan PATH.


def text_metrics_check(drawio_path, annotated_plan, diag, features, by_id_map, geoms_map, styles_map):
    """Cross-check emitted mxGeometry against text_safe dims from annotated plan."""
    if features.get("text_metrics", "auto") == "off":
        return
    if not annotated_plan:
        return

    n_checked = 0
    n_overflow = 0

    # Flatten all shapes + containers from annotated plan into a single id→element map
    plan_elements = {}
    for kind in ("shapes", "containers"):
        for el in annotated_plan.get(kind, []) or []:
            eid = el.get("id")
            if eid:
                plan_elements[eid] = el

    # by_id_map and geoms_map may span multiple diagram pages — iterate all
    for page_key, by_id in by_id_map.items():
        geoms = geoms_map[page_key]
        styles = styles_map[page_key]

        for cid, cell in by_id.items():
            el = plan_elements.get(cid)
            if not el:
                continue
            ts = el.get("text_safe")
            if not ts:
                continue

            n_checked += 1
            g = geoms.get(cid)
            if g is None:
                continue
            x, y, w, h = g
            st = styles.get(cid, {})

            # W106 width overflow
            min_w = ts.get("min_width")
            if min_w is not None and w < min_w - 1:
                n_overflow += 1
                diag.warn("W106", (
                    f"Node '{cid}' width={w:.0f}px < text_safe.min_width={min_w}px "
                    f"— label may overflow horizontally"
                ))

            # W107 height overflow
            min_h = ts.get("min_height")
            if min_h is not None and h < min_h - 1:
                n_overflow += 1
                diag.warn("W107", (
                    f"Node '{cid}' height={h:.0f}px < text_safe.min_height={min_h}px "
                    f"— label may clip vertically"
                ))

            # W108 swimlane header overflow
            min_ss = ts.get("min_startSize")
            if min_ss is not None and "swimlane" in (cell.get("style") or ""):
                # Extract declared startSize from live style string (may differ from plan)
                declared_ss = float(st.get("startSize", 26))
                if declared_ss < min_ss - 1:
                    n_overflow += 1
                    diag.warn("W108", (
                        f"Container '{cid}' startSize={declared_ss:.0f}px < "
                        f"text_safe.min_startSize={min_ss}px — header clips label"
                    ))

    if n_checked > 0:
        diag.info("T801", f"Text metrics: {n_checked} elements checked, {n_overflow} overflow(s) found")


# ------------------------------------------------------------------ comment scan
def scan_comments(path, diag):
    """E006: XML comments inside mxGraphModel are not allowed in this skill's output."""
    try:
        with open(path) as f:
            content = f.read()
    except OSError:
        return
    # Crude scan — flag any <!-- inside <mxGraphModel>...</mxGraphModel>
    start = content.find("<mxGraphModel")
    if start == -1:
        return
    end = content.find("</mxGraphModel>", start)
    if end == -1:
        return
    inner = content[start:end]
    if "<!--" in inner:
        diag.warn("E006", "XML comment found inside <mxGraphModel> — remove for Lucidchart compatibility")


DEFAULT_FEATURES = {
    "quality_gate": "on",
    "grounding_manifest": "on",
    "text_metrics": "auto",
}


def parse_features(spec, defaults=None):
    """Parse 'k1=v1,k2=v2' into dict, merged over defaults."""
    out = dict(defaults or DEFAULT_FEATURES)
    if not spec:
        return out
    for part in spec.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _auto_plan_path(drawio_path):
    """If <name>.drawio has a sibling <name>.plan.json, return it."""
    import os
    base, ext = os.path.splitext(drawio_path)
    candidate = base + ".plan.json"
    return candidate if os.path.isfile(candidate) else None


def _auto_annotated_plan_path(drawio_path):
    """If <name>.drawio has a sibling <name>.annotated.plan.json, return it."""
    import os
    base, _ = os.path.splitext(drawio_path)
    candidate = base + ".annotated.plan.json"
    return candidate if os.path.isfile(candidate) else None


def _collect_cells(root):
    """Return three page-keyed dicts: by_id, geoms, styles — spanning all mxGraphModel pages."""
    by_id_map = {}
    geoms_map = {}
    styles_map = {}
    for i, model in enumerate(root.iter("mxGraphModel")):
        key = str(i)
        by_id = {}
        geoms = {}
        styles = {}
        for c in iter_cells(model):
            cid = c.get("id")
            if not cid:
                continue
            by_id[cid] = c
            geoms[cid] = geom_of(c)
            styles[cid] = style_kv(c)
        by_id_map[key] = by_id
        geoms_map[key] = geoms
        styles_map[key] = styles
    return by_id_map, geoms_map, styles_map


def main():
    ap = argparse.ArgumentParser(description="Validate a drawio-architect .drawio file")
    ap.add_argument("file", help="Path to .drawio XML file")
    ap.add_argument("--mode", choices=["strict", "standard", "loose"], default="standard")
    ap.add_argument(
        "--features",
        default="",
        help="Comma-separated feature overrides, e.g. 'quality_gate=off,grounding_manifest=off'",
    )
    ap.add_argument(
        "--plan",
        default=None,
        help="Path to JSON plan for F3 grounding checks (default: auto-detect <file>.plan.json)",
    )
    ap.add_argument(
        "--annotated-plan",
        default=None,
        dest="annotated_plan",
        help="Path to annotated plan JSON from text-metrics.js (default: auto-detect <file>.annotated.plan.json)",
    )
    args = ap.parse_args()

    features = parse_features(args.features)

    # Load plan if available (used by F3 grounding)
    plan_path = args.plan or _auto_plan_path(args.file)
    plan = None
    if plan_path:
        import json
        try:
            with open(plan_path) as f:
                plan = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARN  G500: Could not read plan {plan_path}: {e}")
    features["_gt_plan"] = plan

    # Load annotated plan for T8 text metrics check
    import json as _json
    annotated_plan_path = args.annotated_plan or _auto_annotated_plan_path(args.file)
    annotated_plan = None
    if annotated_plan_path:
        try:
            with open(annotated_plan_path) as f:
                annotated_plan = _json.load(f)
        except (OSError, _json.JSONDecodeError) as e:
            print(f"WARN  T800: Could not read annotated plan {annotated_plan_path}: {e}")

    root = load(args.file)
    diag = Diag()
    scan_comments(args.file, diag)

    for model in all_models(root):
        validate_model(model, diag, features)

    grounding_check(plan, diag, features)

    # T8: text metrics — needs cell index across all pages
    if features.get("text_metrics", "auto") != "off" and annotated_plan:
        by_id_map, geoms_map, styles_map = _collect_cells(root)
        text_metrics_check(args.file, annotated_plan, diag, features, by_id_map, geoms_map, styles_map)

    sys.exit(diag.print(args.mode))


if __name__ == "__main__":
    main()
