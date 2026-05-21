#!/usr/bin/env python3
"""
drawio-architect plan compiler (v1)

Compiles a JSON plan (<name>.plan.json) into a draw.io XML diagram (.drawio file).
By compiling the plan programmatically, we prevent structural errors, XML syntax errors,
layering issues, parent relative offsets mismatches, and grounding omissions.

Usage:
    python3 compile-plan.py path/to/plan.plan.json
    python3 compile-plan.py path/to/plan.plan.json --out output.drawio
    python3 compile-plan.py path/to/plan.plan.json --features grounding_manifest=on
"""

import argparse
import sys
import os
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom

# Style Dictionary Mappings
STYLE_MAP = {
    # Scope containers (CIAM dual-boundary style)
    "scope_green": "swimlane;startSize=26;dashed=1;strokeColor=#2E7D32;strokeWidth=2;fillColor=none;fontColor=#2E7D32;fontSize=12;fontStyle=1;",
    "scope_black": "swimlane;startSize=26;dashed=1;strokeColor=#424242;strokeWidth=1.5;fillColor=none;fontColor=#424242;fontSize=12;fontStyle=1;",
    "scope_blue": "swimlane;startSize=26;dashed=1;strokeColor=#1565C0;strokeWidth=2;fillColor=none;fontColor=#1565C0;fontSize=12;fontStyle=1;",
    "scope_orange": "swimlane;startSize=26;dashed=1;strokeColor=#E65100;strokeWidth=2;fillColor=none;fontColor=#E65100;fontSize=12;fontStyle=1;",
    "scope_purple": "swimlane;startSize=26;dashed=1;strokeColor=#6A1B9A;strokeWidth=2;fillColor=none;fontColor=#6A1B9A;fontSize=12;fontStyle=1;",
    "scope_red": "swimlane;startSize=26;dashed=1;strokeColor=#C62828;strokeWidth=1.5;fillColor=none;fontColor=#C62828;fontSize=12;fontStyle=1;",
    "lane_default": "swimlane;startSize=26;dashed=0;strokeColor=#424242;strokeWidth=1;fillColor=none;fontColor=#424242;fontSize=12;fontStyle=1;",
    
    # DECOM styles
    "decom_shape": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#9E9E9E;strokeWidth=1.5;fontSize=11;dashed=1;fontColor=#757575;",
    "decom_edge": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;strokeColor=#9E9E9E;fontColor=#757575;",

    # Component fill styles
    "hero": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;strokeWidth=3;fontSize=13;fontStyle=1;",
    "internal_enabler": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontSize=12;fontStyle=1;",
    "internal_standard": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=11;",
    "service_box": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=11;",
    "vendor_saas": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;strokeWidth=1;fontSize=11;",
    "external_partner": "rounded=1;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#512DA8;strokeWidth=1;fontSize=11;",
    "auth_gap": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#C62828;strokeWidth=1.5;fontSize=11;",
    "milestone": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#F9A825;strokeWidth=1.5;fontSize=11;",
    "cylinder_db": "shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;strokeWidth=1;fontSize=11;",
    "actor_ellipse": "ellipse;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1565C0;fontSize=11;",
    "text_label": "text;html=1;fontSize=11;fontStyle=1;",

    # Kafka / streaming diagram palette
    "kafka_topic": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;strokeWidth=1.5;fontSize=11;",
    "sink_connector": "rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;strokeWidth=1.5;fontSize=11;",
    "flink_job": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFE6F0;strokeColor=#CC3366;strokeWidth=1.5;fontSize=11;",
    "db_table_view": "rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;strokeWidth=1;fontSize=11;",
    "tenant_container": "swimlane;startSize=24;dashed=0;strokeColor=#6C8EBF;strokeWidth=1.5;fillColor=#EFF5FF;fontColor=#1A237E;fontSize=11;fontStyle=1;",
    "postgres_group": "swimlane;startSize=22;dashed=0;strokeColor=#757575;strokeWidth=1;fillColor=#FAFAFA;fontSize=10;fontStyle=1;",

    # Edge styles
    "edge_orthogonal_sync": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;",
    "standard_flow": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;",
    "edge_orthogonal_dashed": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;",
    "dashed": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;",
    "edge_orthogonal_bidir": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;startArrow=classic;startFill=1;endArrow=classic;endFill=1;",
    "bidirectional": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;startArrow=classic;startFill=1;endArrow=classic;endFill=1;",
    "edge_orthogonal_emphasis": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;strokeColor=#2E7D32;strokeWidth=2;",
    "green_emphasis": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;strokeColor=#2E7D32;strokeWidth=2;",
    "edge_orthogonal_remediation": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;strokeColor=#C62828;",
    "red_remediation": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;strokeColor=#C62828;",
    "edge_orthogonal_future": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;strokeColor=#757575;",
    "dashed_grey": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;dashed=1;strokeColor=#757575;",
}

def resolve_style(style_key, item_type="shape", vendor_icon=None):
    if not style_key:
        if item_type == "container":
            style_key = "lane_default"
        elif item_type == "edge":
            style_key = "standard_flow"
        else:
            style_key = "service_box"
    
    # Check if style_key is a raw style string
    if ";" in style_key or "=" in style_key:
        base_style = style_key
    else:
        base_style = STYLE_MAP.get(style_key, STYLE_MAP["service_box" if item_type == "shape" else "lane_default" if item_type == "container" else "standard_flow"])
    
    if vendor_icon:
        # Map some common vendor icon shapes if present
        if vendor_icon.startswith("aws."):
            base_style += f";shape=mxgraph.aws4.{vendor_icon[4:]};"
        elif vendor_icon.startswith("azure."):
            base_style += f";shape=mxgraph.azure.{vendor_icon[6:]};"
        elif vendor_icon.startswith("gcp."):
            base_style += f";shape=mxgraph.gcp2.{vendor_icon[4:]};"
    
    return base_style

def find_lca(source, target, parent_map):
    ancestors_s = []
    curr = source
    while curr and curr != "1":
        ancestors_s.append(curr)
        curr = parent_map.get(curr)
    ancestors_s.append("1")

    curr = target
    while curr:
        if curr in ancestors_s:
            return curr
        curr = parent_map.get(curr)
    return "1"

def escape_html(s):
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("\n", "&#xa;")

def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    # The default writexml of minidom keeps whitespace if not instructed
    # We want a clean output without adding massive newlines inside text
    return reparsed.toprettyxml(indent="  ")

def compile_plan(plan_path, out_path, features):
    try:
        with open(plan_path) as f:
            plan = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: Could not read or parse JSON plan: {e}", file=sys.stderr)
        sys.exit(1)

    containers = plan.get("containers", []) or []
    shapes = plan.get("shapes", []) or []
    edges = plan.get("edges", []) or []
    canvas = plan.get("canvas", {"w": 1600, "h": 900})

    # Validate Plan & Enforce Grounding Citation Presence
    all_ids = set()
    node_ids = set()
    parent_map = {}
    
    # Build maps
    for kind, items in [("container", containers), ("shape", shapes)]:
        for item in items:
            iid = item.get("id")
            if not iid:
                print(f"ERROR: Plan {kind} is missing 'id'", file=sys.stderr)
                sys.exit(1)
            if iid in all_ids:
                print(f"ERROR: Duplicate id '{iid}' in plan", file=sys.stderr)
                sys.exit(1)
            all_ids.add(iid)
            node_ids.add(iid)
            parent_map[iid] = item.get("parent", "1") or "1"

    for edge in edges:
        eid = edge.get("id")
        if eid:
            if eid in all_ids:
                print(f"ERROR: Duplicate id '{eid}' in plan (edge ID conflict)", file=sys.stderr)
                sys.exit(1)
            all_ids.add(eid)

    # 1. Grounding check
    if features.get("grounding_manifest", "on") == "on":
        missing_cites = []
        for kind, items in [("container", containers), ("shape", shapes), ("edge", edges)]:
            for item in items:
                iid = item.get("id", "<no-id>")
                cite = (item.get("cite") or "").strip()
                if not cite:
                    missing_cites.append(f"{kind} '{iid}'")
        if missing_cites:
            print("ERROR: Compilation aborted due to missing grounding citations:", file=sys.stderr)
            for mc in missing_cites:
                print(f"  - {mc} has no 'cite' field", file=sys.stderr)
            sys.exit(1)

    # 2. Structure checking
    for node_id, parent_id in parent_map.items():
        if parent_id not in node_ids and parent_id != "1":
            print(f"ERROR: Parent '{parent_id}' of node '{node_id}' does not exist", file=sys.stderr)
            sys.exit(1)

    # Begin XML construction
    # Use output mode (default bare if single page, wrapped otherwise)
    output_mode = features.get("output_mode", "auto")
    is_wrapped = (output_mode == "wrapped" or output_mode == "auto") # Default to wrapped for full document

    # Create root model structure
    mx_model = ET.Element("mxGraphModel", {
        "dx": str(canvas.get("w", 1600)),
        "dy": str(canvas.get("h", 900)),
        "grid": "1",
        "gridSize": "10",
        "guides": "1",
        "tooltips": "1",
        "connect": "1",
        "arrows": "1",
        "fold": "1",
        "page": "1",
        "pageScale": "1",
        "pageWidth": str(canvas.get("w", 1600)),
        "pageHeight": str(canvas.get("h", 900)),
        "math": "0",
        "shadow": "0"
    })
    
    root = ET.SubElement(mx_model, "root")
    
    # Layer 0 (default) & Layer 1 (default icon layer)
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    
    # Layer for edges (Two-layer rendering pattern: edges layer is rendered behind shape layer 1)
    # This prevents edges from rendering on top of shape icons/glyphs!
    edges_layer_id = "edges_layer"
    ET.SubElement(root, "mxCell", {
        "id": edges_layer_id,
        "parent": "0",
        "value": "Edges"
    })

    # Helper function to create mxCell / object elements
    def create_element(item, item_type="shape"):
        iid = item["id"]
        label = item.get("label", "")
        cite = (item.get("cite") or "").strip()
        style_key = item.get("style_key")
        vendor_icon = item.get("vendor_icon")
        
        resolved_style = resolve_style(style_key, item_type, vendor_icon)
        
        # Add exit/entry details to edge styles
        if item_type == "edge":
            exit_pt = item.get("exit")
            entry_pt = item.get("entry")
            if exit_pt:
                resolved_style += f";exitX={exit_pt.get('x', 0)};exitY={exit_pt.get('y', 0.5)};exitDx=0;exitDy=0"
            if entry_pt:
                resolved_style += f";entryX={entry_pt.get('x', 0)};entryY={entry_pt.get('y', 0.5)};entryDx=0;entryDy=0"
        
        parent = item.get("parent", "1") or "1"
        
        # XML Element: use <object> if cite is present, else standard <mxCell>
        if cite:
            el = ET.Element("object", {
                "id": iid,
                "label": label,
                "cite": cite
            })
            mx_cell = ET.SubElement(el, "mxCell", {
                "style": resolved_style,
                "parent": parent
            })
        else:
            el = ET.Element("mxCell", {
                "id": iid,
                "value": label,
                "style": resolved_style,
                "parent": parent
            })
            mx_cell = el

        if item_type == "edge":
            mx_cell.set("edge", "1")
            
            # Geometry for edge (relative = 1 is mandatory!)
            mx_geom = ET.SubElement(mx_cell, "mxGeometry", {
                "relative": "1",
                "as": "geometry"
            })
            
            # Waypoints (if any)
            waypoints = item.get("waypoints", [])
            if waypoints:
                arr = ET.SubElement(mx_geom, "Array", {"as": "points"})
                for pt in waypoints:
                    ET.SubElement(arr, "mxPoint", {
                        "x": str(pt.get("x", 0)),
                        "y": str(pt.get("y", 0))
                    })
        else:
            mx_cell.set("vertex", "1")
            
            # Geometry for node
            x = item.get("x", 0)
            y = item.get("y", 0)
            w = item.get("w", 120)
            h = item.get("h", 60)
            
            # Prevent overlap with swimlane headers
            if item_type == "shape" and parent != "1":
                # Find parent container startSize
                parent_container = next((c for c in containers if c["id"] == parent), None)
                if parent_container:
                    p_style = parent_container.get("style_key")
                    start_size = 26 # Default
                    if p_style and p_style.startswith("swimlane") or "swimlane" in resolve_style(p_style, "container"):
                        # Try parsing startSize from resolved style
                        style_str = resolve_style(p_style, "container")
                        for part in style_str.split(";"):
                            if part.startswith("startSize="):
                                try:
                                    start_size = int(part.split("=")[1])
                                except ValueError:
                                    pass
                                break
                    if y < start_size:
                        print(f"WARNING: Shape '{iid}' y-coord ({y}) is inside container '{parent}' header (startSize={start_size}). Automatically shifting down.", file=sys.stderr)
                        y = start_size + 10
            
            ET.SubElement(mx_cell, "mxGeometry", {
                "x": str(x),
                "y": str(y),
                "width": str(w),
                "height": str(h),
                "as": "geometry"
            })
            
        return el

    # Add containers to root
    for container in containers:
        root.append(create_element(container, "container"))

    # Add shapes to root
    for shape in shapes:
        root.append(create_element(shape, "shape"))

    # Add edges to root
    for edge in edges:
        # Enforce edge layer parent (Two-layer rendering: edges are parented to the edges_layer)
        edge["parent"] = edges_layer_id
        
        # Resolve source/target IDs and calculate LCA for validation if needed
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            print(f"ERROR: Edge '{edge.get('id', '<no-id>')}' must specify source and target", file=sys.stderr)
            sys.exit(1)
        if source not in node_ids:
            print(f"ERROR: Edge source '{source}' does not exist", file=sys.stderr)
            sys.exit(1)
        if target not in node_ids:
            print(f"ERROR: Edge target '{target}' does not exist", file=sys.stderr)
            sys.exit(1)
            
        root.append(create_element(edge, "edge"))

    # Generate Legend if requested
    legend = plan.get("legend")
    if legend and legend.get("include"):
        # Create standard chip legend
        pos = legend.get("position", "bottom-right")
        leg_w, leg_h = 240, 100
        canvas_w = canvas.get("w", 1600)
        canvas_h = canvas.get("h", 900)
        
        if pos == "bottom-right":
            leg_x = canvas_w - leg_w - 40
            leg_y = canvas_h - leg_h - 40
        elif pos == "bottom-left":
            leg_x = 40
            leg_y = canvas_h - leg_h - 40
        elif pos == "top-right":
            leg_x = canvas_w - leg_w - 40
            leg_y = 40
        else: # top-left
            leg_x = 40
            leg_y = 40
            
        # Draw legend container
        leg_container = {
            "id": "legend_container",
            "label": "Legend",
            "parent": "1",
            "x": leg_x, "y": leg_y, "w": leg_w, "h": leg_h,
            "style_key": "swimlane;startSize=22;dashed=0;strokeColor=#999999;strokeWidth=1;fillColor=#FAFAFA;fontColor=#424242;fontSize=10;fontStyle=1;",
            "cite": "template-default"
        }
        root.append(create_element(leg_container, "container"))
        
        # Legend items
        items = legend.get("items", ["sync", "async"])
        y_offset = 30
        for i, item in enumerate(items):
            chip_id = f"legend_chip_{i}"
            if item == "sync" or item == "primary":
                chip_style = "rounded=12;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=10;fontStyle=1;"
                chip_label = "Primary / Synchronous"
            elif item == "async" or item == "secondary":
                chip_style = "rounded=12;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;strokeWidth=1;fontSize=10;fontStyle=1;"
                chip_label = "Secondary / Asynchronous"
            elif item == "auth" or item == "warning":
                chip_style = "rounded=12;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#C62828;strokeWidth=1.5;fontSize=10;fontStyle=1;"
                chip_label = "Auth Gap / Warning"
            else:
                chip_style = "rounded=12;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#9E9E9E;strokeWidth=1;fontSize=10;fontStyle=1;"
                chip_label = item.capitalize()
                
            chip_cell = ET.Element("object", {
                "id": chip_id,
                "label": chip_label,
                "cite": "template-default"
            })
            ET.SubElement(chip_cell, "mxCell", {
                "style": chip_style,
                "parent": "legend_container",
                "vertex": "1"
            })
            ET.SubElement(chip_cell, "mxGeometry", {
                "x": "20",
                "y": str(y_offset),
                "width": "200",
                "height": "18",
                "as": "geometry"
            })
            root.append(chip_cell)
            y_offset += 22

    # Wrap the XML if needed
    if is_wrapped:
        mx_file = ET.Element("mxfile", {
            "host": "Electron",
            "modified": "2026-05-21T00:00:00.000Z",
            "agent": "diagrams.net",
            "etag": "compiled-diagram",
            "version": "24.7.17",
            "type": "device"
        })
        diagram = ET.SubElement(mx_file, "diagram", {
            "id": "compiled-id",
            "name": "Compiled Diagram"
        })
        diagram.append(mx_model)
        output_element = mx_file
    else:
        output_element = mx_model

    # Pretty print XML string
    xml_str = prettify_xml(output_element)
    
    # Write to file
    try:
        with open(out_path, "w") as f:
            f.write(xml_str)
        print(f"Successfully compiled JSON plan to draw.io XML: {out_path}")
    except OSError as e:
        print(f"ERROR: Could not write to output file {out_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    ap = argparse.ArgumentParser(description="Compile a drawio-architect JSON plan to a .drawio XML diagram")
    ap.add_argument("file", help="Path to .plan.json file")
    ap.add_argument("--out", default=None, help="Output path for .drawio diagram (default: sibling of input)")
    ap.add_argument(
        "--features",
        default="",
        help="Comma-separated feature overrides, e.g. 'grounding_manifest=on,output_mode=bare'",
    )
    args = ap.parse_args()

    # Feature flags parsing
    features = {
        "grounding_manifest": "on",
        "output_mode": "auto"
    }
    if args.features:
        for part in args.features.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                features[k.strip()] = v.strip()

    # Resolve output path
    out_path = args.out
    if not out_path:
        base, _ = os.path.splitext(args.file)
        # Handle cases where input is .plan.json or just .json
        if base.endswith(".plan"):
            out_path = base[:-5] + ".drawio"
        else:
            out_path = base + ".drawio"

    compile_plan(args.file, out_path, features)

if __name__ == "__main__":
    main()
