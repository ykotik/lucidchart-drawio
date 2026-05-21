"""
validators/features.py — F0xx feature-flag compatibility validator.

Validates that the combination of --features flags passed to validate.py
is internally consistent.  Rules are encoded as data (RULES list) so
new constraints can be added without touching control flow.

F001  font_fit=grow requires auto_layout in {elk, neato, dot}
F002  edge_routing=script requires auto_layout != off
       (route-edges.py runs after ELK; off means raw LLM coords, routing pointless)
F003  unknown feature flag key
F004  grounding_manifest=off conflicts with quality_gate=on
       (quality gate checks grounding coverage; disabling manifest silently voids it)
F005  text_metrics=off with font_fit != off
       (font_fit post-processor needs text-metric annotations to be meaningful)
F006  output_mode value must be one of {bare, wrapped, auto}
F007  auto_layout value must be one of {off, elk, dot, neato, auto}
"""

from __future__ import annotations

from .base import Diagnostic, ERR, WRN, INF, Validator


# ---------------------------------------------------------------- known flags

KNOWN_FLAGS: frozenset[str] = frozenset({
    "output_mode",
    "quality_gate",
    "grounding_manifest",
    "auto_layout",
    "text_metrics",
    "font_fit",
    "edge_routing",
})

# Private keys injected by validate.py — not user-facing, never flag as unknown.
_INTERNAL_PREFIXES: tuple[str, ...] = ("_",)

# ---------------------------------------------------------------- allowed values

ALLOWED_VALUES: dict[str, frozenset[str]] = {
    "output_mode":        frozenset({"bare", "wrapped", "auto"}),
    "quality_gate":       frozenset({"on", "off"}),
    "grounding_manifest": frozenset({"on", "off"}),
    "auto_layout":        frozenset({"off", "elk", "dot", "neato", "auto"}),
    "text_metrics":       frozenset({"off", "auto"}),
    "font_fit":           frozenset({"off", "auto", "grow"}),
    "edge_routing":       frozenset({"off", "script", "auto"}),
}

# ---------------------------------------------------------------- compatibility rules
#
# Each rule dict has:
#   "if"          — {flag: value} that triggers the check
#   "requires_any"— {flag: [allowed_values]}  (at least one flag must match)
#   OR
#   "conflicts"   — {flag: [disallowed_values]}  (none of these may be set)
#   "code"        — F-code to emit
#   "severity"    — ERR | WRN | INF  (default ERR)
#   "message"     — human-readable explanation (may use {flag} {value} placeholders)

RULES: list[dict] = [
    {
        "if": {"font_fit": "grow"},
        "requires_any": {"auto_layout": ["elk", "neato", "dot"]},
        "code": "F001",
        "severity": ERR,
        "message": (
            "font_fit=grow requires auto_layout in {elk, neato, dot}; "
            "grow mode enlarges cells whose coords come from ELK/Graphviz — "
            "LLM-emitted coords have no headroom guarantee."
        ),
    },
    {
        "if": {"edge_routing": "script"},
        "requires_any": {"auto_layout": ["elk", "neato", "dot", "auto"]},
        "code": "F002",
        "severity": WRN,
        "message": (
            "edge_routing=script is most effective after auto_layout; "
            "with auto_layout=off the LLM-emitted coords may already overlap shapes, "
            "making obstacle-push waypoints unreliable."
        ),
    },
    {
        "if": {"grounding_manifest": "off"},
        "conflicts": {"quality_gate": ["on"]},
        "code": "F004",
        "severity": WRN,
        "message": (
            "grounding_manifest=off with quality_gate=on: "
            "the quality gate checks grounding coverage (D6xx) but the manifest is "
            "disabled, so those checks will always produce zero-coverage scores."
        ),
    },
    {
        "if": {"font_fit": "auto"},
        "conflicts": {"text_metrics": ["off"]},
        "code": "F005",
        "severity": WRN,
        "message": (
            "font_fit=auto with text_metrics=off: "
            "font_fit uses text-metric annotations produced by text_metrics; "
            "without them the post-processor operates blind and may mis-shrink fonts."
        ),
    },
    {
        "if": {"font_fit": "grow"},
        "conflicts": {"text_metrics": ["off"]},
        "code": "F005",
        "severity": ERR,
        "message": (
            "font_fit=grow with text_metrics=off: "
            "grow mode requires per-cell overflow annotations from text_metrics; "
            "disabling text_metrics makes font_fit=grow produce incorrect results."
        ),
    },
]


# ---------------------------------------------------------------- validator


class FeatureFlagValidator(Validator):
    """Validate feature-flag combinations for internal consistency."""

    codes = ("F001", "F002", "F003", "F004", "F005", "F006", "F007")

    def check(self, model, ctx: dict) -> list[Diagnostic]:  # noqa: ARG002
        features: dict[str, str] = ctx.get("features", {})
        diags: list[Diagnostic] = []

        # F003 — unknown flag keys
        for key in features:
            if key.startswith(_INTERNAL_PREFIXES):
                continue
            if key not in KNOWN_FLAGS:
                diags.append(Diagnostic(
                    severity=WRN,
                    code="F003",
                    message=(
                        f"Unknown feature flag {key!r}. "
                        f"Known flags: {', '.join(sorted(KNOWN_FLAGS))}."
                    ),
                ))

        # F006/F007 — enum value validation
        for flag, allowed in ALLOWED_VALUES.items():
            val = features.get(flag)
            if val is not None and val not in allowed:
                code = "F006" if flag == "output_mode" else "F007" if flag == "auto_layout" else "F003"
                diags.append(Diagnostic(
                    severity=ERR,
                    code=code,
                    message=(
                        f"Feature flag {flag}={val!r} is not a recognised value. "
                        f"Allowed: {{{', '.join(sorted(allowed))}}}."
                    ),
                ))

        # Compatibility rules
        for rule in RULES:
            trigger = rule["if"]
            # Check if trigger condition is met
            if not all(features.get(k) == v for k, v in trigger.items()):
                continue

            code = rule["code"]
            severity = rule.get("severity", ERR)
            message = rule["message"]

            if "requires_any" in rule:
                req = rule["requires_any"]
                satisfied = any(
                    features.get(flag) in vals
                    for flag, vals in req.items()
                )
                if not satisfied:
                    for flag, vals in req.items():
                        actual = features.get(flag, "<unset>")
                        diags.append(Diagnostic(
                            severity=severity,
                            code=code,
                            message=f"{message} (got {flag}={actual!r})",
                        ))

            elif "conflicts" in rule:
                conflicts = rule["conflicts"]
                for flag, bad_vals in conflicts.items():
                    actual = features.get(flag)
                    if actual in bad_vals:
                        diags.append(Diagnostic(
                            severity=severity,
                            code=code,
                            message=f"{message} (got {flag}={actual!r})",
                        ))

        return diags
