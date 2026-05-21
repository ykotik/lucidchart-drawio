# Validator — Pre-Flight Checks for .drawio Files

The validator (`scripts/validate.py`) inspects a `.drawio` XML file and reports
violations of the rules in this skill. Run it on every diagram before delivery.

```bash
python3 scripts/validate.py path/to/diagram.drawio
python3 scripts/validate.py path/to/diagram.drawio --mode strict     # fail on warnings
python3 scripts/validate.py path/to/diagram.drawio --mode loose      # only fail on errors
```

Default mode is `standard` — errors fail, warnings print but exit 0.

---

## What it checks

### Errors (always fail the diagram)

| Check | Message | Why it matters |
|---|---|---|
| `E001` | Duplicate id `<id>` | Random shapes disappear or merge on import |
| `E002` | Edge `<id>` missing `<mxGeometry>` child | Edge missing on Lucidchart import |
| `E003` | Shape `<id>` parent `<parent>` does not exist | Shape rendered at canvas origin |
| `E004` | Edge `<id>` source `<source>` does not exist | Edge dangles / removed on import |
| `E005` | Edge `<id>` target `<target>` does not exist | Same as E004 |
| `E006` | XML comment inside `<mxGraphModel>` | Import may fail in Lucidchart |
| `E007` | Malformed XML (parse error) | Document broken |
| `E008` | Shape `<id>` has `vertex="1"` but no `<mxGeometry>` | Shape has no size; invisible |
| `E009` | Container `<id>` declared with `swimlane` style has no `startSize` | Undefined header offset |

### Warnings (visible quality issues)

| Check | Message | Suggested fix |
|---|---|---|
| `W101` | Shape `<id>` extends beyond parent container bounds | Reduce shape size or move container boundary |
| `W102` | Shape `<id>` overlaps shape `<other>` | Move one shape; check grid plan |
| `W103` | Shape `<id>` overlaps container header (`y < startSize`) | Move shape down to clear header |
| `W104` | Edge `<id>` parent `<parent>` is not the lowest common ancestor of source and target | Set edge parent to LCA — see `container-coords.md` |
| `W105` | Style fragment `<frag>` not in allowlist | Add to vocabulary file or replace with allowlisted style |
| `W106` | Container `<id>` has only 1 child (low-value grouping) | Consider removing the container |
| `W107` | More than 12 shapes at top level (no grouping) | Group into containers — see `gestalt-rules.md` Rule 2 |
| `W108` | Two shapes have the same label `<label>` | Disambiguate labels |
| `W109` | Shape coords look canvas-absolute but parent is a container | Convert to relative coords |
| `W110` | Edge has no entry/exit points and crosses ≥3 other shapes | Force `exitX/entryX` or add waypoints |
| `W120` | Shape `<id>` cites `<vendor>` docs but uses generic style (expected `mxgraph.<vendor-prefix>.*`) | Replace generic style with the correct vendor shape from the vocabulary file (e.g. `shape=mxgraph.aws4.ec2`) — see `shape-vocabulary/aws.md`, `azure.md`, `gcp.md` |
| `W121` | Edge `<id>` missing anchor(s) on dense diagram (edges=N, cross_container=M) — add exitX/exitY/entryX/entryY to style | Add all four anchor attrs to the edge style: `exitX=1;exitY=0.5;entryX=0;entryY=0.5` — triggered when edges≥20 or cross-container edges≥3; skipped for edges to/from containers |
| `W122` | Diagram has N edge type(s) / M vendor namespace(s) — add a legend container (see references/legend.md) | Add a legend container using `_legend-snippet.drawio` template; container `id` must contain `"legend"` (case-insensitive). Triggered when edge semantic types ≥ 2 OR vendor namespaces (aws4/azure2/gcp2) ≥ 3. Edge semantic type = (dashed, strokeColor, endArrow) tuple. |

### Info (nice-to-fix)

| Check | Message |
|---|---|
| `I201` | Diagram has >40 nodes — consider splitting into multiple pages |
| `I202` | (superseded by W122) No legend present on a diagram with >2 edge styles |
| `I203` | Container `<id>` is empty |

### Layout quality metrics (F2 — `quality_gate` feature flag)

Runs only when `features.quality_gate=on` (default). Disable with `--features quality_gate=off`. All Q4xx codes print as INFO (raw value); a WARN also fires when the threshold is exceeded.

| Code | Metric | Warning threshold |
|---|---|---|
| `Q401` | **Edge crossings** — straight-line proxy between source/target shape centers in canvas-absolute coords | `> max(2, edges / 4)` when `edges >= 6` — suggestion: `auto_layout=elk` |
| `Q402` | **Orthogonality conformance %** — edges using `edgeStyle=orthogonalEdgeStyle` | `< 80%` when `edges >= 4`. **Exempt patterns**: `hub-radial`, `sequence` — emits INFO "Skipped (pattern '…' exempt)" instead of WARN. |
| `Q403` | **Edge length CV** — coefficient of variation = std/mean of straight-line edge lengths | `> 1.2` when `edges >= 3` |
| `Q404` | **Area utilization** — sum of node areas / bounding-box area | `< 10%` (spread thin) or `> 65%` (crowded) when `nodes >= 6` |
| `Q405` | **Text overflow** — label exceeds cell bounds at current `fontSize` (char-width estimate, matches `scripts/fit-fonts.py`) | Any overflowing cell — suggestion: run `scripts/fit-fonts.py` |

The edge-crossings check resolves container coords by walking parent chains and applying `startSize` offsets for swimlanes, so child shapes inside containers get correct canvas-absolute coordinates before the sweep.

### Grounding (F3 — `grounding_manifest` feature flag)

Requires a JSON plan alongside the .drawio (`<name>.plan.json`, auto-detected) or passed via `--plan PATH`.

| Code | Severity | Message |
|---|---|---|
| `G500` | WARN | Could not read plan file (path/json error) |
| `G501` | ERROR | Element `<id>` has no `cite` field |
| `G502` | WARN | Element `<id>` is an `assumption:` (review before delivery) |
| `G503` | INFO | Coverage summary — `N cited, M assumptions, K missing` |

See `plan-format.md` "F3: Grounding manifest" for `cite` value formats.

## How the overlap detection works

The validator builds an axis-aligned bounding box (AABB) for each shape in canvas
coordinates (resolving parent chains) and reports any two AABBs that intersect by
more than 4 pixels on each axis.

It does **not** flag intentional overlap (e.g., a label cell intentionally
positioned on top of a container) — only same-tier vertex overlaps.

---

## How the "edge parent is LCA" check works

For each edge:
1. Walk the parent chain from `source` up to canvas root → `ancestors_s` (a set)
2. Walk the parent chain from `target` up to canvas root → `ancestors_t` (a set)
3. The LCA is the deepest container present in both sets
4. If `edge.parent != LCA`, emit W104

---

## How to fix common violations

**E001 duplicate id**: search for the id, rename one of the duplicates. Update any
`source`/`target` references that pointed to the renamed cell.

**E002 missing edge geometry**: change
```xml
<mxCell id="e1" style="..." edge="1" source="a" target="b" parent="1"/>
```
to
```xml
<mxCell id="e1" style="..." edge="1" source="a" target="b" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**E003 missing parent**: the parent was renamed or never defined. Add the container
or fix the shape's `parent` attribute.

**W103 overlap with container header**: container has `startSize=30` but a child sits
at `y=10`. Move the child to `y=40` or larger.

**W104 wrong edge parent**: if source is in `lane_a` and target is in `lane_b`,
both inside `pool`, then `edge.parent` must be `"pool"`.

**W109 canvas-absolute coords inside container**: a shape at canvas `(280, 110)` is
inside a container at canvas `(40, 40)` with `startSize=30`. The shape's `mxGeometry`
should use `x=240 y=40` (relative to the container), not `x=280 y=110`.

---

## Running the validator on every template

The `scripts/validate.py` script should pass `--mode strict` against every template
in `templates/`. The verification step at the end of the v2 build runs this.

---

## Plugin interface

The validator is built on a pluggable framework in `scripts/validators/`.

### Architecture

```
scripts/validators/
  __init__.py    — REGISTRY list, @register_validator / @validates_code decorators, run_all()
  base.py        — Validator ABC, Diagnostic dataclass, Diag accumulator
  structure.py   — E0xx, W1xx, I2xx checks
  quality.py     — Q4xx quality-gate metrics (F2)
  grounding.py   — G5xx grounding manifest (F3)
  text_checks.py — T8xx text-metrics cross-check
```

### Writing a plugin

Create a Python file that imports from `validators` and defines a `Validator` subclass:

```python
# my_custom_checks.py
from validators import register_validator, validates_code
from validators.base import Validator, Diagnostic, WRN

@register_validator
class NoOrphanEdgesValidator(Validator):
    codes = ("X901",)

    def check(self, model, ctx: dict) -> list[Diagnostic]:
        results = []
        for cid, c in ctx["by_id"].items():
            if ctx["is_edge"][cid]:
                if not c.get("source") and not c.get("target"):
                    results.append(Diagnostic(
                        "X901", WRN,
                        f"Edge '{cid}' has neither source nor target",
                        element_id=cid,
                    ))
        return results
```

### Loading a plugin

```bash
python3 scripts/validate.py diagram.drawio --validator-plugin /path/to/my_custom_checks.py
```

### `Validator.check()` context keys

| Key | Type | Description |
|---|---|---|
| `features` | `dict[str, str]` | Feature flags (e.g. `quality_gate`, `grounding_manifest`) |
| `cells` | `list[Element]` | Raw mxCell elements for this page |
| `by_id` | `dict[str, Element]` | id → mxCell (deduped) |
| `parents` | `dict[str, str]` | id → parent id |
| `is_vertex` | `dict[str, bool]` | id → vertex flag |
| `is_edge` | `dict[str, bool]` | id → edge flag |
| `geoms` | `dict[str, tuple]` | id → `(x,y,w,h)` or `None` |
| `styles` | `dict[str, dict]` | id → parsed style key/value dict |
| `_gt_plan` | `dict \| None` | Loaded plan JSON (F3 grounding) |
| `_annotated_plan` | `dict \| None` | Annotated plan from text-metrics.js (T8) |
| `_by_id_map` | `dict[str, dict]` | page-key → by_id (all pages, for T8) |
| `_geoms_map` | `dict[str, dict]` | page-key → geoms (all pages, for T8) |
| `_styles_map` | `dict[str, dict]` | page-key → styles (all pages, for T8) |

### `Diagnostic` fields

```python
@dataclass
class Diagnostic:
    code:       str   # e.g. "E001", "Q401", "X901"
    severity:   str   # ERR | WRN | INF  (from validators.base)
    message:    str
    element_id: str = ""  # id of offending cell (optional)
    location:   str = ""  # page, line, etc. (optional)
```
