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
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

# ---------------------------------------------------------------- package path
# Allow running validate.py directly without installing the package.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from validators import REGISTRY, run_all, load_plugin
from validators.base import Diag, Diagnostic, ERR, WRN, INF


# ---------------------------------------------------------------- parsing
def load(path: str):
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
    for m in root.iter("mxGraphModel"):
        yield m


def iter_cells(model):
    for r in model.iter("root"):
        for c in r.findall("mxCell"):
            yield c
        for c in r.findall("object"):
            inner = c.find("mxCell")
            if inner is not None:
                inner.set("id", c.get("id", inner.get("id", "")))
                yield inner


# ---------------------------------------------------------------- geometry
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
    s = cell.get("style", "") or ""
    kv = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
        elif part.strip():
            kv[part.strip()] = "1"
    return kv


def _build_ctx(model, features: dict) -> dict:
    """Build the shared context dict consumed by all validators."""
    cells = list(iter_cells(model))
    by_id: dict = {}
    parents: dict = {}
    is_vertex: dict = {}
    is_edge: dict = {}
    geoms: dict = {}
    styles: dict = {}

    for c in cells:
        cid = c.get("id")
        if cid is None:
            continue
        if cid in by_id:
            # E001 duplicate — record but don't overwrite so other checks stay valid
            pass
        else:
            by_id[cid] = c
        parents[cid] = c.get("parent")
        is_vertex[cid] = c.get("vertex") == "1"
        is_edge[cid] = c.get("edge") == "1"
        geoms[cid] = geom_of(c)
        styles[cid] = style_kv(c)

    return {
        "features":  features,
        "cells":     cells,
        "by_id":     by_id,
        "parents":   parents,
        "is_vertex": is_vertex,
        "is_edge":   is_edge,
        "geoms":     geoms,
        "styles":    styles,
    }


def _detect_duplicates(cells, diag: Diag) -> None:
    """E001: duplicate id — must run before _build_ctx drops duplicates."""
    seen: set = set()
    for c in cells:
        cid = c.get("id")
        if cid is None:
            continue
        if cid in seen:
            diag.err("E001", f"Duplicate id '{cid}'")
        else:
            seen.add(cid)


# ---------------------------------------------------------------- comment scan (E006)
def scan_comments(path: str, diag: Diag) -> None:
    try:
        with open(path) as f:
            content = f.read()
    except OSError:
        return
    start = content.find("<mxGraphModel")
    if start == -1:
        return
    end = content.find("</mxGraphModel>", start)
    if end == -1:
        return
    inner = content[start:end]
    if "<!--" in inner:
        diag.warn("E006",
            "XML comment found inside <mxGraphModel> — remove for Lucidchart compatibility")


# ---------------------------------------------------------------- feature helpers
DEFAULT_FEATURES = {
    "quality_gate": "on",
    "grounding_manifest": "on",
    "text_metrics": "auto",
}


def parse_features(spec: str, defaults=None) -> dict:
    out = dict(defaults or DEFAULT_FEATURES)
    if not spec:
        return out
    for part in spec.split(","):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _auto_plan_path(drawio_path: str):
    base, _ = os.path.splitext(drawio_path)
    candidate = base + ".plan.json"
    return candidate if os.path.isfile(candidate) else None


def _auto_annotated_plan_path(drawio_path: str):
    base, _ = os.path.splitext(drawio_path)
    candidate = base + ".annotated.plan.json"
    return candidate if os.path.isfile(candidate) else None


def _collect_cells(root):
    """Page-keyed dicts for T8 text-metrics multi-page traversal."""
    by_id_map: dict = {}
    geoms_map: dict = {}
    styles_map: dict = {}
    for i, model in enumerate(root.iter("mxGraphModel")):
        key = str(i)
        by_id: dict = {}
        geoms: dict = {}
        styles: dict = {}
        for c in iter_cells(model):
            cid = c.get("id")
            if not cid:
                continue
            by_id[cid] = c
            geoms[cid] = geom_of(c)
            styles[cid] = style_kv(c)
        by_id_map[key] = by_id
        geoms_map[key]  = geoms
        styles_map[key] = styles
    return by_id_map, geoms_map, styles_map


# ---------------------------------------------------------------- main
def main() -> None:
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
    ap.add_argument(
        "--validator-plugin",
        default=None,
        dest="validator_plugin",
        metavar="PATH",
        help="Path to a Python plugin file that registers additional Validator subclasses",
    )
    args = ap.parse_args()

    # Load plugin (before any validation)
    if args.validator_plugin:
        try:
            load_plugin(args.validator_plugin)
        except Exception as e:
            print(f"{ERR} Could not load validator plugin {args.validator_plugin!r}: {e}")
            sys.exit(2)

    features = parse_features(args.features)

    # Load plan (F3 grounding)
    import json
    plan_path = args.plan or _auto_plan_path(args.file)
    plan = None
    if plan_path:
        try:
            with open(plan_path) as f:
                plan = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARN  G500: Could not read plan {plan_path}: {e}")
    features["_gt_plan"] = plan

    # Load annotated plan (T8 text metrics)
    annotated_plan_path = args.annotated_plan or _auto_annotated_plan_path(args.file)
    annotated_plan = None
    if annotated_plan_path:
        try:
            with open(annotated_plan_path) as f:
                annotated_plan = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARN  T800: Could not read annotated plan {annotated_plan_path}: {e}")

    root = load(args.file)
    diag = Diag()
    scan_comments(args.file, diag)

    # Pre-collect multi-page cell data for T8 (done once, shared across pages)
    by_id_map, geoms_map, styles_map = _collect_cells(root)

    for model in all_models(root):
        # Detect duplicates before building ctx (which silently dedupes)
        _detect_duplicates(list(iter_cells(model)), diag)

        ctx = _build_ctx(model, features)

        # Attach T8 multi-page context
        ctx["_annotated_plan"] = annotated_plan
        ctx["_by_id_map"]      = by_id_map
        ctx["_geoms_map"]      = geoms_map
        ctx["_styles_map"]     = styles_map

        for d in run_all(model, ctx):
            diag.add(d)

    sys.exit(diag.print(args.mode))


if __name__ == "__main__":
    main()
