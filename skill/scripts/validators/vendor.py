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
