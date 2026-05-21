"""
validators/text_checks.py — T8xx text-metrics checks.

Feature flag: text_metrics. Disable with --features text_metrics=off.

Reads an annotated plan JSON produced by scripts/text-metrics.js and verifies
that every shape/container's mxGeometry is at least as large as the safe
dimensions computed from label measurement.

W106  WARN  node width  < text_safe.min_width
W107  WARN  node height < text_safe.min_height
W108  WARN  swimlane startSize < text_safe.min_startSize
T801  INFO  summary

Note: this validator needs cell data across ALL pages, not just the single
mxGraphModel passed to check().  The CLI shim therefore passes extra state
via ctx keys:
    ``_by_id_map``    — {page_key: by_id}
    ``_geoms_map``    — {page_key: geoms}
    ``_styles_map``   — {page_key: styles}
    ``_annotated_plan`` — loaded plan dict (or None)
"""

from __future__ import annotations

from .base import Diagnostic, WRN, INF, Validator


class TextMetricsValidator(Validator):
    """T8xx text-metrics cross-check."""

    codes = ("W106", "W107", "W108", "T801")

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        features = ctx["features"]
        if features.get("text_metrics", "auto") == "off":
            return []

        annotated_plan = ctx.get("_annotated_plan")
        if not annotated_plan:
            return []

        by_id_map  = ctx.get("_by_id_map", {})
        geoms_map  = ctx.get("_geoms_map", {})
        styles_map = ctx.get("_styles_map", {})

        result: list[Diagnostic] = []
        n_checked = 0
        n_overflow = 0

        # Flatten all shapes + containers into id→element map
        plan_elements: dict[str, dict] = {}
        for kind in ("shapes", "containers"):
            for el in annotated_plan.get(kind, []) or []:
                eid = el.get("id")
                if eid:
                    plan_elements[eid] = el

        for page_key, by_id in by_id_map.items():
            geoms  = geoms_map[page_key]
            styles = styles_map[page_key]

            for cid, cell in by_id.items():
                el = plan_elements.get(cid)
                if not el:
                    continue
                ts = el.get("text_safe")
                if not ts:
                    continue

                n_checked += 1
                g = geoms.get(cid)
                if g is None:
                    continue
                x, y, w, h = g
                st = styles.get(cid, {})

                # W106 width overflow
                min_w = ts.get("min_width")
                if min_w is not None and w < min_w - 1:
                    n_overflow += 1
                    result.append(Diagnostic("W106", WRN,
                        f"Node '{cid}' width={w:.0f}px < text_safe.min_width={min_w}px "
                        f"— label may overflow horizontally", element_id=cid))

                # W107 height overflow
                min_h = ts.get("min_height")
                if min_h is not None and h < min_h - 1:
                    n_overflow += 1
                    result.append(Diagnostic("W107", WRN,
                        f"Node '{cid}' height={h:.0f}px < text_safe.min_height={min_h}px "
                        f"— label may clip vertically", element_id=cid))

                # W108 swimlane header overflow
                min_ss = ts.get("min_startSize")
                if min_ss is not None and "swimlane" in (cell.get("style") or ""):
                    declared_ss = float(st.get("startSize", 26))
                    if declared_ss < min_ss - 1:
                        n_overflow += 1
                        result.append(Diagnostic("W108", WRN,
                            f"Container '{cid}' startSize={declared_ss:.0f}px < "
                            f"text_safe.min_startSize={min_ss}px — header clips label",
                            element_id=cid))

        if n_checked > 0:
            result.append(Diagnostic("T801", INF,
                f"Text metrics: {n_checked} elements checked, {n_overflow} overflow(s) found"))

        return result
