"""
validators/vendor.py — W120 vendor-icon enforcement check.

W120  WARN  Shape cites vendor docs but uses a generic (non-vendor) style.

Feature flag: grounding_manifest (reuses same gate as G5xx — only meaningful
when a plan is present).  Disable with --features grounding_manifest=off.

Detection logic
---------------
The check operates on the plan JSON (``ctx["_gt_plan"]``), not on the mxCell
XML, because the ``cite`` field lives in the plan, not in the .drawio file.

For each shape/container/edge element in the plan:

1. Skip if ``cite`` is absent, empty, ``user-stated``, starts with
   ``assumption:``, or does not look like a URL (no "://").
2. Detect vendor by matching ``cite`` against VENDOR_URL_PATTERNS.
3. If a vendor is detected, check whether the element's ``style`` value
   contains the expected vendor shape prefix (VENDOR_SHAPE_PREFIXES).
4. On mismatch → W120 WARN.

VENDOR_URL_PATTERNS / VENDOR_SHAPE_PREFIXES
-------------------------------------------
Vendor    URL patterns                                          Style prefix
aws       docs.aws.amazon.com, aws.amazon.com/, amazonaws.com  mxgraph.aws4.
azure     docs.microsoft.com/azure, learn.microsoft.com/azure, mxgraph.azure2.
          azure.microsoft.com
gcp       cloud.google.com/docs, cloud.google.com/products     mxgraph.gcp2.
"""

from __future__ import annotations

from .base import Diagnostic, WRN, Validator


# URL substrings that identify a vendor cite
VENDOR_URL_PATTERNS: dict[str, list[str]] = {
    "aws": [
        "docs.aws.amazon.com",
        "aws.amazon.com/",
        "amazonaws.com",
    ],
    "azure": [
        "docs.microsoft.com/azure",
        "learn.microsoft.com/azure",
        "azure.microsoft.com",
    ],
    "gcp": [
        "cloud.google.com/docs",
        "cloud.google.com/products",
    ],
}

# Style prefix expected for each vendor
VENDOR_SHAPE_PREFIXES: dict[str, str] = {
    "aws":   "mxgraph.aws4.",
    "azure": "mxgraph.azure2.",
    "gcp":   "mxgraph.gcp2.",
}


def _detect_vendor(cite: str) -> str | None:
    """Return the vendor name if *cite* matches a known URL pattern, else None."""
    for vendor, patterns in VENDOR_URL_PATTERNS.items():
        if any(pat in cite for pat in patterns):
            return vendor
    return None


class VendorEnforcementValidator(Validator):
    """W120 — vendor-icon enforcement via cite URL inspection."""

    codes = ("W120",)

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        features = ctx["features"]
        # Gate on grounding_manifest feature (plan required for this check)
        if features.get("grounding_manifest", "on") != "on":
            return []

        plan = features.get("_gt_plan")
        if not plan:
            return []

        result: list[Diagnostic] = []

        # Iterate all plan element kinds that can carry vendor shapes
        for kind in ("containers", "shapes", "edges", "lanes"):
            for el in plan.get(kind, []) or []:
                cite = (el.get("cite") or "").strip()

                # Skip non-URL cites
                if not cite or "://" not in cite:
                    continue
                if cite in ("user-stated",) or cite.startswith("assumption:"):
                    continue

                vendor = _detect_vendor(cite)
                if vendor is None:
                    continue

                expected_prefix = VENDOR_SHAPE_PREFIXES[vendor]
                style = (el.get("style") or "").strip()

                if expected_prefix not in style:
                    eid = el.get("id", "<no-id>")
                    result.append(Diagnostic(
                        "W120", WRN,
                        f"Shape '{eid}' cites {vendor} docs but uses generic style "
                        f"(expected {expected_prefix}*)",
                        element_id=eid,
                    ))

        return result


# Per-vendor geometry minimums for icon cells that carry a label
# (label > 12 chars needs a wider cell than the bare icon size)
VENDOR_MIN_DIMS: dict[str, dict[str, int]] = {
    "aws":   {"min_icon_w": 76, "min_icon_h": 76, "min_label_w": 120, "long_label_chars": 12},
    "azure": {"min_icon_w": 64, "min_icon_h": 64, "min_label_w": 120, "long_label_chars": 12},
    "gcp":   {"min_icon_w": 60, "min_icon_h": 60, "min_label_w": 120, "long_label_chars": 12},
}


def _vendor_from_style(style: str) -> str | None:
    """Return vendor name if style references a vendor shape prefix."""
    for vendor, prefix in VENDOR_SHAPE_PREFIXES.items():
        if prefix in style:
            return vendor
    return None


def _strip_html_tags(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s or "")


class VendorLabelWidthValidator(Validator):
    """W123 — vendor icon cell too narrow for its label.

    For any cell whose style references mxgraph.<vendor>.*, if the visible
    label exceeds long_label_chars characters AND the cell width is below
    the per-vendor min_label_w, emit W123. This catches label overflow on
    small vendor icons (e.g. 60×60 GCP icons with "Pub/Sub Ingestion" label).
    """

    codes = ("W123",)

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        result: list[Diagnostic] = []
        for cell in model.iter("mxCell"):
            if cell.get("vertex") != "1":
                continue
            style = cell.get("style") or ""
            vendor = _vendor_from_style(style)
            if vendor is None:
                continue
            dims = VENDOR_MIN_DIMS.get(vendor)
            if dims is None:
                continue
            label = _strip_html_tags(cell.get("value") or "").strip()
            if len(label) <= dims["long_label_chars"]:
                continue
            geom = cell.find("mxGeometry")
            if geom is None:
                continue
            try:
                w = float(geom.get("width", "0") or 0)
            except (TypeError, ValueError):
                continue
            if w < dims["min_label_w"]:
                eid = cell.get("id", "<no-id>")
                result.append(Diagnostic(
                    "W123", WRN,
                    f"Vendor icon '{eid}' ({vendor}) label \"{label[:40]}\" exceeds "
                    f"available width (cell w={w:.0f}, min={dims['min_label_w']})",
                    element_id=eid,
                ))
        return result
