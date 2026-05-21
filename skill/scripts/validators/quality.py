"""
validators/quality.py — Q4xx quality-gate metrics (F2).

Feature flag: quality_gate. Disable with --features quality_gate=off.

Q401  edge crossings (straight-line proxy)
Q402  orthogonality conformance %
Q403  edge-length coefficient of variation
Q404  area utilization
Q405  text overflow heuristic
"""

from __future__ import annotations

import re as _re

from .base import Diagnostic, ERR, WRN, INF, Validator

# Patterns where non-orthogonal edges are intentional (radial spokes, lifeline crossings).
Q402_EXEMPT_PATTERNS: frozenset[str] = frozenset({"hub-radial", "sequence"})


# ---------------------------------------------------------------- geometry helpers

def _resolve_canvas_xy(cid, geoms, parents, by_id):
    """Canvas-absolute (x,y,w,h) by walking parent chain."""
    if cid not in geoms or geoms[cid] is None:
        return None
    x, y, w, h = geoms[cid]
    p = parents.get(cid)
    while p and p in by_id and p not in ("0", "1"):
        pg = geoms.get(p)
        if pg is None:
            break
        px, py, _, _ = pg
        ps = (by_id[p].get("style", "") or "")
        if "swimlane" in ps:
            ss = 20
            for kv in ps.split(";"):
                if kv.startswith("startSize="):
                    try:
                        ss = float(kv.split("=", 1)[1])
                    except ValueError:
                        pass
                    break
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


def _segments_intersect(a1, a2, b1, b2) -> bool:
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])

    if a1 == b1 or a1 == b2 or a2 == b1 or a2 == b2:
        return False
    d1 = ccw(b1, b2, a1)
    d2 = ccw(b1, b2, a2)
    d3 = ccw(a1, a2, b1)
    d4 = ccw(a1, a2, b2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _strip_html(s: str) -> str:
    if not s:
        return ""
    s = (s.replace("&amp;", "&").replace("&lt;", "<")
          .replace("&gt;", ">").replace("&quot;", '"').replace("&nbsp;", " "))
    return _re.sub(r"<[^>]+>|&[a-z]+;|&#x?[0-9a-f]+;", "", s,
                   flags=_re.IGNORECASE).strip()


# ---------------------------------------------------------------- validator

class QualityValidator(Validator):
    codes = ("Q401", "Q402", "Q403", "Q404", "Q405")

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        features = ctx["features"]
        if features.get("quality_gate", "on") != "on":
            return []

        by_id   = ctx["by_id"]
        parents = ctx["parents"]
        is_vertex = ctx["is_vertex"]
        is_edge   = ctx["is_edge"]
        geoms   = ctx["geoms"]
        styles  = ctx["styles"]
        result: list[Diagnostic] = []

        # Canvas-absolute centers for each vertex
        centers: dict[str, tuple[float, float]] = {}
        for cid in by_id:
            if not is_vertex[cid]:
                continue
            ab = _resolve_canvas_xy(cid, geoms, parents, by_id)
            if ab is None:
                continue
            x, y, w, h = ab
            centers[cid] = (x + w / 2.0, y + h / 2.0)

        # ---------- Q401 edge crossings ----------
        edge_segments: list[tuple[str, tuple, tuple]] = []
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
        result.append(Diagnostic("Q401", INF,
            f"Edge crossings (straight-line proxy): {n_cross}"))
        if len(edge_segments) >= 6 and n_cross > max(2, len(edge_segments) // 4):
            result.append(Diagnostic("Q401", WRN,
                f"High edge-crossing count: {n_cross} crossings over {len(edge_segments)} edges "
                f"(threshold = max(2, edges/4) = {max(2, len(edge_segments) // 4)}) — "
                f"run scripts/route-edges.py (F7) then re-validate; "
                f"for structural overlaps also run scripts/elk-layout.py (F4)"))

        # ---------- Q402 orthogonality conformance ----------
        # Detect layout pattern: prefer root attribute → ctx key → cell-ID heuristic.
        _pattern: str = ""
        if model is not None:
            _pattern = (model.get("data-layout-pattern") or "").strip().lower()
        if not _pattern:
            _pattern = str(ctx.get("pattern", "")).strip().lower()
        if not _pattern:
            # Last-resort: infer from well-known sentinel cell IDs.
            _ids = set(by_id.keys())
            if "hub" in _ids:
                _pattern = "hub-radial"
            elif any(cid.startswith("lifeline") for cid in _ids):
                _pattern = "sequence"

        if _pattern in Q402_EXEMPT_PATTERNS:
            result.append(Diagnostic("Q402", INF,
                f"Skipped (pattern '{_pattern}' exempt from orthogonality check)"))
        else:
            n_edges = sum(1 for cid in by_id if is_edge[cid])
            n_ortho = sum(
                1 for cid in by_id
                if is_edge[cid]
                and "orthogonalEdgeStyle" in (styles[cid].get("edgeStyle", "") or "")
            )
            if n_edges > 0:
                pct = (n_ortho / n_edges) * 100.0
                result.append(Diagnostic("Q402", INF,
                    f"Orthogonality conformance: {n_ortho}/{n_edges} = {pct:.0f}%"))
                if pct < 80.0 and n_edges >= 4:
                    result.append(Diagnostic("Q402", WRN,
                        f"Low orthogonality ({pct:.0f}%) — architecture diagrams read cleanest at >=80% "
                        f"orthogonal. Add edgeStyle=orthogonalEdgeStyle to remaining edges."))

        # ---------- Q403 edge-length CV ----------
        lengths: list[float] = []
        for _, a, b in edge_segments:
            dx = a[0] - b[0]
            dy = a[1] - b[1]
            lengths.append((dx * dx + dy * dy) ** 0.5)
        if len(lengths) >= 3:
            mean = sum(lengths) / len(lengths)
            var = sum((L - mean) ** 2 for L in lengths) / len(lengths)
            std = var ** 0.5
            cv = (std / mean) if mean > 1e-6 else 0.0
            result.append(Diagnostic("Q403", INF,
                f"Edge-length CV: {cv:.2f} (mean={mean:.0f}px, std={std:.0f}px)"))
            if cv > 1.2:
                result.append(Diagnostic("Q403", WRN,
                    f"High edge-length variance (CV={cv:.2f}). One or two edges dominate — "
                    f"consider re-grouping shapes or running auto_layout=elk."))

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
                result.append(Diagnostic("Q404", INF,
                    f"Area utilization: {util * 100:.1f}% (nodes/bbox)"))
                if util < 0.10 and len(all_geoms) >= 6:
                    result.append(Diagnostic("Q404", WRN,
                        f"Low area utilization ({util * 100:.1f}%) — shapes are spread thin. "
                        f"Tighten spacing or scale canvas down."))
                if util > 0.65:
                    result.append(Diagnostic("Q404", WRN,
                        f"High area utilization ({util * 100:.1f}%) — diagram is crowded. "
                        f"Add gutter or scale canvas up."))

        # ---------- Q405 text overflow ----------
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
            sp = float(st.get("spacing", 2))
            sl = float(st.get("spacingLeft", sp))
            sr = float(st.get("spacingRight", sp))
            stp = float(st.get("spacingTop", sp))
            sb = float(st.get("spacingBottom", sp))
            hdr = float(st.get("startSize", 0)) if "swimlane" in st else 0
            avail_w = max(1.0, gw - sl - sr)
            avail_h = max(1.0, gh - hdr - stp - sb)
            wrap = st.get("whiteSpace") == "wrap"
            lines = [_strip_html(p) for p in _re.split(r"<br\s*/?>|\n", value,
                                                        flags=_re.IGNORECASE)
                     if _strip_html(p)]
            if not lines:
                continue
            char_w = fs * 0.55
            line_h = fs * 1.2
            if wrap:
                max_chars = max(1, int(avail_w / char_w))
                total = sum(max(1, -(-len(L) // max_chars)) for L in lines)
                fits = total * line_h <= avail_h
            else:
                fits = (len(lines) * line_h <= avail_h and
                        all(len(L) * char_w <= avail_w for L in lines))
            if not fits:
                n_overflow += 1
                if n_overflow <= 5:
                    result.append(Diagnostic("Q405", WRN,
                        f"Cell '{cid}' text overflows at fontSize={int(fs)} "
                        f"(w={gw:.0f} h={gh:.0f}, label='{_strip_html(value)[:40]}'). "
                        f"Run scripts/fit-fonts.py.",
                        element_id=cid))
        if n_overflow > 0:
            result.append(Diagnostic("Q405", INF,
                f"Text overflow: {n_overflow} cell(s) at current fontSize"))

        return result
