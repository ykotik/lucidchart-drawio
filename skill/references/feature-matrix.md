# Feature Flags & Compatibility Matrix

Reference for all feature flags accepted by `validate.py --features` and the
`<!-- lucid:key=value -->` comment syntax in `.drawio` source plans.

---

## Flag Reference

### `output_mode`
**Allowed:** `bare` | `wrapped` | `auto` (default: `auto`)

Controls the XML envelope of emitted diagrams.
- `bare` — raw `<mxGraphModel>` fragment; recommended for single-page AI generation.
- `wrapped` — full `<mxfile><diagram>…</diagram></mxfile>`; required for multi-page.
- `auto` — bare when plan has one page, wrapped otherwise.

### `quality_gate`
**Allowed:** `on` | `off` (default: `on`)

Enables Q4xx quality-metric checks (edge crossings, orthogonality %, edge-length
variance, area utilization).  Also activates D6xx DiagramEval F1 scoring when a
ground-truth plan is present.

### `grounding_manifest`
**Allowed:** `on` | `off` (default: `on`)

Every node and edge in the plan must carry a non-empty `source` field
(`file:line`, `doc:section`, `user-stated`, or `assumption:…`).
Validator emits G5xx for violations.

### `auto_layout`
**Allowed:** `off` | `elk` | `dot` | `neato` | `auto` (default: `auto`)

Replaces LLM-emitted coordinates with ELK Layered or Graphviz output.
- `elk` — ELK Layered (preferred; handles large graphs well).
- `dot` — Graphviz hierarchical layout.
- `neato` — Graphviz spring/force-directed; best for overlap removal only.
- `auto` — runs ELK when diagram has > 20 vertices; LLM coords otherwise.
- `off` — use LLM-emitted coordinates as-is.

### `text_metrics`
**Allowed:** `off` | `auto` (default: `auto`)

Runs `scripts/text-metrics.js` between plan validation and XML emit.
Annotates each shape with `text_safe.{min_width, min_height, overflow}`.
Emits W106/W107/W108 if emitted XML geometry is smaller than safe dims.

### `font_fit`
**Allowed:** `off` | `auto` | `grow` (default: `auto`)

Post-processor applied after XML emit.
- `auto` — shrinks `fontSize` only when label overflows its cell.
- `grow` — also enlarges cells that have headroom (useful after ELK layout).
  **Requires `auto_layout` in {elk, neato, dot}** — see F001.
  **Requires `text_metrics != off`** — see F005.
- `off` — skip font post-processing entirely.

### `edge_routing`
**Allowed:** `off` | `script` | `auto` (default: `auto`)

Two-layer edge routing (F7 feature).
- `auto` — activates obstacle-push waypoint insertion when diagram has > 15 edges.
- `script` — always runs `scripts/route-edges.py` after ELK (zero extra LLM tokens).
  Most effective when `auto_layout != off` — see F002.
- `off` — disable edge routing entirely.

---

## Compatibility Matrix

Rows = flag being set. Columns = flags it interacts with.
Cell content: constraint type and F-code.

| Flag set to …          | `auto_layout`              | `text_metrics`         | `quality_gate`         | `grounding_manifest`   |
|------------------------|----------------------------|------------------------|------------------------|------------------------|
| `font_fit=grow`        | **requires elk/neato/dot** (F001 ERROR) | **requires != off** (F005 ERROR) | — | — |
| `font_fit=auto`        | —                          | **warn if off** (F005 WARN) | — | — |
| `edge_routing=script`  | **warn if off** (F002 WARN) | —                     | — | — |
| `grounding_manifest=off` | —                        | —                      | **warn if on** (F004 WARN) | — |

---

## Valid Combinations (examples)

```
# Dense graph: ELK layout + font grow + metrics — all consistent
--features auto_layout=elk,font_fit=grow,text_metrics=auto,quality_gate=on

# Fast draft: skip layout and font processing
--features auto_layout=off,font_fit=off,text_metrics=off,quality_gate=off

# Script-only edge routing after ELK
--features auto_layout=elk,edge_routing=script

# Multi-page wrapped output, grounding off for prototyping
--features output_mode=wrapped,grounding_manifest=off,quality_gate=off
```

## Invalid Combinations and Expected F-codes

```
# F001 ERROR: grow needs ELK/neato/dot
--features font_fit=grow,auto_layout=off

# F001 ERROR: grow needs ELK/neato/dot (auto_layout unset defaults to auto — auto is OK)
# NOTE: auto_layout=auto is accepted by F001 because it MAY run ELK.
# Explicitly setting auto_layout=off is what triggers F001.

# F005 ERROR: grow needs text metrics
--features font_fit=grow,text_metrics=off,auto_layout=elk

# F005 WARN: auto font_fit without metrics is imprecise
--features font_fit=auto,text_metrics=off

# F002 WARN: script routing without layout produces unreliable results
--features edge_routing=script,auto_layout=off

# F004 WARN: quality gate checks grounding coverage but manifest is off
--features grounding_manifest=off,quality_gate=on

# F003 WARN: typo in flag name
--features font_ffit=auto

# F006 ERROR: bad output_mode value
--features output_mode=inline

# F007 ERROR: bad auto_layout value
--features auto_layout=graphviz
```

---

## Override Syntax (in-diagram)

Add as the first comment line of the source plan:

```
<!-- lucid:auto_layout=elk lucid:font_fit=grow -->
```

Each `lucid:key=value` token is parsed as a feature override.
The validator reads these from the `.drawio` file comments.
