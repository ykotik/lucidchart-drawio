#!/usr/bin/env python3
"""
F5: ELK auto-layout for drawio-architect .drawio files

Replaces LLM-emitted coordinates with output from the Eclipse Layout Kernel
(ELK Layered, the production-quality hierarchical engine). Falls back to
Graphviz `dot` if ELK is unavailable.

Per eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html:
- Routing styles: straight | orthogonal | splines  (we use orthogonal)
- Node placement: BRANDES_KOEPF (default) | LINEAR_SEGMENTS | NETWORK_SIMPLEX | SIMPLE
- Hierarchy handling: INCLUDE_CHILDREN | SEPARATE_CHILDREN (we use INCLUDE_CHILDREN)

Usage:
    python3 elk-layout.py path/to/diagram.drawio [path/to/output.drawio]
    python3 elk-layout.py diagram.drawio --engine elk           # default
    python3 elk-layout.py diagram.drawio --engine dot           # Graphviz fallback
    python3 elk-layout.py diagram.drawio --direction RIGHT      # or DOWN/LEFT/UP
    python3 elk-layout.py diagram.drawio --features auto_layout=elk

If output path omitted, writes to `<input-stem>.laid-out.drawio` (does not
overwrite the source).

Requirements:
    --engine elk  →  Node.js + `npx -y elkjs` (auto-fetched on first run)
    --engine dot  →  Graphviz (`brew install graphviz`)
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


# ============================================================ parse .drawio


def iter_cells(root):
    for r in root.iter("root"):
        for c in r.findall("mxCell"):
            yield c


def geom_of(cell):
    g = cell.find("mxGeometry")
    if g is None:
        return None
    try:
        return (
            float(g.get("x", 0)),
            float(g.get("y", 0)),
            float(g.get("width", 0)),
            float(g.get("height", 0)),
        )
    except (TypeError, ValueError):
        return None


def style_kv(cell):
    s = cell.get("style", "") or ""
    kv = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


# ============================================================ build ELK graph


def build_elk_graph(drawio_root, direction="RIGHT"):
    """Convert mxGraphModel → ELK JSON graph.

    Output schema (https://www.eclipse.org/elk/documentation/tooldevelopers/graphdatastructure/jsonformat.html):
      { id, layoutOptions, children: [{id, width, height, children?}], edges: [{id, sources, targets}] }
    """
    cells = list(iter_cells(drawio_root))
    if not cells:
        return None, {}, {}

    by_id = {c.get("id"): c for c in cells if c.get("id")}
    parents = {cid: c.get("parent") for cid, c in by_id.items()}
    is_vertex = {cid: c.get("vertex") == "1" for cid, c in by_id.items()}
    is_edge = {cid: c.get("edge") == "1" for cid, c in by_id.items()}
    geoms = {cid: geom_of(c) for cid, c in by_id.items()}
    styles = {cid: style_kv(c) for cid, c in by_id.items()}

    def is_container(cid):
        s = styles.get(cid, {})
        return ("swimlane" in (by_id[cid].get("style") or "")) or s.get("container") == "1"

    # Children index
    children_of = {}
    for cid, p in parents.items():
        if p:
            children_of.setdefault(p, []).append(cid)

    def build_node(cid):
        g = geoms.get(cid)
        w = (g[2] if g else 160) or 160
        h = (g[3] if g else 64) or 64
        node = {"id": cid, "width": w, "height": h}
        # Recurse for containers
        cs = []
        for ch in children_of.get(cid, []):
            if is_vertex.get(ch):
                cs.append(build_node(ch))
        if cs:
            node["children"] = cs
            node["layoutOptions"] = {
                "elk.padding": "[top=40,left=20,bottom=20,right=20]",
                "elk.algorithm": "layered",
                "elk.direction": direction,
            }
        return node

    # Top-level children are nodes whose parent is "1" or "0"
    top_nodes = []
    for cid in by_id:
        if not is_vertex.get(cid):
            continue
        if parents.get(cid) in ("1", "0", None):
            top_nodes.append(build_node(cid))

    # Edges (only those between vertices we know about)
    elk_edges = []
    for cid, c in by_id.items():
        if not is_edge.get(cid):
            continue
        s = c.get("source")
        t = c.get("target")
        if s in by_id and t in by_id and is_vertex.get(s) and is_vertex.get(t):
            elk_edges.append({"id": cid, "sources": [s], "targets": [t]})

    graph = {
        "id": "root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": direction,
            "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
            "elk.layered.nodePlacement.bk.edgeStraightening": "IMPROVE_STRAIGHTNESS",
            "elk.edgeRouting": "ORTHOGONAL",
            "elk.hierarchyHandling": "INCLUDE_CHILDREN",
            "elk.spacing.nodeNode": "60",
            "elk.layered.spacing.nodeNodeBetweenLayers": "80",
            "elk.spacing.edgeNode": "20",
            "elk.spacing.edgeEdge": "16",
        },
        "children": top_nodes,
        "edges": elk_edges,
    }

    return graph, by_id, parents


# ============================================================ call ELK / dot


ELK_RUNNER_JS = r"""
const elkPkg = await import('elkjs');
const ELK = elkPkg.default || elkPkg.ELK;
const elk = new ELK();
const input = JSON.parse(await new Promise(res => {
  let s = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', d => s += d);
  process.stdin.on('end', () => res(s));
}));
try {
  const out = await elk.layout(input);
  process.stdout.write(JSON.stringify(out));
} catch (e) {
  process.stderr.write("ELK layout failed: " + e.message + "\n");
  process.exit(2);
}
"""


def run_elk(graph):
    """Run the graph through elkjs via npx. Returns laid-out graph dict."""
    # Write a temp runner so we can import elkjs cleanly
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(ELK_RUNNER_JS)
        runner = f.name
    try:
        proc = subprocess.run(
            ["npx", "--yes", "elkjs", "node", runner],
            input=json.dumps(graph),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise RuntimeError("`npx` not found. Install Node.js (https://nodejs.org) or use --engine dot.")
    finally:
        try:
            os.unlink(runner)
        except OSError:
            pass

    # The above invocation actually requires elkjs as a dep — easier path:
    # try a direct one-liner node call that imports elkjs from the npx cache.
    if proc.returncode != 0:
        # Fallback: spawn `npx -y -p elkjs node -e "..."` form
        node_inline = (
            "const ELK=require('elkjs'); const e=new ELK(); "
            "let s=''; process.stdin.on('data',d=>s+=d); "
            "process.stdin.on('end',async()=>{const o=await e.layout(JSON.parse(s));"
            "process.stdout.write(JSON.stringify(o));});"
        )
        proc = subprocess.run(
            ["npx", "-y", "-p", "elkjs", "node", "-e", node_inline],
            input=json.dumps(graph),
            capture_output=True,
            text=True,
            timeout=180,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"elkjs failed:\n{proc.stderr}")
    return json.loads(proc.stdout)


def run_dot(graph):
    """Fallback: Graphviz dot. Produces less polished output, no nested containers."""
    # Flatten container tree into a single layer (dot doesn't handle compound graphs well)
    def all_nodes(n, out):
        for ch in n.get("children", []) or []:
            all_nodes(ch, out)
        out.append(n)

    nodes = []
    for n in graph["children"]:
        all_nodes(n, nodes)

    dot = ["digraph G {", '  rankdir="LR";', '  node [shape=box, fixedsize=true];']
    for n in nodes:
        if "children" in n:
            continue  # skip containers in flattened pass
        dot.append(f'  "{n["id"]}" [width={n["width"] / 72:.2f}, height={n["height"] / 72:.2f}];')
    for e in graph["edges"]:
        dot.append(f'  "{e["sources"][0]}" -> "{e["targets"][0]}";')
    dot.append("}")
    try:
        proc = subprocess.run(
            ["dot", "-Tjson0"],
            input="\n".join(dot),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        raise RuntimeError("`dot` (Graphviz) not found. `brew install graphviz` or use --engine elk.")
    if proc.returncode != 0:
        raise RuntimeError(f"Graphviz dot failed:\n{proc.stderr}")
    return _dot_json_to_elk(json.loads(proc.stdout), graph)


def _dot_json_to_elk(dot_out, original_graph):
    """Convert Graphviz -Tjson0 output back into ELK-shaped layout dict (id -> x,y,w,h)."""
    # Graphviz coords are bottom-left origin; flip y
    objects = dot_out.get("objects", [])
    bb = dot_out.get("bb", "0,0,800,600").split(",")
    canvas_h = float(bb[3]) - float(bb[1])
    laid = {"id": "root", "children": [], "edges": original_graph["edges"]}
    for obj in objects:
        if "name" not in obj or "pos" not in obj:
            continue
        cx, cy = obj["pos"].split(",")
        cx, cy = float(cx), float(cy)
        w = float(obj.get("width", 1)) * 72
        h = float(obj.get("height", 1)) * 72
        x = cx - w / 2.0
        y = canvas_h - cy - h / 2.0
        laid["children"].append({"id": obj["name"], "x": x, "y": y, "width": w, "height": h})
    return laid


# ============================================================ rewrite .drawio


def apply_layout(drawio_root, laid_graph, by_id, parents):
    """Write x/y/w/h from laid_graph back into the mxGraphModel cells.

    ELK output is hierarchical: each node's x/y is relative to its parent (matches mxGraph convention).
    """
    def walk(node):
        cid = node["id"]
        if cid in by_id:
            cell = by_id[cid]
            g = cell.find("mxGeometry")
            if g is not None:
                if "x" in node:
                    g.set("x", f"{node['x']:.0f}")
                if "y" in node:
                    g.set("y", f"{node['y']:.0f}")
                if "width" in node:
                    g.set("width", f"{node['width']:.0f}")
                if "height" in node:
                    g.set("height", f"{node['height']:.0f}")
        for ch in node.get("children", []) or []:
            walk(ch)

    for n in laid_graph.get("children", []):
        walk(n)


# ============================================================ main


def main():
    ap = argparse.ArgumentParser(description="ELK / Graphviz auto-layout for .drawio files")
    ap.add_argument("input", help="Source .drawio file")
    ap.add_argument("output", nargs="?", help="Output path (default: <input>.laid-out.drawio)")
    ap.add_argument("--engine", choices=["elk", "dot", "auto"], default="auto")
    ap.add_argument("--direction", choices=["RIGHT", "DOWN", "LEFT", "UP"], default="RIGHT")
    ap.add_argument(
        "--auto-threshold",
        type=int,
        default=20,
        help="auto_layout=auto runs ELK when vertex count exceeds this (default: 20)",
    )
    ap.add_argument(
        "--features",
        default="",
        help="Feature overrides: 'auto_layout=elk', 'auto_layout=dot', 'auto_layout=auto', or 'auto_layout=off'",
    )
    args = ap.parse_args()

    # Parse --features overrides
    feats = {"auto_layout": args.engine}
    for part in args.features.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            feats[k.strip()] = v.strip()

    if feats.get("auto_layout") == "off":
        print("auto_layout=off — no-op.")
        sys.exit(0)
    engine = feats.get("auto_layout", "auto")

    tree = ET.parse(args.input)
    root = tree.getroot()
    graph, by_id, parents = build_elk_graph(root, direction=args.direction)
    if graph is None:
        print(f"No cells found in {args.input}")
        sys.exit(1)

    # Count vertices for `auto` mode decision
    def _count(node):
        n = 1
        for ch in node.get("children", []) or []:
            n += _count(ch)
        return n
    n_vertices = sum(_count(n) for n in graph["children"])

    # Patterns where auto-layout damages the semantic layout — opt out by name
    SKIP_PATTERNS = ("sequence", "grid", "matrix", "bpmn", "swim")

    if engine == "auto":
        # Detect pattern from <diagram name="..."> attribute
        diagram_name = ""
        for d in root.iter("diagram"):
            diagram_name = (d.get("name") or "").lower()
            break
        if any(p in diagram_name for p in SKIP_PATTERNS):
            print(f"auto_layout=auto: pattern '{diagram_name}' is positional — skipping (use --features auto_layout=elk to force)")
            sys.exit(0)
        if n_vertices > args.auto_threshold:
            engine = "elk"
            print(f"auto_layout=auto: {n_vertices} vertices > {args.auto_threshold} threshold → running ELK")
        else:
            print(f"auto_layout=auto: {n_vertices} vertices ≤ {args.auto_threshold} threshold → skipping (LLM coords retained)")
            sys.exit(0)

    print(f"Built graph: {len(graph['children'])} top-level nodes, {n_vertices} total vertices, {len(graph['edges'])} edges")
    print(f"Running engine={engine} direction={args.direction}...")

    if engine == "elk":
        laid = run_elk(graph)
    elif engine == "dot":
        laid = run_dot(graph)
    else:
        print(f"Unknown engine: {engine}")
        sys.exit(1)

    apply_layout(root, laid, by_id, parents)

    out_path = args.output or (os.path.splitext(args.input)[0] + ".laid-out.drawio")
    tree.write(out_path, encoding="utf-8", xml_declaration=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
