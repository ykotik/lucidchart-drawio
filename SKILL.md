---
name: lucidchart-drawio
description: >-
  Generate Lucidchart-importable architecture diagrams as draw.io XML (.drawio) with
  strict layout discipline and clean edge routing. 15 layout patterns: hub-radial,
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
  diagram_eval: off          # on | off              — Node-F1 / Path-F1 vs ground-truth plan (DiagramEval)
  auto_layout: off           # off | elk | dot       — call ELK or Graphviz dot for coord assignment
  critic_judge_loop: auto    # off | on | auto       — auto = on when shapes > 15 (See it. Say it. Sorted.)
  eval_harness: off          # on | off              — run eval/ regression suite
---

# Lucidchart draw.io Diagram Skill (v2.1)

## Feature flags

The skill's behavior is controlled by the `features:` block in the YAML frontmatter above. Override per-diagram with a `<!-- lucid:feature=value -->` comment on the first line of the source plan, or by passing `--features <key>=<value>,...` to `scripts/validate.py` / `scripts/elk-layout.py` where supported. **Each feature can be turned off independently.**

| Flag | Values | Default | What it does |
|---|---|---|---|
| `output_mode` | `bare` / `wrapped` / `auto` | `auto` | Emit bare `<mxGraphModel>` (drawio FAQ) for single-page; full `<mxfile>` wrapper for multi-page. `auto` picks based on `diagrams.length`. |
| `quality_gate` | `on` / `off` | `on` | Adds edge-crossings, orthogonality conformance, edge-length variance, area utilization checks to validator. |
| `grounding_manifest` | `on` / `off` | `on` | Every node/edge in the plan must include a non-empty `source` field. Validator rejects orphans. |
| `diagram_eval` | `on` / `off` | `off` | Computes Node-F1 / Path-F1 (DiagramEval, EMNLP 2025) when a ground-truth plan is provided. |
| `auto_layout` | `off` / `elk` / `dot` | `off` | Replaces LLM-emitted coords with ELK Layered (preferred) or Graphviz dot output. |
| `critic_judge_loop` | `off` / `on` / `auto` | `auto` | Iterative Critic→Candidates→Judge refinement (`auto` = on when >15 shapes). |
| `eval_harness` | `on` / `off` | `off` | Runs `eval/` regression suite against fixed reference diagrams. |

To turn everything off (legacy v2.0 behavior): set every flag to `off` except `output_mode: wrapped`.

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
Step 2. EMIT XML (read template, fill placeholders, apply plan)
Step 3. SELF-CHECK (re-read XML before writing file)
  → see "Pre-flight checklist" below
Step 4. WRITE file with the Write tool
Step 5. VALIDATE (optional but recommended for >20 shapes)
  → run scripts/validate.py
```

See `references/plan-format.md` for the JSON plan schema.

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
| 8 | Container header reserved with `startSize=N` and no shape overlaps it | Header text overlaps content |
| 9 | Min 40px gutter on all sides of each shape; min 30px around container headers | Crowded layout |
| 10 | Edges in a layer **before** the icon layer | Edges drawn over icons |
| 11 | All styles used are in the allowlist (`style-dictionary.md`) or vendor-vocabulary | Style fragments invented; broken in Lucidchart |
| 12 | Font sizes consistent within a category (titles 14, labels 12, sub-labels 10) | Visual noise |

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

- `scripts/validate.py` — pre-flight validator (duplicate IDs, orphan parents, missing edge
  geometry, container/coord sanity, overlap detection). Run with:
  `python3 scripts/validate.py path/to/diagram.drawio`

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
