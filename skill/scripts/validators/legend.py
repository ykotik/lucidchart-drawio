"""
validators/legend.py — W122 legend presence check.

W122  Diagram has <n> edge types / <m> vendor namespaces — add a legend.

Trigger condition (either is sufficient):
  - Distinct edge semantic types >= 2
  - Distinct vendor namespaces >= 3

Edge semantic type is derived from (dashed, strokeColor, endArrow) tuple.
Vendor namespaces counted from shape= prefix: mxgraph.aws4., mxgraph.azure2., mxgraph.gcp2.

Legend detection heuristic: a cell whose id contains "legend" (case-insensitive)
or whose value matches "legend" (case-insensitive), with swimlane or container=1 style.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .base import Diagnostic, WRN, Validator

_VENDOR_PREFIXES = ("mxgraph.aws4.", "mxgraph.azure2.", "mxgraph.gcp2.")


def _edge_semantic(style: dict) -> tuple:
    """Return a hashable key representing an edge's visual semantics."""
    return (
        style.get("dashed", "0"),
        (style.get("strokeColor") or "").lower(),
        (style.get("endArrow") or "block").lower(),
    )


def _vendor_namespace(style: dict) -> str | None:
    """Return the vendor namespace prefix if this shape uses one, else None."""
    shape = style.get("shape", "")
    for prefix in _VENDOR_PREFIXES:
        if shape.startswith(prefix):
            return prefix
    return None


def _has_legend(by_id: dict, styles: dict) -> bool:
    """Return True if any container cell looks like a legend."""
    for cid, cell in by_id.items():
        # id check
        if "legend" in cid.lower():
            return True
        # value check
        val = (cell.get("value") or "").strip()
        if val.lower() == "legend":
            st = styles.get(cid, {})
            if "swimlane" in st or st.get("container") == "1":
                return True
    return False


class LegendValidator(Validator):
    """
    W122  legend missing on diagram with multiple edge types or vendor namespaces.
    """

    codes = ("W122",)

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        by_id = ctx["by_id"]
        is_edge = ctx["is_edge"]
        is_vertex = ctx["is_vertex"]
        styles = ctx["styles"]
        result: list[Diagnostic] = []

        # --- count distinct edge semantic types ---
        edge_semantics: set[tuple] = set()
        for cid in by_id:
            if is_edge[cid]:
                st = styles.get(cid, {})
                edge_semantics.add(_edge_semantic(st))
        n_edge_types = len(edge_semantics)

        # --- count distinct vendor namespaces ---
        vendor_ns: set[str] = set()
        for cid in by_id:
            if is_vertex[cid]:
                st = styles.get(cid, {})
                ns = _vendor_namespace(st)
                if ns:
                    vendor_ns.add(ns)
        n_vendors = len(vendor_ns)

        # --- check trigger ---
        needs_legend = n_edge_types >= 2 or n_vendors >= 3
        if not needs_legend:
            return result

        # --- check presence ---
        if not _has_legend(by_id, styles):
            result.append(Diagnostic(
                "W122", WRN,
                f"Diagram has {n_edge_types} edge type(s) / {n_vendors} vendor "
                f"namespace(s) — add a legend container (see references/legend.md). "
                f"Legend id must contain 'legend' (case-insensitive).",
            ))

        return result
