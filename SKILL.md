---
name: lucidchart-drawio
description: >
  Generate Lucidchart-importable architecture diagrams as draw.io XML (.drawio files).
  Use when asked to create, restyle, or produce diagrams for Lucidchart in any of these
  layout patterns: hub-radial (hub-spoke), scope-columns (CIAM dual-scope), horizontal
  swimlanes (trust/cadence bands), LR data pipeline (streaming/event-driven), or
  tenant-namespace (nested Kafka/Flink tenant containers). Outputs valid mxGraph XML
  that can be imported directly into Lucidchart via File → Import → draw.io.
  Triggers: "drawio", "lucidchart diagram", "architecture diagram", "drawio xml",
  "create diagram", ".drawio", "C4 diagram", "swimlane diagram", "pipeline diagram",
  "streaming architecture diagram", "import into lucidchart".
---

# Lucidchart draw.io Diagram Skill

## Output requirement

Always produce a `.drawio` file saved to the user's workspace. Never inline XML in chat.
File naming: `NN_DiagramName/V_layout-name.drawio` (e.g. `01_System_Context/A_top_down_hub.drawio`).

## Workflow

1. **Identify layout pattern** → pick from the 5 patterns below
2. **Read the relevant template** from `templates/` as a starting skeleton
3. **Read style-dictionary.md** for color/style constants
4. **Read gestalt-rules.md** for spacing and quality rules
5. **Apply content** — replace placeholder labels, add/remove shapes, wire edges
6. **Write file** to workspace using Write tool
7. **Verify** — check: every edge has `<mxGeometry relative="1" as="geometry"/>`, all IDs unique, containers use `parent=` correctly, no XML comments

## Layout pattern selection

| Pattern | When to use | Template file |
|---|---|---|
| **hub-radial** | One central system with spokes to satellite systems | `templates/hub-radial.drawio` |
| **scope-columns** | Two boundary scopes (internal vs external/vendor) side by side | `templates/scope-columns.drawio` |
| **swimlanes** | Horizontal bands by trust zone, cadence, or tenant | `templates/swimlanes.drawio` |
| **pipeline** | Left-to-right data flow: sources → processing → consumers | `templates/pipeline.drawio` |
| **tenant-namespace** | Nested containers per tenant/namespace (Kafka, multi-cloud) | `templates/tenant-namespace.drawio` |

## Critical XML rules (memorize)

- Every edge `mxCell` **must** have `<mxGeometry relative="1" as="geometry"/>` child — never self-close edges
- Children inside containers use **relative coordinates** (offset from container top-left)
- Container cells need `swimlane` style **or** `container=1;pointerEvents=0;` on any shape
- Always add `pointerEvents=0;` to containers that should not capture child connections
- No XML comments (`<!-- -->`): forbidden in output
- Escape: `&amp;` `&lt;` `&gt;` `&quot;` in attribute values
- All `id` values must be unique across the diagram

## Scope container styles (CIAM-inspired)

```
Green (FMI internal):  swimlane;startSize=26;dashed=1;strokeColor=#2E7D32;strokeWidth=2;fillColor=none;fontColor=#2E7D32;fontSize=12;fontStyle=1;
Black (vendor/external): swimlane;startSize=26;dashed=1;strokeColor=#424242;strokeWidth=1.5;fillColor=none;fontColor=#424242;fontSize=12;fontStyle=1;
```

## Reference files

- **xml-schema.md** — full mxGraph attribute reference, geometry, layers, tags, edge routing
- **style-dictionary.md** — component palettes, scope styles, edge styles, legend snippets
- **layout-patterns.md** — skeleton XML + coordinate guide for each of the 5 patterns
- **gestalt-rules.md** — 10 design rules (flow, spacing, connectors, typography, density)

Read a reference file when you need details beyond what's in this SKILL.md.
