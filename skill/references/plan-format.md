# JSON Layout Plan Format

Before emitting any mxGraph XML, build a JSON plan. The plan is the constraint that
keeps the XML output clean. **The plan does not need to be persisted to disk** — it
lives in your scratchpad / thinking. But it must be built and validated **before**
the XML is written.

This is the "plan-then-emit" technique documented in the AWS GenAI-DrawIO-Creator
paper and the arXiv DiagrammerGPT paper.

---

## Plan schema

```jsonc
{
  "pattern": "swimlanes | pipeline | hub-radial | c4-context | ... ",
  "canvas": { "w": 1600, "h": 900 },
  "grid":   { "cols": 8,  "rows": 4, "cell_w": 200, "cell_h": 220 },

  "containers": [
    {
      "id": "pool",
      "parent": "1",
      "label": "External Users",
      "x": 40, "y": 40, "w": 1520, "h": 820,
      "style_key": "scope_green",
      "startSize": 30,
      "cite": "hosting.xlsx:SYS-12"            // F3 grounding — REQUIRED when grounding_manifest=on
    },
    {
      "id": "lane_a",
      "parent": "pool",
      "label": "Identity",
      "x": 0, "y": 30, "w": 1520, "h": 260,
      "style_key": "lane_default",
      "startSize": 120,
      "cite": "user-stated"
    }
  ],

  "shapes": [
    {
      "id": "api",
      "parent": "lane_a",
      "label": "Public API",
      "grid_cell": { "row": 0, "col": 1 },
      "x": 160, "y": 40,
      "w": 160, "h": 64,
      "style_key": "service_box",
      "vendor_icon": null,
      "cite": "hla.md:§3.2 'Public API gateway'"     // F3 grounding for this shape
    }
  ],

  "edges": [
    {
      "id": "e_api_db",
      "parent": "lane_a",
      "source": "api",
      "target": "db",
      "label": "SQL",
      "style_key": "edge_orthogonal_sync",
      "exit": { "x": 1, "y": 0.5 },
      "entry": { "x": 0, "y": 0.5 },
      "waypoints": [],
      "cite": "interfaces.xlsx:row 14 (api → db SQL)"  // F3 grounding for the edge itself
    }
  ],

  "corridors": [
    {
      "id": "h_r1_r2",
      "axis": "h",            // "h" = horizontal band | "v" = vertical strip
      "y": 220,               // top edge of band (canvas-absolute px)
      "height": 40,           // min 40 px; 60 px when 2-3 edges share the corridor
      "between": ["row_1", "row_2"],   // human label for auditing
      "cite": "routing"       // always "routing" — accepted by grounding validator
    }
  ],

  "legend": {
    "include": true,
    "position": "bottom-right",
    "items": [ "sync", "async", "auth" ]
  }
}
```

---

## Required fields

| Field | Type | Why required |
|---|---|---|
| `pattern` | string | Selects the template file and routing defaults |
| `canvas.w`, `canvas.h` | int | Bounds for the entire diagram |
| `containers[].id` | string | Must be unique; used as `parent` for children |
| `containers[].parent` | string | "1" for canvas; container id for nesting |
| `containers[].x/y/w/h` | int | Relative to parent — see `container-coords.md` |
| `containers[].startSize` | int | Reserved header strip; children must clear it |
| `shapes[].id` | string | Must be unique |
| `shapes[].parent` | string | The container the shape sits inside |
| `shapes[].x/y/w/h` | int | Relative to parent |
| `edges[].source`, `edges[].target` | string | Must reference existing shape or container ids |
| `edges[].parent` | string | Lowest common ancestor of source and target |

---

## Optional fields that improve output quality

| Field | Effect |
|---|---|
| `grid_cell` on shapes | Lets you verify no two shapes claim the same cell |
| `exit` / `entry` on edges | Forces clean routing — see `edge-routing.md` §4 |
| `waypoints` on edges | Explicit waypoints for edges that must detour around a blocker — populated during Step 1.2 corridor planning (F7). Each entry is `{x, y}` in canvas-absolute coordinates. `scripts/route-edges.py` also writes waypoints here when it detects intersections post-ELK. |
| `corridors[]` | **F7 edge_routing** — reserved routing bands. Add when diagram has > 15 edges. Each entry needs `id`, `axis` (`h`\|`v`), `y`+`height` (horizontal) or `x`+`width` (vertical), and `cite: "routing"`. See `routing-corridors.md` for sizing rules and pattern-specific guidance. |
| `legend.include` | Auto-add a legend box at the bottom-right |
| `vendor_icon` on shapes | Looks up the icon style from shape-vocabulary |
| `cite` on every shape / container / edge | **F3 grounding manifest — required when `grounding_manifest=on`.** See the section below. |

---

## F3: Grounding manifest — every entity cites a source

When the skill's `grounding_manifest` feature flag is `on` (default), **every** `containers[]`, `shapes[]`, and `edges[]` entry must include a non-empty `cite` field. The validator (`scripts/validate.py`) emits `G501` ERROR for any unciteed entity.

The goal: no hallucinated boxes, arrows, or labels in client-facing deliverables. Every element on the diagram traces back to an artifact the user can verify.

### Citation formats

Free-form string. Use the format that fits your source:

| Source type | Example `cite` value |
|---|---|
| Spreadsheet cell or row | `hosting.xlsx:SYS-12` , `interfaces.xlsx:row 14` |
| Document section | `hla.md:§3.2 'Public API gateway'` , `Solution Design v3.pdf:p.18` |
| Code / config | `terraform/api.tf:147 aws_lambda_function.api` |
| Issue tracker | `JIRA:ENT-4421` , `GitHub#1203` |
| Direct user statement | `user-stated` (verbatim from chat / message) |
| Inference from another element | `inferred from {hosting.xlsx:SYS-12, SYS-13}` |
| Template default (e.g. legend box) | `template-default` |
| Architectural assumption to challenge later | `assumption:multi-region warm DR` |

### Why a `cite` field per element, not a single bibliography

A central bibliography lets boxes drift. Per-element `cite` forces the model to justify every choice at the point of choice. When the validator rejects an emitted shape, the cause is immediate ("api has no cite") rather than "the bibliography is incomplete."

### When `grounding_manifest=off`

If turned off, `cite` is ignored. Use for sketchy exploration where source-tracing is overhead. Switch back on before any client-facing deliverable.

### Validator behavior

- `G501` ERROR — `<id>` has no `cite` field (or `cite` is empty / whitespace).
- `G502` WARN — `<id>.cite == "assumption:..."` — listed for the user to confirm before delivery.
- `G503` INFO — coverage summary at end (e.g. `Grounding: 17/17 cited, 2 assumptions, 0 missing`).

---

## Validation checks to run on the plan (before emitting XML)

| # | Check | Implementation hint |
|---|---|---|
| 1 | Every shape's `parent` exists in `containers[]` or equals `"1"` | Build a set of all container ids; check membership |
| 2 | Every edge's `source` and `target` exist in `shapes[]` (or containers[]) | Build a set of all shape+container ids; check membership |
| 3 | No two shapes share the same `grid_cell` | Build a `{(row,col) → shape_id}` map; check for duplicates |
| 4 | Every container's children fit inside its `w` and `h` | For each container, find children where `x+w > container.w` or `y+h > container.h` |
| 5 | Every container's first child clears `startSize` | For each container, find children with `y < startSize` |
| 6 | Every edge's `parent` is the lowest common ancestor of source and target | Walk parent chain from source up; first ancestor that also contains target |
| 7 | Shape and container ids are unique across the whole plan | Set membership check |

If any check fails, **adjust the plan** before emitting XML — do not skip ahead.

---

## Grid-cell to coordinates (recommended)

For consistent spacing, define a grid at the top of the plan, then assign each shape
to a `(row, col)` cell. Compute `x` and `y` from the cell:

```
cell_origin_x = grid_start_x + col * cell_w
cell_origin_y = grid_start_y + row * cell_h
shape.x = cell_origin_x + cell_padding_x        (typically 20)
shape.y = cell_origin_y + cell_padding_y        (typically 20)
shape.w = cell_w - 2 * cell_padding_x           (typically 160)
shape.h = cell_h - 2 * cell_padding_y           (typically 64)
```

This produces uniformly aligned shapes — the single biggest quality win.

---

## Pattern-specific grid defaults

| Pattern | Grid columns | Grid rows | Cell width | Cell height |
|---|---|---|---|---|
| hub-radial | 1 hub + 6-12 spokes around radius | — | — | — |
| scope-columns | 2 outer cols × N inner zone cols | N rows of shapes per zone | 200 | 100 |
| swimlanes | N shapes per lane | 1 per lane row | 180 | 80 |
| pipeline | 4-7 stages | 1-3 rows per stage | 200 | 80 |
| tenant-namespace | 3 cols inside each tenant | 2 rows | 180 | 70 |
| c4-context | 3-4 cols | 2 rows | 200 | 100 |
| c4-container | 4-6 cols | 2-3 rows | 200 | 100 |
| c4-component | 4-6 cols | 2-3 rows | 200 | 100 |
| erd-crowfoot | freeform (entities placed by relationship) | — | 220 | varies (h = 30 + 22*field_count) |
| uml-class | 3-5 cols | 2-3 rows | 220 | varies |
| sequence | N lifelines as columns | 1 row per message (y-axis is time) | 160 | 30 |
| tree-hierarchy | levels as rows | leaves at bottom | 180 | 70 |
| flowchart-dag | flexible | top-down | 180 | 70 |
| bpmn-process | N tasks per lane | 2-4 lanes | 140 | 70 |
| grid-matrix | 4-8 cols (categories) | 4-8 rows | 160 | 90 |

---

## Worked example: small swimlane plan

User: "Show a 2-lane swimlane with API → Service → DB in lane 1 and Auth Service in lane 2"

```jsonc
{
  "pattern": "swimlanes",
  "canvas": { "w": 1000, "h": 600 },
  "grid":   { "cols": 4, "rows": 2, "cell_w": 220, "cell_h": 200 },

  "containers": [
    { "id": "pool",   "parent": "1",    "label": "System",
      "x": 40, "y": 40, "w": 920, "h": 500, "style_key": "scope_green", "startSize": 30 },
    { "id": "lane_app",  "parent": "pool",
      "label": "Application", "x": 0, "y": 30, "w": 920, "h": 235,
      "style_key": "lane_default", "startSize": 120 },
    { "id": "lane_auth", "parent": "pool",
      "label": "Auth", "x": 0, "y": 265, "w": 920, "h": 235,
      "style_key": "lane_default", "startSize": 120 }
  ],

  "shapes": [
    { "id": "api", "parent": "lane_app", "label": "API",
      "grid_cell": {"row":0,"col":0}, "x": 140, "y": 80, "w": 160, "h": 64,
      "style_key": "service_box" },
    { "id": "svc", "parent": "lane_app", "label": "Service",
      "grid_cell": {"row":0,"col":1}, "x": 360, "y": 80, "w": 160, "h": 64,
      "style_key": "service_box" },
    { "id": "db",  "parent": "lane_app", "label": "DB",
      "grid_cell": {"row":0,"col":2}, "x": 580, "y": 80, "w": 160, "h": 64,
      "style_key": "cylinder_db" },
    { "id": "auth","parent": "lane_auth","label": "Auth Service",
      "grid_cell": {"row":0,"col":0}, "x": 140, "y": 80, "w": 160, "h": 64,
      "style_key": "service_box" }
  ],

  "edges": [
    { "id": "e1", "parent": "lane_app", "source": "api", "target": "svc",
      "style_key": "edge_orthogonal_sync",
      "exit": {"x":1,"y":0.5}, "entry": {"x":0,"y":0.5} },
    { "id": "e2", "parent": "lane_app", "source": "svc", "target": "db",
      "style_key": "edge_orthogonal_sync",
      "exit": {"x":1,"y":0.5}, "entry": {"x":0,"y":0.5} },
    { "id": "e3", "parent": "pool",    "source": "api", "target": "auth",
      "label": "verify token",
      "style_key": "edge_orthogonal_auth",
      "exit": {"x":0.5,"y":1}, "entry": {"x":0.5,"y":0} }
  ]
}
```

Note `e3.parent = "pool"` (cross-lane edge → lowest common ancestor).

Now emit the XML from this plan, mapping `style_key` to the actual mxGraph style
strings from `style-dictionary.md` and `shape-vocabulary/*.md`.
---

## Edge constraints (enforced by validator W109 / W111 / W113)

### 1. Unique (source, target) pairs

Each `(source, target)` combination may appear **at most once** in the `edges` array.
Encode relationship type via the `arrow` hint and edge style — not as duplicate edges.

❌ **Forbidden — same pair twice:**
```json
{ "id": "e1", "source": "customer", "target": "person", "label": "extends" },
{ "id": "e2", "source": "customer", "target": "person", "label": "generalization" }
```

✅ **Correct — one edge, type in arrow style:**
```json
{ "id": "e1", "source": "customer", "target": "person", "label": "extends",
  "arrow": "hollow-block", "cite": "user-stated" }
```

`arrow` hint → `endArrow` style mapping:

| `arrow` value | `endArrow` style | UML meaning |
|---|---|---|
| `hollow-block` | `block;endFill=0` | Inheritance / generalisation |
| `filled-diamond` | `diamondThin;endFill=1` | Composition |
| `open-diamond` | `diamondThin;endFill=0` | Aggregation |
| `open` | `open` | Plain association |
| `none` | `none` | Dependency (dashed) |

### 2. Convergence node annotation (W111)

When a node will have > 3 edges total (in + out), add a `ports` hint so the emitter
assigns staggered `exitX/Y` and `entryX/Y` values:

```json
{
  "id": "ecs",
  "label": "ECS Fargate",
  "ports": { "out": "right-staggered", "in": "left-staggered" },
  "cite": "user-stated"
}
```

| `ports` value | Meaning |
|---|---|
| `right-staggered` | Exits along right side: `exitX=1.0`, `exitY` from 0.2 to 0.8 |
| `left-staggered` | Entries along left side: `entryX=0.0`, `entryY` from 0.2 to 0.8 |
| `bottom-staggered` | Exits along bottom: `exitY=1.0`, `exitX` from 0.2 to 0.8 |
| `top-staggered` | Entries along top: `entryY=0.0`, `entryX` from 0.2 to 0.8 |

### 3. Container height sizing (W112)

Set each container's `h` using actual child count — **never copy the canvas plan height**:

```
container_h = startSize + (n_direct_children × (child_h + gap)) + 60
```

Example: 4 children at child_h = 50, gap = 20, startSize = 30:
`container_h = 30 + (4 × 70) + 60 = 370 px`

### 4. External shapes grouping (W113)

When the plan includes a primary container (VPC, system boundary, etc.), all shapes
outside that container **must** be wrapped in their own named dashed boundary:

```json
{
  "containers": [
    { "id": "vpc",        "label": "AWS VPC",        "cite": "user-stated" },
    { "id": "inet_layer", "label": "Internet Layer",
      "style": "dashed-boundary", "cite": "user-stated" }
  ],
  "shapes": [
    { "id": "route53",    "label": "Route 53",    "parent": "inet_layer", "cite": "user-stated" },
    { "id": "cloudfront", "label": "CloudFront",  "parent": "inet_layer", "cite": "user-stated" },
    { "id": "cognito",    "label": "Cognito",     "parent": "inet_layer", "cite": "user-stated" }
  ]
}
```

Shapes directly on the canvas (`parent` omitted or `"1"`) alongside a primary container
trigger W113. Every orphan group needs a boundary label.
