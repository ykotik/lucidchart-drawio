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
| `anchor_attrs` on edges | See **Edge anchors** section below — required when edges≥20 or cross-container edges≥3 (W121). |
| `waypoints` on edges | Explicit waypoints for edges that must detour around a blocker — populated during Step 1.2 corridor planning (F7). Each entry is `{x, y}` in canvas-absolute coordinates. `scripts/route-edges.py` also writes waypoints here when it detects intersections post-ELK. |
| `corridors[]` | **F7 edge_routing** — reserved routing bands. Add when diagram has > 15 edges. Each entry needs `id`, `axis` (`h`\|`v`), `y`+`height` (horizontal) or `x`+`width` (vertical), and `cite: "routing"`. See `routing-corridors.md` for sizing rules and pattern-specific guidance. |
| `legend.include` | Auto-add a legend box at the bottom-right |
| `vendor_icon` on shapes | Looks up the icon style from shape-vocabulary |
| `cite` on every shape / container / edge | **F3 grounding manifest — required when `grounding_manifest=on`.** See the section below. |

---

## Edge anchors

mxGraph edges express connection anchor points via four style attributes:

| Attribute | Range | Meaning |
|---|---|---|
| `exitX` | 0–1 | Horizontal fraction of source shape bounds where edge exits |
| `exitY` | 0–1 | Vertical fraction of source shape bounds where edge exits |
| `entryX` | 0–1 | Horizontal fraction of target shape bounds where edge enters |
| `entryY` | 0–1 | Vertical fraction of target shape bounds where edge enters |

Without these, mxGraph auto-picks connection points that can look wrong on dense diagrams, especially across container boundaries.

**When required:** The validator emits **W121** when `edge_count >= 20` OR `cross_container_count >= 3`. At that threshold, every edge connecting two non-container shapes must carry all four attrs.

**Exempt edges:** Edges where source or target is a container (swimlane/group) may legitimately omit anchors — mxGraph connects to the container perimeter dynamically.

**Worked example** — edge exiting the right side of source, entering the left side of target (the most common LR-pipeline pattern):

```xml
<mxCell id="e4" value="route traffic"
  style="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0;entryY=0.5;
         rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
  edge="1" source="alb" target="ecs" parent="vpc">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Common anchor combinations:

| Direction | exitX | exitY | entryX | entryY |
|---|---|---|---|---|
| Left → Right | 1 | 0.5 | 0 | 0.5 |
| Right → Left | 0 | 0.5 | 1 | 0.5 |
| Top → Bottom | 0.5 | 1 | 0.5 | 0 |
| Bottom → Top | 0.5 | 0 | 0.5 | 1 |

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
| 5 | Every container's first child clears `startSize` | Parse `horizontal` from the container's `style` string (default `1` if absent). `horizontal=1` → top header: flag children where `y < startSize`. `horizontal=0` → left header: flag children where `x < startSize`. |
| 6 | Every edge's `parent` is the lowest common ancestor of source and target. For shapes nested 3+ levels deep (e.g. grandchildren of the same grandparent container), the LCA is the grandparent — not `"1"`. Example: shape in `ext_z1` (child of `ext_scope`) and shape in `ext_z2` (child of `ext_scope`) → edge `parent="ext_scope"`. | Walk parent chain from source up; first ancestor that also contains target |
| 7 | Shape and container ids are unique across the whole plan | Set membership check |
| 8 | Every shape assigned a `grid_cell` has `y` equal to `grid_start_y + row * cell_h` (±padding). No shape's y falls between two grid rows. Straddle = wrong row assignment. | For each shape with grid_cell, compute expected y from cell; flag if actual y differs by more than cell_padding |
| 9 | No dead-end shapes. Every non-terminal shape (not an explicit sink/store) has at least one outgoing edge. Flag any shape with edges in but no edges out — either add the missing connection or mark it as a sink in the plan. | Build an adjacency set; for each shape check out-degree > 0 or explicitly tagged `terminal: true` |

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
