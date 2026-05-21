---
name: drawio-architect
description: >-
  Generate clean draw.io architecture diagrams (.drawio / mxGraph XML) with strict
  layout discipline and clean edge routing. Output opens natively in draw.io and
  imports cleanly into Lucidchart, Confluence drawio plugin, and any mxGraph-aware
  tool. 15 layout patterns: hub-radial,
  scope-columns, swimlanes, LR pipeline, tenant-namespace, C4 context/container/component,
  ERD crow's-foot, UML class, sequence, tree-hierarchy, flowchart-DAG, BPMN, grid-matrix.
  Vendor icon vocabularies for AWS, Azure, GCP, UML, ER, BPMN. Enforces container-relative
  coordinates, two-layer edge rendering, plan-then-emit workflow, pre-flight validation.
  Triggers: drawio, lucidchart diagram, architecture diagram, .drawio, C4 diagram,
  swimlane diagram, pipeline diagram, ERD, class diagram, sequence diagram, BPMN,
  flowchart, org chart, tree diagram, AWS/Azure/GCP architecture, import into lucidchart.
version: 2.1.0
features:
  output_mode: auto          # bare | wrapped | auto  — bare <mxGraphModel> (drawio FAQ) vs full <mxfile>
  quality_gate: on           # on | off              — edge crossings, orthogonality, length variance
  grounding_manifest: on     # on | off              — every node/edge cites a source
  auto_layout: auto          # off | elk | dot | auto — auto = elk when diagram has >20 vertices
  text_metrics: auto         # off | auto            — auto = measure labels, warn on overflow, apply min dims
  font_fit: auto             # off | auto | grow     — auto = shrink fontSize when text overflows cell
  edge_routing: auto         # off | script | auto   — auto = obstacle-push when >15 edges
---

# Lucidchart draw.io Diagram Skill (v2.1)

## Quick start — usage

Pick the prompt closest to what you need, replace the source citations with your real artifacts, paste into Claude. The skill picks the matching template, validates, lays out, fits fonts, and writes a `.drawio` + `.plan.json` pair.

| Prompt | Pattern | Best for |
|---|---|---|
| [1. C4 Container — internal system](references/prompt-examples.md#1-c4-container--internal-payments-platform) | `c4-container` | Multi-tier app: web/mobile/api/worker/db, with named external systems. Grounding cites required. |
| [2. LR streaming pipeline](references/prompt-examples.md#2-lr-streaming-pipeline--clickstream-analytics) | `pipeline` | 20+ shapes, many cross-stage edges — auto_layout=elk pays for itself. |
| [3. BPMN swimlanes — approval flow](references/prompt-examples.md#3-bpmn-swimlanes--purchase-requisition-approval) | `bpmn-process` | Multi-lane process with cross-lane edges + decision gateways. |
| [4. ERD crow's-foot](references/prompt-examples.md#4-erd-crows-foot--multi-tenant-saas-schema) | `erd-crowfoot` | Database schema with PK/FK + crow's-foot cardinality. |
| [5. Multi-tenant Kafka deployment](references/prompt-examples.md#5-multi-tenant-kafka-deployment--tenant-namespace-pattern) | `tenant-namespace` | 3-level nesting (cluster → tenant → namespace), per-tenant sub-containers. |

**Minimum shape of a good prompt:**

```text
Build a <pattern-name> diagram for <subject>.

Containers/lanes (if applicable):
  ...

Shapes (with source citations — required when grounding_manifest=on):
  - <name> — cite: <source.md:§N> or <table.xlsx:row N>
  ...

Edges:
  - <source> → <target> labeled "<protocol/format>"
  ...

Output: <path>/<NN_name>.drawio + matching .plan.json
```

Full examples (~200-word prompts with realistic source maps): see [references/prompt-examples.md](references/prompt-examples.md). The "anti-examples" section there shows what NOT to write.

---

## Feature flags

The skill's behavior is controlled by the `features:` block in the YAML frontmatter above. Override per-diagram with a `<!-- lucid:feature=value -->` comment on the first line of the source plan, or by passing `--features <key>=<value>,...` to `scripts/validate.py` / `scripts/elk-layout.py` where supported. **Each feature can be turned off independently.**

| Flag | Values | Default | What it does |
|---|---|---|---|
| `output_mode` | `bare` / `wrapped` / `auto` | `auto` | Emit bare `<mxGraphModel>` (drawio FAQ) for single-page; full `<mxfile>` wrapper for multi-page. `auto` picks based on `diagrams.length`. |
| `quality_gate` | `on` / `off` | `on` | Adds edge-crossings, orthogonality conformance, edge-length variance, area utilization checks to validator. |
| `grounding_manifest` | `on` / `off` | `on` | Every node/edge in the plan must include a non-empty `source` field. Validator rejects orphans. |
| `auto_layout` | `off` / `elk` / `dot` / `auto` | `auto` | Replaces LLM-emitted coords with ELK Layered (preferred) or Graphviz dot output. `auto` runs ELK only when the diagram has >20 vertices (LLM coords are usually clean below that). |
| `text_metrics` | `off` / `auto` | `auto` | Runs `scripts/text-metrics.js` between plan validation and XML emit. Annotates each shape/container with `text_safe.{min_width, min_height, overflow}`. LLM must apply these as geometry lower bounds. Validator emits W106/W107/W108 if emitted XML is smaller than safe dims. Zero native deps (char-table measurement). See `references/text-metrics.md`. |
| `font_fit` | `off` / `auto` / `grow` | `auto` | Lightweight post-processor: shrinks `fontSize` when label text overflows its cell. `auto` shrinks only; `grow` also enlarges when boxes have headroom (useful after `auto_layout`). Skips edge labels and `style=text;` chrome. See `references/font-fit.md`. |
| `edge_routing` | `off` / `script` / `auto` | `auto` | Two-layer edge routing. LLM layer: plan gains `corridors[]` and `edge.waypoints[]` fields (read `references/routing-corridors.md`). Script layer: `scripts/route-edges.py` runs after ELK, detects edge-shape AABB intersections, inserts shortest-detour waypoints. `auto` activates when diagram has > 15 edges. `script` runs the post-emit script only (zero extra LLM tokens). See `references/routing-corridors.md`. |


## Generation profiles

Use the profile that matches the situation. Override any flag per-diagram with `<!-- lucid:feature=value -->` on the first line of the source plan.

### Production (default)

All features on. Use for client deliverables, team documentation, regulated diagrams.

```yaml
output_mode: auto
quality_gate: on
grounding_manifest: on
auto_layout: auto
text_metrics: auto
font_fit: auto
```

~93K tokens · ~80–180 s end-to-end for a 50–60 element diagram.

### Fast draft

For exploration and rough ideation. Skips grounding, text measurement, layout engine, and quality metrics. Produces structurally valid XML (correct parent IDs, container-relative coords, edge geometry) but without cite traceability, label-fit guarantees, or auto-layout.

**Switch back to production before any delivery.**

```yaml
output_mode: auto
quality_gate: off
grounding_manifest: off
auto_layout: off
text_metrics: off
font_fit: off
```

~58K tokens · ~50–110 s (~37% faster than production).

**Fast draft workflow — condensed steps:**

```
Step 1. READ 4 references (skip layout-engines.md, gestalt-rules.md)
         container-coords.md · edge-routing.md · plan-format.md · style-dictionary.md
Step 2. PLAN — JSON plan, no cite fields required
Step 3. EMIT XML — bare <mxGraphModel>, apply container-relative coords, two-layer edges
Step 4. SELF-CHECK (structural only):
         ✅ every edge has <mxGeometry relative="1">
         ✅ all IDs unique
         ✅ every parent= exists
         ✅ children use container-relative coordinates
         ✅ cross-container edges have parent = LCA
         ✅ no XML comments inside model
         ✅ HTML in value is escaped
         ✅ startSize on all swimlane containers
         ✅ edges in layer before icon layer
         ⚠️ style allowlist — best-effort only
         ❌ font sizes / label fit — skipped (no text_metrics)
Step 5. WRITE file
Step 6. VALIDATE structural errors only (E0xx) — no Q/G metrics
```

### Dense diagram (> 50 elements)

Force ELK regardless of vertex count; grow fonts after ELK expands shapes.

```
<!-- lucid:auto_layout=elk lucid:font_fit=grow -->
```

---

## Output requirement

Always produce a `.drawio` file saved to the user's workspace. **Never inline XML in chat.**

File naming: `NN_DiagramName/V_layout-name.drawio` (e.g. `01_System_Context/A_top_down_hub.drawio`).

## Output mode — bare vs wrapped (`output_mode`)

Per the drawio FAQ (drawio.com/doc/faq/ai-drawio-generation): *"AI systems can also generate just the `<mxGraphModel>` element without the `<mxfile>` and `<diagram>` wrappers... The simplified format is recommended for AI generation when multi-page support is not needed."*

Pick by mode:

- **`output_mode: bare`** — emit a bare fragment. Fewer XML nesting levels, lower syntax-error rate. Use for single-page diagrams.
  ```xml
  <mxGraphModel adaptiveColors="auto">
    <root>
      <mxCell id="0"/>
      <mxCell id="1" parent="0"/>
      <!-- shapes and edges, parent="1" or container ids -->
    </root>
  </mxGraphModel>
  ```
- **`output_mode: wrapped`** — emit the full `<mxfile><diagram><mxGraphModel>...` document. Required for multi-page diagrams (more than one `<diagram>` element).
- **`output_mode: auto`** (default) — use bare when the plan contains exactly one page; otherwise wrapped.

draw.io accepts both formats and auto-wraps bare fragments on open. Lucidchart's drawio importer accepts both.

> **Heads-up on existing templates:** all 15 `templates/*.drawio` files still use the wrapped form so they remain openable in any reader without re-wrapping. When the skill emits *new* diagrams, follow the `output_mode` flag.

## Plan-then-emit workflow (mandatory)

Raw LLM coordinate math fails on dense diagrams (overlaps, edges over icons, wrong parent IDs).
**Always plan structure before emitting XML.** The plan acts as the constraint that makes the
XML output clean.

```
Step 1. PLAN (JSON, in scratchpad)
  → list containers, shapes, edges with parent IDs + grid cell assignments
  → validate: every shape's parent exists; no two shapes share a grid cell;
    every edge endpoint is a valid id
Step 1.2. CORRIDOR PLANNING (when edge_routing != off AND edges > 15)
  → read references/routing-corridors.md
  → add corridors[] array to plan: one horizontal band between each shape row,
    one vertical strip between each shape column — min 40 px wide/tall
  → for any edge whose straight-line path crosses a non-endpoint shape,
    add waypoints[] to that edge routing it through the nearest corridor
  → re-validate: no corridor overlaps a shape AABB; corridors clear by ≥ 20 px
Step 1.5. TEXT METRICS (when text_metrics != off)
  → node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
  → For each shape/container where text_safe.overflow == true:
      - Set width  = max(declared_width,  text_safe.min_width)
      - Set height = max(declared_height, text_safe.min_height)
      - If swimlane: update startSize = max(declared_startSize, text_safe.min_startSize)
  → Re-check grid collisions (nodes may have grown); adjust neighbours if needed
  → Use diagram.annotated.plan.json as the plan going forward
Step 2. EMIT XML (read template, fill placeholders, apply plan)
Step 3. SELF-CHECK (re-read XML before writing file)
  → see "Pre-flight checklist" below
Step 4. WRITE file with the Write tool
Step 5. VALIDATE (optional but recommended for >20 shapes)
  → run scripts/validate.py
Step 6. OVERLAP REMOVAL (mandatory for dense/complex diagrams)
  → run scripts/elk-layout.py <file.drawio> --engine neato to automatically resolve overlaps
Step 6.5. EDGE ROUTING (when edge_routing != off)
  → run scripts/route-edges.py <file.drawio>
  → inserts waypoints around any shapes that edges still intersect post-ELK
  → re-run scripts/validate.py to confirm Q401 crossings → 0
```

See `references/plan-format.md` for the JSON plan schema.

### Grounding manifest (F3) — `grounding_manifest`

When `grounding_manifest: on` (default), **every** container, shape, and edge in the plan MUST include a non-empty `cite` field that traces the element to its source (file:line, doc:section, `user-stated`, `inferred from ...`, or `assumption:...`). The validator rejects any uncited entity with `G501`.

Goal: no hallucinated boxes on client deliverables. Every element on the diagram is traceable back to an artifact the user can verify.

Persist the plan next to the diagram as `<name>.plan.json` so `scripts/validate.py` auto-detects it (or pass `--plan path/to/plan.json` explicitly).

Disable per-diagram with `--features grounding_manifest=off` for sketchy exploration; turn back on before delivery.

## Workflow

1. **Identify layout pattern** → pick from the 12 patterns below (or compose)
2. **Read the relevant template** from `templates/` as a starting skeleton
3. **Read `references/container-coords.md`** if the diagram has any container/swimlane/pool
4. **Read `references/style-dictionary.md`** for color/style constants
5. **Read `references/gestalt-rules.md`** for spacing, density, alignment rules
6. **Read `references/shape-vocabulary/<vendor>.md`** if using AWS/Azure/GCP/UML/ER/BPMN icons
7. **Build the JSON plan** (see `references/plan-format.md`)
8. **Validate the plan** — parents exist, no grid collisions, edge endpoints valid
9. **Emit XML** — replace placeholders, add shapes, wire edges, apply scope styles
10. **Self-check** — run the pre-flight checklist (below)
11. **Write file** to workspace
12. **Validate** (optional) — `python3 scripts/validate.py <file.drawio>`
13. **Overlap Removal** (mandatory for dense/complex diagrams) — run `python3 scripts/elk-layout.py <file.drawio> --engine neato`

## Layout pattern selection (12 patterns)

| # | Pattern | When to use | Template |
|---|---|---|---|
| 1 | **hub-radial** | One central system, spokes to satellites | `hub-radial.drawio` |
| 2 | **scope-columns** | Two boundary scopes side by side (internal vs vendor) | `scope-columns.drawio` |
| 3 | **swimlanes** | Horizontal bands by trust zone / cadence / tenant | `swimlanes.drawio` |
| 4 | **pipeline** | LR flow: sources → processing → consumers (streaming, ETL) | `pipeline.drawio` |
| 5 | **tenant-namespace** | Nested containers per tenant (multi-tenant Kafka/Flink) | `tenant-namespace.drawio` |
| 6 | **c4-context** | C4 L1 — Person/System/External boundaries | `c4-context.drawio` |
| 7 | **c4-container** | C4 L2 — Containers inside a system | `c4-container.drawio` |
| 8 | **c4-component** | C4 L3 — Components inside a container | `c4-component.drawio` |
| 9 | **erd-crowfoot** | Entity-relationship with crow's-foot cardinality | `erd-crowfoot.drawio` |
| 10 | **uml-class** | UML class diagram (3-compartment boxes, inheritance) | `uml-class.drawio` |
| 11 | **sequence** | UML sequence — lifelines + messages | `sequence.drawio` |
| 12 | **tree-hierarchy** | Org chart, decision tree, taxonomy | `tree-hierarchy.drawio` |
| 13 | **flowchart-dag** | Flowchart with decision diamonds, start/end | `flowchart-dag.drawio` |
| 14 | **bpmn-process** | BPMN: pools, lanes, gateways, events, tasks | `bpmn-process.drawio` |
| 15 | **grid-matrix** | 2D classification / capability matrix | `grid-matrix.drawio` |

> The numbering exceeds 12 because C4 has three sub-patterns. Pick the **finest-grained** pattern that fits.

## The #1 rule: container-relative coordinates

> *"The #1 swimlane mistake is using absolute coordinates for children instead of
> container-relative coordinates."* — OpenAEC drawio-impl-swimlanes

Children inside a container use coordinates **relative to the container's top-left**, not
absolute canvas coordinates. Cross-lane edges must have `parent="<pool-id>"`, not `parent="1"`.

```
Pool      (parent="1")           x=40,  y=40        ← absolute (canvas)
  Lane A  (parent="pool")        x=0,   y=30        ← relative to pool
    Shape1(parent="lane_a")      x=40,  y=20        ← relative to lane A
  Lane B  (parent="pool")        x=0,   y=270       ← relative to pool
    Shape2(parent="lane_b")      x=40,  y=20        ← relative to lane B
Edge Shape1→Shape2 (parent="pool", source="shape1", target="shape2")
```

Read `references/container-coords.md` for the full coord math and worked examples.

## Two-layer edge rendering

Edges drawn **over** icons look amateurish. Use two layers:

```
<root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>                                <!-- default layer = icons -->
  <mxCell id="edges_layer" parent="0" value="Edges"/>        <!-- edges drawn first (behind) -->
  <!-- ...containers and shapes with parent="1" ... -->
  <!-- ...all edges with parent="edges_layer" ... -->
</root>
```

When draw.io renders, layers earlier in the list draw **first** (i.e. behind). Put edges in
the layer that comes *before* the icon layer to keep connectors behind shape glyphs.

Read `references/edge-routing.md` for full edge routing patterns (orthogonal, curved,
waypoints, label anchoring).

## Pre-flight checklist (run before writing the file)

| # | Check | Failure symptom |
|---|---|---|
| 1 | Every edge `mxCell` has `<mxGeometry relative="1" as="geometry"/>` child | Edge missing on import |
| 2 | All `id` values unique across the diagram | Random shapes disappear |
| 3 | Every shape's `parent=` exists in the document | Shape rendered at canvas origin |
| 4 | Shape coordinates are **relative to parent** when parent is a container | Shapes appear outside their swimlane |
| 5 | Cross-container edges have `parent="<common-ancestor>"` | Edge clipped or invisible |
| 6 | No XML comments (`<!-- -->`) inside the model | Import may fail in Lucidchart |
| 7 | HTML in `value` is escaped (`&amp;`, `&lt;`, `&gt;`, `&quot;`) | Malformed XML |
| 8 | Container header reserved with `startSize=N` and no shape overlaps it | Header text overlaps content (x >= startSize for horizontal=0; y >= startSize for horizontal=1) |
| 9 | Min 40px gutter on all sides of each shape; min 30px around container headers | Crowded layout |
| 10 | Hub-radial center shapes must have enough gap between quadrants (gap width >= shape width) | Center shape overlaps surrounding quadrant containers |
| 11 | Edges in a layer **before** the icon layer | Edges drawn over icons |
| 12 | All styles used are in the allowlist (`style-dictionary.md`) or vendor-vocabulary | Style fragments invented; broken in Lucidchart |
| 13 | Font sizes consistent within a category (titles 14, labels 12, sub-labels 10) | Visual noise |
| 14 | All labels fit declared geometry (`text_metrics` run clean — zero W106/W107/W108) | Text clips or overflows node box |

## Style allowlist

Use only styles from these sources (do not invent fragments):

- `references/style-dictionary.md` — general palette, scope containers, edge styles
- `references/shape-vocabulary/aws.md` — AWS official icons (mxgraph.aws4.*)
- `references/shape-vocabulary/azure.md` — Azure icons (mxgraph.azure.*)
- `references/shape-vocabulary/gcp.md` — GCP icons (mxgraph.gcp2.*)
- `references/shape-vocabulary/uml-erd-bpmn.md` — UML class, ER, BPMN shapes

If you need a style that is **not** in the allowlist, add it to the appropriate vocabulary
file first and document its source — then use it.

## Scope container styles (CIAM-inspired)

```
Green (FMI internal):     swimlane;startSize=26;dashed=1;strokeColor=#2E7D32;strokeWidth=2;fillColor=none;fontColor=#2E7D32;fontSize=12;fontStyle=1;
Black (vendor/external):  swimlane;startSize=26;dashed=1;strokeColor=#424242;strokeWidth=1.5;fillColor=none;fontColor=#424242;fontSize=12;fontStyle=1;
Blue (cloud zone):        swimlane;startSize=26;dashed=1;strokeColor=#1565C0;strokeWidth=2;fillColor=none;fontColor=#1565C0;fontSize=12;fontStyle=1;
Orange (regulated):       swimlane;startSize=26;dashed=1;strokeColor=#E65100;strokeWidth=2;fillColor=none;fontColor=#E65100;fontSize=12;fontStyle=1;
```

## Reference files (read on demand)

Critical (read first when diagram has matching feature):
- **container-coords.md** — coord math for containers, swimlanes, nested pools (read for #3, #5, #8, #14)
- **edge-routing.md** — two-layer rendering, orthogonal/curved edges, waypoints, label anchor
- **plan-format.md** — JSON layout plan schema (the planning step)
- **font-fit.md** — adaptive `fontSize` algorithm and bounds (read when any label > 20 chars or using multi-line C4-style labels)
- **routing-corridors.md** — corridor planning rules and `corridors[]` / `edge.waypoints[]` schema (read when `edge_routing != off` and diagram has > 15 edges)

Examples & guides:
- **prompt-examples.md** — 5 canonical prompts (C4 container, pipeline, BPMN swimlanes, ERD, multi-tenant) — copy/paste starting points
- **layout-engines.md** — when to use ELK vs Graphviz `dot` / `neato`; direction guide per pattern

Supporting (read for details):
- **xml-schema.md** — mxGraph attribute reference, geometry, layers, tags
- **style-dictionary.md** — color palettes, component fills, edge styles, legend snippets
- **layout-patterns.md** — coordinate guides for all 15 patterns
- **gestalt-rules.md** — 10 design rules (flow, spacing, typography, density)
- **validator.md** — what `scripts/validate.py` checks and how to fix each violation

Vendor vocabularies:
- **shape-vocabulary/aws.md** — AWS service icons (compute, storage, network, db, ml, etc.)
- **shape-vocabulary/azure.md** — Azure service icons
- **shape-vocabulary/gcp.md** — GCP service icons
- **shape-vocabulary/uml-erd-bpmn.md** — UML class, ER notation, BPMN gateways/events/tasks

## Scripts

- `scripts/validate.py` — pre-flight validator (E0xx errors, W1xx warnings, Q4xx quality metrics, G5xx grounding). Run with: `python3 scripts/validate.py <file>.drawio`
- `scripts/elk-layout.py` — ELK / Graphviz auto-layout (honors `auto_layout` flag). Run with: `python3 scripts/elk-layout.py <file>.drawio --engine auto` (or `--engine neato` for overlap removal)
- `scripts/route-edges.py` — obstacle-push edge routing (honors `edge_routing` flag). Run with: `python3 scripts/route-edges.py <file>.drawio` (after elk-layout, before fit-fonts)
- `scripts/fit-fonts.py` — adaptive `fontSize` post-processor (honors `font_fit` flag). Run with: `python3 scripts/fit-fonts.py <file>.drawio --mode auto`


## When the user does not specify a layout

Pick the layout by intent:

| User says... | Pick |
|---|---|
| "system context", "external systems and users" | c4-context |
| "show the containers / services inside X" | c4-container |
| "deployment / hosting / where things run" | scope-columns or swimlanes |
| "data flow / pipeline / streaming / ETL" | pipeline |
| "multi-tenant / per-tenant" | tenant-namespace |
| "central X integrating with N satellites" | hub-radial |
| "database schema / entities and relationships" | erd-crowfoot |
| "class diagram / domain model" | uml-class |
| "how the request flows through services" (call ordering matters) | sequence |
| "decision tree / process with conditions" | flowchart-dag |
| "business process with gateways / events" | bpmn-process |
| "org chart / taxonomy / hierarchy" | tree-hierarchy |
| "capability map / 2D classification" | grid-matrix |

If still unclear, ask one question — do not guess.
