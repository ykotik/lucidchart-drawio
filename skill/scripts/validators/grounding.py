"""
validators/grounding.py — G5xx grounding-manifest checks (F3).

Feature flag: grounding_manifest. Disable with --features grounding_manifest=off.

G500  WARN  could not read plan file (emitted by CLI shim before check runs)
G501  ERROR element has no 'cite' field
G502  WARN  element cite starts with 'assumption:'
G503  INFO  coverage summary

Note: this validator operates on the plan JSON, not on an mxGraphModel.
The ``check()`` method therefore ignores the ``model`` argument and reads
``ctx["_gt_plan"]`` instead.  The CLI shim passes the plan via the features
dict (key ``_gt_plan``) exactly as the original validate.py did.
"""

from __future__ import annotations

from .base import Diagnostic, ERR, WRN, INF, Validator


class GroundingValidator(Validator):
    """F3 grounding manifest checks."""

    codes = ("G500", "G501", "G502", "G503")

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        features = ctx["features"]
        if features.get("grounding_manifest", "on") != "on":
            return []

        plan = features.get("_gt_plan")
        if not plan:
            return []

        result: list[Diagnostic] = []
        n_cited = 0
        n_assumptions = 0
        n_missing = 0

        for kind in ("containers", "shapes", "edges"):
            for el in plan.get(kind, []) or []:
                eid = el.get("id", "<no-id>")
                cite = (el.get("cite") or "").strip()
                if not cite:
                    result.append(Diagnostic("G501", ERR,
                        f"{kind[:-1]} '{eid}' has no 'cite' field (grounding required)",
                        element_id=eid))
                    n_missing += 1
                    continue
                n_cited += 1
                if cite.startswith("assumption:"):
                    result.append(Diagnostic("G502", WRN,
                        f"{kind[:-1]} '{eid}' is an assumption: {cite[11:].strip()}",
                        element_id=eid))
                    n_assumptions += 1

        total = n_cited + n_missing
        if total:
            result.append(Diagnostic("G503", INF,
                f"Grounding: {n_cited}/{total} cited, {n_assumptions} assumptions, "
                f"{n_missing} missing"))

        return result
