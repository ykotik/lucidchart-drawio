#!/usr/bin/env python3
"""
drawio-architect plan bootstrapper (v1)

Given an existing .drawio file, extracts all containers, shapes, and edges
and auto-generates a boilerplate .plan.json file with empty "cite": "" fields.

Usage:
    python3 bootstrap-plan.py path/to/diagram.drawio
    python3 bootstrap-plan.py path/to/diagram.drawio --out custom_plan.json
"""

import argparse
import sys
import os
import re
import json
import xml.etree.ElementTree as ET

# ------------------------------------------------------------- helper utilities
def _strip_html(s):
    if not s:
        return ""
    # Replace common HTML entities
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&nbsp;", " ")
    # Strip HTML tags
    return re.sub(r"<[^>]+>|&[a-z]+;|&#x?[0-9a-f]+;", "", s, flags=re.IGNORECASE).strip()


def parse_geometry(cell):
    g = cell.find("mxGeometry")
    if g is None:
        return None
    try:
        x = float(g.get("x", 0))
        y = float(g.get("y", 0))
        w = float(g.get("width", 0))
        h = float(g.get("height", 0))
        return {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
    except (TypeError, ValueError):
        return None


def parse_style(cell):
    s = cell.get("style", "") or ""
    kv = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
        elif part.strip():
            kv[part.strip()] = "1"
    return kv


def guess_style_key(style_dict, cell_type):
    if cell_type == "container":
        stroke = style_dict.get("strokeColor", "").upper()
        if "#2E7D32" in stroke:
            return "scope_green"
        elif "#424242" in stroke or "#757575" in stroke:
            return "scope_black"
        elif "#1565C0" in stroke:
            return "scope_blue"
        elif "#E65100" in stroke:
            return "scope_orange"
        elif "#6A1B9A" in stroke:
            return "scope_purple"
        elif "#C62828" in stroke:
            return "scope_red"
        return "lane_default"
    elif cell_type == "shape":
        if "cylinder" in style_dict or style_dict.get("shape") == "cylinder3":
            return "cylinder_db"
        elif "ellipse" in style_dict or style_dict.get("shape") == "ellipse":
            return "actor_ellipse"
        elif "text" in style_dict or style_dict.get("shape") == "text":
            return "text_label"
        fill = style_dict.get("fillColor", "").upper()
        stroke = style_dict.get("strokeColor", "").upper()
        if "#FFEBEE" in fill or "#C62828" in stroke:
            return "auth_gap"
        if "#E8F5E9" in fill or "#2E7D32" in stroke:
            return "service_box"
        return "shape_default"
    elif cell_type == "edge":
        if style_dict.get("dashed") == "1":
            if "#C62828" in style_dict.get("strokeColor", ""):
                return "edge_orthogonal_remediation"
            return "edge_orthogonal_dashed"
        if "#2E7D32" in style_dict.get("strokeColor", ""):
            return "edge_orthogonal_emphasis"
        return "edge_orthogonal_sync"
    return "default"


# ----------------------------------------------------------------- XML parsing
def load(path):
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as e:
        print(f"ERROR: Malformed XML: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)


def all_models(root):
    for m in root.iter("mxGraphModel"):
        yield m


def iter_cells(model):
    for r in model.iter("root"):
        for c in r.findall("mxCell"):
            yield c
        for c in r.findall("object"):
            inner = c.find("mxCell")
            if inner is not None:
                # objects wrap mxCell; carry id and value/label from object
                inner_copy = ET.Element(inner.tag, attrib=inner.attrib)
                inner_copy.set("id", c.get("id", inner.get("id", "")))
                val = c.get("label") or c.get("value") or c.get("name") or inner.get("value", "")
                inner_copy.set("value", val)
                for child in inner:
                    inner_copy.append(child)
                yield inner_copy


# ------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Bootstrap a plan JSON file from a .drawio file")
    ap.add_argument("file", help="Path to .drawio XML file")
    ap.add_argument("--out", default=None, help="Output path for plan JSON (default: sibling of input)")
    ap.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists")
    args = ap.parse_args()

    root = load(args.file)
    models = list(all_models(root))
    if not models:
        print("ERROR: No mxGraphModel found in diagram.", file=sys.stderr)
        sys.exit(1)
    if len(models) > 1:
        print("WARNING: Multiple pages detected. Extracting first page only.", file=sys.stderr)
    model = models[0]

    by_id = {}
    parents = {}
    is_vertex = {}
    is_edge = {}
    geoms = {}
    styles = {}
    values = {}

    # Extract all cells
    for cell in iter_cells(model):
        cid = cell.get("id")
        if not cid:
            continue
        by_id[cid] = cell
        parents[cid] = cell.get("parent")
        is_vertex[cid] = cell.get("vertex") == "1"
        is_edge[cid] = cell.get("edge") == "1"
        geoms[cid] = parse_geometry(cell)
        styles[cid] = parse_style(cell)
        values[cid] = cell.get("value", "") or ""

    # Helper to resolve absolute canvas coords for bounding box estimation
    def resolve_canvas_coords(cid):
        if cid not in geoms or geoms[cid] is None:
            return 0, 0, 0, 0
        geom = geoms[cid]
        x, y, w, h = geom["x"], geom["y"], geom["w"], geom["h"]
        p = parents.get(cid)
        while p and p in by_id and p not in ("0", "1"):
            pg = geoms.get(p)
            if pg is not None:
                px, py = pg["x"], pg["y"]
                ps = styles.get(p, {})
                if "swimlane" in ps:
                    try:
                        ss = float(ps.get("startSize", 20))
                    except ValueError:
                        ss = 20.0
                    horizontal = ps.get("horizontal", "1") != "0"
                    if horizontal:
                        py += ss
                    else:
                        px += ss
                x += px
                y += py
            p = parents.get(p)
        return x, y, w, h

    # Bounding box estimation for canvas size
    max_x, max_y = 1200, 800
    for cid in by_id:
        if cid in ("0", "1") or is_edge[cid]:
            continue
        cx, cy, cw, ch = resolve_canvas_coords(cid)
        if cx + cw > max_x:
            max_x = cx + cw
        if cy + ch > max_y:
            max_y = cy + ch

    canvas_w = int(max_x + 80)
    canvas_h = int(max_y + 80)

    containers_list = []
    shapes_list = []
    edges_list = []

    # Sort keys for deterministic output ordering
    sorted_cids = sorted(by_id.keys())

    for cid in sorted_cids:
        if cid in ("0", "1"):
            continue
        
        cell = by_id[cid]
        p = parents[cid]
        label = _strip_html(values[cid])
        st = styles[cid]

        if is_vertex[cid]:
            geom = geoms[cid] or {"x": 0, "y": 0, "w": 80, "h": 80}
            is_container = ("swimlane" in st or "pool" in st or st.get("container") == "1" or st.get("shape") == "pool")
            
            if is_container:
                container_dict = {
                    "id": cid,
                    "parent": p if p not in ("0", "1") else "1",
                    "label": label,
                    "x": geom["x"],
                    "y": geom["y"],
                    "w": geom["w"],
                    "h": geom["h"],
                    "style_key": guess_style_key(st, "container"),
                    "cite": ""
                }
                if "swimlane" in st:
                    try:
                        container_dict["startSize"] = int(float(st.get("startSize", 20)))
                    except ValueError:
                        container_dict["startSize"] = 20
                containers_list.append(container_dict)
            else:
                shape_dict = {
                    "id": cid,
                    "parent": p if p not in ("0", "1") else "1",
                    "label": label,
                    "x": geom["x"],
                    "y": geom["y"],
                    "w": geom["w"],
                    "h": geom["h"],
                    "style_key": guess_style_key(st, "shape"),
                    "cite": ""
                }
                shapes_list.append(shape_dict)

        elif is_edge[cid]:
            src = cell.get("source", "")
            tgt = cell.get("target", "")
            edge_dict = {
                "id": cid,
                "parent": p if p not in ("0", "1") else "1",
                "source": src,
                "target": tgt,
                "label": label,
                "style_key": guess_style_key(st, "edge"),
                "cite": ""
            }

            # Extract exit/entry points
            exit_x = st.get("exitX")
            exit_y = st.get("exitY")
            entry_x = st.get("entryX")
            entry_y = st.get("entryY")
            if exit_x is not None and exit_y is not None:
                try:
                    edge_dict["exit"] = {"x": round(float(exit_x), 2), "y": round(float(exit_y), 2)}
                except ValueError:
                    pass
            if entry_x is not None and entry_y is not None:
                try:
                    edge_dict["entry"] = {"x": round(float(entry_x), 2), "y": round(float(entry_y), 2)}
                except ValueError:
                    pass

            # Extract waypoints
            waypoints = []
            g = cell.find("mxGeometry")
            if g is not None:
                arr = g.find("Array")
                if arr is not None and arr.get("as") == "points":
                    for pt in arr.findall("mxPoint"):
                        try:
                            px = float(pt.get("x", 0))
                            py = float(pt.get("y", 0))
                            waypoints.append({"x": int(px), "y": int(py)})
                        except (TypeError, ValueError):
                            pass
            edge_dict["waypoints"] = waypoints
            edges_list.append(edge_dict)

    # Compile the final plan JSON structure
    plan_data = {
        "pattern": "c4-container",
        "canvas": {
            "w": canvas_w,
            "h": canvas_h
        },
        "containers": containers_list,
        "shapes": shapes_list,
        "edges": edges_list
    }

    # Resolve output path
    out_path = args.out
    if not out_path:
        base, _ = os.path.splitext(args.file)
        out_path = base + ".plan.json"

    if os.path.exists(out_path) and not args.force:
        print(f"ERROR: Output file {out_path} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(out_path, "w") as f:
            json.dump(plan_data, f, indent=2)
        print(f"Successfully bootstrapped plan skeleton to: {out_path}")
    except OSError as e:
        print(f"ERROR: Could not write to output path {out_path}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
