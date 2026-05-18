#!/usr/bin/env python3
"""
lucidchart-drawio validator (v2)

Pre-flight checks for .drawio files produced by the lucidchart-drawio skill.

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
def validate_model(model, diag):
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


def main():
    ap = argparse.ArgumentParser(description="Validate a lucidchart-drawio .drawio file")
    ap.add_argument("file", help="Path to .drawio XML file")
    ap.add_argument("--mode", choices=["strict", "standard", "loose"], default="standard")
    args = ap.parse_args()

    root = load(args.file)
    diag = Diag()
    scan_comments(args.file, diag)

    for model in all_models(root):
        validate_model(model, diag)

    sys.exit(diag.print(args.mode))


if __name__ == "__main__":
    main()
