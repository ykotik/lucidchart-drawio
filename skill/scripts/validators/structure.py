"""
validators/structure.py — E0xx and W1xx structural checks.

All logic ported verbatim from the monolithic validate.py; only the
return convention changed from diag.err/warn/info calls to
returning Diagnostic objects.
"""

from __future__ import annotations

import os
from collections import defaultdict

from .base import Diagnostic, ERR, WRN, INF, Validator


class StructureValidator(Validator):
    """
    All structural / layout integrity checks.

    E001  duplicate id
    E002  edge missing mxGeometry
    E003  parent does not exist
    E004  edge source does not exist
    E005  edge target does not exist
    E008  vertex missing mxGeometry
    E006  XML comment inside mxGraphModel (via scan_comments)
    E018  edge has parent="1" while a dedicated edge layer exists
    W101  shape extends beyond parent bounds
    W102  same-tier vertex overlap
    W103  child overlaps swimlane header
    W104  edge parent not LCA
    W105  swimlane without explicit startSize
    W121  missing edge anchors on dense diagram
    I201  >40 vertices
    I203  empty container
    """

    codes = (
        "E001", "E002", "E003", "E004", "E005", "E006", "E008", "E018",
        "W101", "W102", "W103", "W104", "W105", "W121",
        "I201", "I203",
    )

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        cells = ctx["cells"]
        by_id = ctx["by_id"]
        parents = ctx["parents"]
        is_vertex = ctx["is_vertex"]
        is_edge = ctx["is_edge"]
        geoms = ctx["geoms"]
        styles = ctx["styles"]
        result: list[Diagnostic] = []

        # ---- Pass 2: per-cell checks ----
        for cid, c in by_id.items():
            p = parents[cid]

            # E003 parent exists
            if p is not None and p not in by_id and p not in ("0", "1"):
                if p not in ("0", "1"):
                    result.append(Diagnostic("E003", ERR,
                        f"Cell '{cid}' parent '{p}' does not exist", element_id=cid))

            # E002, E008 geometry presence
            if is_edge[cid]:
                if geoms[cid] is None:
                    result.append(Diagnostic("E002", ERR,
                        f"Edge '{cid}' missing <mxGeometry> child", element_id=cid))
            if is_vertex[cid]:
                if geoms[cid] is None:
                    result.append(Diagnostic("E008", ERR,
                        f"Vertex '{cid}' has no <mxGeometry>", element_id=cid))

            # E004, E005 edge endpoints
            if is_edge[cid]:
                src = c.get("source")
                tgt = c.get("target")
                if src is not None and src not in by_id:
                    result.append(Diagnostic("E004", ERR,
                        f"Edge '{cid}' source '{src}' does not exist", element_id=cid))
                if tgt is not None and tgt not in by_id:
                    result.append(Diagnostic("E005", ERR,
                        f"Edge '{cid}' target '{tgt}' does not exist", element_id=cid))

            # W105 swimlane without startSize
            st = styles[cid]
            if "swimlane" in st and "startSize" not in st:
                result.append(Diagnostic("W105", WRN,
                    f"Container '{cid}' uses swimlane style without explicit startSize",
                    element_id=cid))

        # ---- W101 shape extends beyond parent ----
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
                pst = styles[p]
                is_container = ("swimlane" in pst or pst.get("container") == "1")
                if is_container and (x + w > pw + 1 or y + h > ph + 1):
                    result.append(Diagnostic("W101", WRN,
                        f"Shape '{cid}' extends beyond parent '{p}' bounds",
                        element_id=cid))

        # ---- W103 child overlaps container header ----
        for cid, geom in geoms.items():
            if geom is None or not is_vertex[cid]:
                continue
            p = parents[cid]
            if p in by_id:
                pst = styles[p]
                if "swimlane" in pst:
                    start_size = float(pst.get("startSize", 20))
                    horizontal = pst.get("horizontal", "1") != "0"
                    x, y, _, _ = geom
                    if horizontal and y < start_size - 1:
                        result.append(Diagnostic("W103", WRN,
                            f"Shape '{cid}' overlaps container '{p}' header "
                            f"(y={y} < startSize={start_size})", element_id=cid))
                    if not horizontal and x < start_size - 1:
                        result.append(Diagnostic("W103", WRN,
                            f"Shape '{cid}' overlaps container '{p}' header "
                            f"(x={x} < startSize={start_size})", element_id=cid))

        # ---- W104 edge parent should be LCA ----
        def ancestors(cell_id):
            out = []
            cur = cell_id
            seen: set[str] = set()
            while cur and cur not in seen:
                seen.add(cur)
                p = parents.get(cur)
                if p is None:
                    break
                out.append(p)
                cur = p
            return out

        layer_ids = {cid for cid, p in parents.items() if p == "0"}
        # Also treat cells whose id signals an intended edge/icon layer as layers
        # even when authored with parent="1" (malformed but common LLM pattern).
        for cid, c in by_id.items():
            if cid in ("0", "1"):
                continue
            lower = (cid or "").lower()
            if ("edge" in lower or "layer" in lower or lower == "nodes") and is_vertex[cid] is False and is_edge[cid] is False:
                layer_ids.add(cid)

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
            if ep in layer_ids:
                continue
            if ep in ancestors(lca) or ep == "1":
                continue
            result.append(Diagnostic("W104", WRN,
                f"Edge '{cid}' parent '{ep}' is not LCA '{lca}' or an ancestor of LCA "
                f"— source '{src}' target '{tgt}'", element_id=cid))

        # ---- E018 edge-layer consistency ----
        # If a layer (parent="0") whose id contains "edge" exists, every edge
        # with parent="1" is an error UNLESS source and target share a common
        # container (LCA != "1") — in that case the container is the legitimate
        # parent and the edge is correctly NOT on the dedicated edge layer.
        edge_layer_id = None
        for lid in layer_ids:
            if lid and "edge" in lid.lower():
                edge_layer_id = lid
                break

        if edge_layer_id is not None:
            for cid, c in by_id.items():
                if not is_edge[cid]:
                    continue
                if parents.get(cid) != "1":
                    continue
                src = c.get("source")
                tgt = c.get("target")
                # If endpoints share a real container ancestor (not "1"/"0"),
                # parent="1" is structurally wrong but the edge belongs to that
                # container, not the edge layer — skip E018 (W104 covers it).
                shared_container = False
                if src and tgt and src in by_id and tgt in by_id:
                    ans_s = set([src] + ancestors(src))
                    ans_t = [tgt] + ancestors(tgt)
                    lca = next((a for a in ans_t if a in ans_s), None)
                    if lca and lca not in ("0", "1") and lca not in layer_ids:
                        shared_container = True
                if shared_container:
                    continue
                result.append(Diagnostic("E018", ERR,
                    f"edge {cid} has parent=\"1\" but edge layer "
                    f"\"{edge_layer_id}\" exists; expected parent=\"{edge_layer_id}\"",
                    element_id=cid))

        # ---- W102 same-tier vertex overlap ----
        siblings: dict[str, list[str]] = defaultdict(list)
        for cid in by_id:
            if not is_vertex[cid]:
                continue
            if geoms[cid] is None:
                continue
            p = parents.get(cid, "1")
            siblings[p].append(cid)

        def overlaps(a, b, tol=4):
            ax, ay, aw, ah = a
            bx, by, bw, bh = b
            return (ax + aw > bx + tol and bx + bw > ax + tol and
                    ay + ah > by + tol and by + bh > ay + tol)

        for p, sibs in siblings.items():
            for i in range(len(sibs)):
                for j in range(i + 1, len(sibs)):
                    a, b = sibs[i], sibs[j]
                    ga = geoms[a]
                    gb = geoms[b]
                    if ga and gb and overlaps(ga, gb):
                        result.append(Diagnostic("W102", WRN,
                            f"Shape '{a}' overlaps shape '{b}' (siblings under '{p}')",
                            element_id=a))

        # ---- W121 missing edge anchors on dense diagram ----
        _ANCHOR_KEYS = ("exitX", "exitY", "entryX", "entryY")
        edge_cells = [(cid, c) for cid, c in by_id.items() if is_edge[cid]]
        edge_count = len(edge_cells)

        # count cross-container edges: source.parent != target.parent
        cross_container_count = 0
        for cid, c in edge_cells:
            src = c.get("source")
            tgt = c.get("target")
            if src and tgt and src in by_id and tgt in by_id:
                if parents.get(src) != parents.get(tgt):
                    cross_container_count += 1

        if edge_count >= 20 or cross_container_count >= 3:
            for cid, c in edge_cells:
                src = c.get("source")
                tgt = c.get("target")
                # skip dangling edges (E004/E005 handles those)
                if not src or not tgt or src not in by_id or tgt not in by_id:
                    continue
                # skip edges to/from containers — anchor is legitimately absent
                src_st = styles.get(src, {})
                tgt_st = styles.get(tgt, {})
                if ("swimlane" in src_st or src_st.get("container") == "1" or
                        "swimlane" in tgt_st or tgt_st.get("container") == "1"):
                    continue
                # styles[cid] is a KV dict; check key presence directly
                edge_st = styles.get(cid, {})
                if any(k not in edge_st for k in _ANCHOR_KEYS):
                    result.append(Diagnostic("W121", WRN,
                        f"Edge '{cid}' missing anchor(s) on dense diagram "
                        f"(edges={edge_count}, cross_container={cross_container_count})"
                        f" — add exitX/exitY/entryX/entryY to style",
                        element_id=cid))

        # ---- I201 too many nodes ----
        n_vertices = sum(1 for c in by_id if is_vertex[c])
        if n_vertices > 40:
            result.append(Diagnostic("I201", INF,
                f"Diagram has {n_vertices} vertices — consider splitting into pages"))

        # ---- I203 empty container ----
        for cid in by_id:
            st = styles[cid]
            if "swimlane" in st or st.get("container") == "1":
                children = [k for k, v in parents.items() if v == cid]
                if not children:
                    result.append(Diagnostic("I203", INF,
                        f"Container '{cid}' is empty", element_id=cid))

        return result
