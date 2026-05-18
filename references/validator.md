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

### Info (nice-to-fix)

| Check | Message |
|---|---|
| `I201` | Diagram has >40 nodes — consider splitting into multiple pages |
| `I202` | No legend present on a diagram with >2 edge styles |
| `I203` | Container `<id>` is empty |

---

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
