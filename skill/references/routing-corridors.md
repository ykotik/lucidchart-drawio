# Routing Corridors (F7)

Routing corridors are empty horizontal or vertical bands reserved in the grid
layout so edges have a clean path between shape rows and columns. When
`edge_routing` is `auto` or `on` (default: `auto`), add corridors to the JSON
plan during the plan construction step **before** emitting XML.

The corridor plan is the LLM layer of F7. It reduces intersections before the
diagram is written. `scripts/route-edges.py` (the script layer) catches any
intersections that remain after ELK relayout.

---

## When to add corridors

Add at least one corridor whenever:

- The diagram has > 15 edges, **or**
- Any edge's straight-line path passes through a non-endpoint shape, **or**
- Edges cross between swimlane rows or pipeline stages

Skip corridors only for sequence and BPMN diagrams (ELK is disabled for those
patterns — no relayout means no post-layout intersection risk).

---

## Plan JSON additions

### `corridors[]` array (plan-level)

Add a `corridors` key alongside `shapes` and `edges`:

```jsonc
{
  "pattern": "swimlanes",
  "canvas": { "w": 1600, "h": 900 },
  "corridors": [
    {
      "id": "h_r1_r2",
      "axis": "h",          // "h" = horizontal band between rows
      "y": 220,             // top edge of the band (canvas-absolute, px)
      "height": 40,         // band height — 40 px minimum
      "between": ["row_1", "row_2"],   // human label — helps audit
      "cite": "routing"
    },
    {
      "id": "v_c1_c2",
      "axis": "v",          // "v" = vertical strip between columns
      "x": 440,             // left edge of the strip (canvas-absolute, px)
      "width": 50,
      "between": ["col_1", "col_2"],
      "cite": "routing"
    }
  ],
  "shapes": [ ... ],
  "edges": [ ... ]
}
```

`cite` must be `"routing"` for all corridor entries — the grounding validator
accepts this as a structural element, not a user-data element.

### `edge.waypoints[]` (edge-level, optional)

When you can already determine that an edge needs to detour, list explicit
waypoints in the plan rather than relying on the script:

```jsonc
{
  "id": "e_api_db",
  "source": "api",
  "target": "db",
  "label": "SQL",
  "waypoints": [
    { "x": 160, "y": 240 }   // routes through corridor h_r1_r2
  ],
  "cite": "interfaces.xlsx:row 14"
}
```

The script reads existing waypoints and preserves them unless the waypoint
itself lands inside a blocker (rare; script adjusts automatically).

---

## Corridor sizing rules

| Scenario | Minimum corridor size |
|---|---|
| Single edge passes through | 40 px tall / wide |
| 2–3 parallel edges | 60 px tall / wide |
| Cross-lane edge (swimlane) | Use swimlane `startSize` gap (already ≥ 26 px) |
| Pipeline stage transition | 60 px between stage columns |

---

## Placement rules

1. Place horizontal corridors between shape rows — never inside a row.
2. Centre the corridor on the midpoint between the bottom of the upper row and
   the top of the lower row.
3. Keep ≥ 20 px clearance between the corridor edge and the nearest shape AABB.
4. Vertical corridors: same rules applied to columns.
5. Corridors must not overlap shape AABBs — move corridor or shapes if they do.

### Quick sizing heuristic

```
row_bottom  = max(shape.y + shape.h) across all shapes in the upper row
next_top    = min(shape.y)           across all shapes in the lower row
gap         = next_top - row_bottom

gap >= 40 px  →  existing gap is sufficient; set corridor.y = row_bottom + 10
gap < 40 px   →  note in plan; expand shape spacing by (40 - gap) px before emitting
```

---

## Pattern-specific guidance

### Pipeline (LR flow)

Vertical corridors between each stage:

```
Sources  | corr_v1 | Kafka topics | corr_v2 | Flink jobs | corr_v3 | Sinks
```

Stage columns are typically 200 px wide with 60 px gaps → corridors fit naturally.

### Swimlanes (horizontal bands)

Horizontal corridors between lanes are the swimlane gaps themselves.
Cross-lane edges should use `exitX/entryX` exit points to hug the lane border,
then turn in the inter-lane gap. No extra corridor needed if `startSize ≥ 26`.

### C4 container / component

Horizontal corridor between the front-end tier and the middle tier, and between
the middle tier and the data tier. Typically y-positions between rows of shapes:

```
Row 0: users/actors
  ↕  corridor h0 (y = 100, height = 40)
Row 1: containers
  ↕  corridor h1 (y = 240, height = 40)
Row 2: databases / external systems
```

### Hub-radial

Radial diagrams rarely need corridors — spokes radiate outward from the hub
and do not cross each other when placed at equal angular intervals. Skip
corridor planning for hub-radial; rely on the script layer only.

---

## Validation

`scripts/validate.py` Q401 (edge crossings) measures intersection count before
and after route-edges. After a successful F7 run, Q401 should report 0.

If Q401 is non-zero after route-edges, the W110 warning in route-edges output
identifies which edges are still blocked — those diagrams are likely too dense
for single-waypoint detours. Recommendation: `auto_layout=elk` with wider
`spacing.nodeNode`.
