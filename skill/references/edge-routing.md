# Edge Routing — Clean Connectors

The single biggest visual quality lever after layout is **how edges are routed**:
orthogonal vs straight vs curved, where they enter/exit shapes, how they avoid
crossing other shapes, and whether they render behind or over icons.

---

## 1. Two-layer rendering (edges drawn behind icons)

draw.io renders layers in document order — **layers earlier in the XML draw first
(behind), later layers draw on top**. For clean diagrams, put edges in a layer that
comes **before** the icon/shape layer.

```xml
<root>
  <mxCell id="0"/>
  <mxCell id="edge_layer" value="Edges" parent="0"/>        <!-- drawn first (BEHIND) -->
  <mxCell id="1" parent="0"/>                               <!-- default shape layer (on top) -->

  <!-- all containers + shapes: parent="1" (or a container id) -->
  <!-- all edges: parent="edge_layer" -->
</root>
```

For simpler diagrams without explicit edge layering, the default order
(`<mxCell id="0"/>`, then `<mxCell id="1" parent="0"/>`) puts everything on one layer
and edges naturally draw in source order. Use two layers when:
- you have icon-shaped nodes (AWS/Azure/GCP icons) where edges would visually cross the icon glyph
- you have dense connectors crossing each other
- the diagram has more than 20 shapes

**Note on container parents for edges:** even with a two-layer setup, an edge that
visually sits inside a container should still have the container as its `parent` if
both endpoints are inside that container. The "edge layer" pattern is used when you
want **all** edges at canvas level. Pick one strategy per diagram, do not mix.

---

## 2. Edge style — orthogonal vs straight vs curved

```
Orthogonal (default for architecture):
  edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;jettySize=auto;orthogonalLoop=1;

Orthogonal with rounded corners (nicer for ERD/UML):
  edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;curved=0;

Straight (use for hub-radial, sequence messages):
  edgeStyle=none;html=1;rounded=0;

Curved (use sparingly — looks decorative):
  edgeStyle=orthogonalEdgeStyle;curved=1;html=1;rounded=1;

Entity-relation (for ERD crow's foot):
  edgeStyle=entityRelationEdgeStyle;startArrow=ERmany;endArrow=ERone;html=1;rounded=0;
```

**Rule of thumb:**
- **Orthogonal** for boxes-and-arrows diagrams (architecture, BPMN, flowchart)
- **Straight** for radial / hub-spoke / sequence
- **Curved** only when you specifically want a "flow" feeling and have ≤6 edges

---

## 3. Arrow heads

```
Standard arrow:        endArrow=classic;
Filled arrow (closed): endArrow=classicThin;endFill=1;
Open arrow:            endArrow=open;
None:                  endArrow=none;
Diamond:               endArrow=diamond;
Diamond filled:        endArrow=diamond;endFill=1;
UML aggregation:       endArrow=diamondThin;endFill=0;
UML composition:       endArrow=diamondThin;endFill=1;
UML inheritance:       endArrow=block;endFill=0;
UML interface impl:    endArrow=block;endFill=0;dashed=1;
ER one (line):         endArrow=ERone;
ER many (crow's foot): endArrow=ERmany;
ER zero or one:        endArrow=ERzeroToOne;
ER one or many:        endArrow=ERoneToMany;
ER zero or many:       endArrow=ERzeroToMany;

Start side is the mirror: startArrow=...
```

For bidirectional edges, set both `startArrow=` and `endArrow=`.

---

## 4. Edge entry/exit points (control where the arrow attaches)

By default draw.io picks the entry/exit side automatically. To force the side:

```
Exit from right side of source:    exitX=1;exitY=0.5;exitDx=0;exitDy=0;
Exit from left of source:          exitX=0;exitY=0.5;exitDx=0;exitDy=0;
Exit from bottom of source:        exitX=0.5;exitY=1;exitDx=0;exitDy=0;
Exit from top of source:           exitX=0.5;exitY=0;exitDx=0;exitDy=0;

Enter left side of target:         entryX=0;entryY=0.5;entryDx=0;entryDy=0;
Enter right of target:             entryX=1;entryY=0.5;entryDx=0;entryDy=0;
Enter top of target:               entryX=0.5;entryY=0;entryDx=0;entryDy=0;
Enter bottom of target:            entryX=0.5;entryY=1;entryDx=0;entryDy=0;
```

`exitX` / `entryX` and `exitY` / `entryY` are **fractions** of the shape's width/height:
- `0` = left/top edge
- `0.5` = middle
- `1` = right/bottom edge

For **pipeline (LR) diagrams** always set:
```
exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
```
This forces all edges to exit right and enter left, giving a clean horizontal flow.

For **vertical flowcharts** use top/bottom:
```
exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;
```

---

## 5. Waypoints (force a specific bend)

When orthogonal routing picks a wrong path, add explicit waypoints:

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;..." edge="1"
        parent="1" source="api" target="db">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="500" y="200"/>
      <mxPoint x="500" y="400"/>
    </Array>
  </mxGeometry>
</mxCell>
```

Waypoints are in **canvas coordinates** (not relative to parent). Use sparingly —
prefer adjusting exit/entry sides first.

---

## 6. Edge labels

Edge labels are child `mxCell` elements with their own `mxGeometry` using a
**fractional position along the edge** (`x`) and a **perpendicular offset** (`y`):

```xml
<mxCell id="e1_label" value="HTTP/JSON" style="edgeLabel;html=1;align=center;..."
        vertex="1" connectable="0" parent="e1">
  <mxGeometry x="-0.1" y="0" relative="1" as="geometry">
    <mxPoint as="offset"/>
  </mxGeometry>
</mxCell>
```

- `x` is `[-1.0, 1.0]` where `-1` is the source end, `0` is the midpoint, `1` is the target end
- `y` is the perpendicular offset in pixels from the edge line

**Tip:** for cleaner labels, put them inline in the edge `value` attribute instead of as
child cells:

```xml
<mxCell id="e1" value="HTTP/JSON" style="..." edge="1" source="api" target="db">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Use the child-cell pattern only when you need multiple labels per edge or precise
positioning.

---

## 7. Avoiding crossings — the routing heuristic

When you have a dense diagram, follow this order:

1. **Place shapes on a grid** (see `gestalt-rules.md` Rule 3). Aligned shapes
   produce aligned edges.
2. **Force flow direction** with `exitX/entryX` on every edge — do not let draw.io
   auto-pick sides.
3. **Group related edges** — if 3 edges all go from layer-A shapes to layer-B
   shapes, exit them all from the same side at evenly spaced `exitY` values.
4. **Use a "bus" pattern** when a hub talks to many spokes: route all edges
   through a shared waypoint, then fan out.
5. **Add waypoints** only if 1-4 don't produce a clean result.

---

## 8. Edge colors and weights — semantic mapping

Use color and weight to encode meaning, not decoration:

| Semantic | Style fragment |
|---|---|
| Synchronous call (default) | `strokeColor=#424242;strokeWidth=1.5;` |
| Async / event | `dashed=1;strokeColor=#1565C0;strokeWidth=1.5;` |
| Critical path | `strokeColor=#C62828;strokeWidth=2.5;` |
| Read-only / inspection | `strokeColor=#9E9E9E;strokeWidth=1;` |
| Auth / identity | `dashed=1;dashPattern=8 4;strokeColor=#6A1B9A;strokeWidth=1.5;` |
| Data flow | `strokeColor=#2E7D32;strokeWidth=2;` |

Always include a legend on the diagram if you use more than 2 edge styles.

---

## 9. Sequence-diagram messages (special case)

Sequence diagrams use **horizontal** edges between lifelines. The pattern:

```
Lifeline A: vertical dashed line at fixed x
Lifeline B: vertical dashed line at fixed x

Message edge: source on A's lifeline, target on B's lifeline,
              exitX=0.5;exitY=0;entryX=0.5;entryY=0;
              with explicit waypoints at the message's y coordinate
```

See `templates/sequence.drawio` for a worked example.

---

## 10. Retry contract — `_route_with_retry` (route-edges.py)

`route-edges.py` calls `_route_with_retry(p1, p2, blocker_aabbs, max_iter=4)`
for every edge that has at least one blocking shape on its straight-line path.

**Algorithm:**

1. First pass: walk blocker list in path order; insert one `_shortest_detour`
   waypoint per blocker hit (same as the original single-pass logic).
2. Retry loop: walk every resulting sub-segment against the **full** blocker list.
   On any hit, insert one detour waypoint at that position and restart the walk.
3. Repeat until no sub-segment hits a blocker **or** `max_iter` extra waypoints
   have been inserted (whichever comes first).

**Bounds:**

| Parameter | Default | Meaning |
|---|---|---|
| `max_iter` | `4` | Maximum *additional* waypoints inserted during retry. Total waypoints for one edge ≤ `len(blockers) + 4`. |

**Fallback behavior:**

When `max_iter` is exhausted and blockers still remain, `_route_with_retry`
returns `exhausted=True`. `process_model` writes the best waypoint set found
so far (partial improvement) and emits **W110**:

```
WARN W110: edge '<label>' — detour did not fully clear all blockers
           after N waypoint(s) (diagram may be too dense — consider auto_layout=elk)
```

The edge is counted in the `routing.retries_used` summary statistic printed by
`route-edges.py` at the end of each run:

```
route-edges: fixed 7 edge(s), routing.retries_used=3, 1 partially blocked (see W110 warnings above) → diagram.drawio
```

**W110 semantics:** the edge *is* written (with partial detour); only a
subsequent `auto_layout=elk` pass can guarantee full clearance for pathologically
dense diagrams.

---

## 11. Common edge bugs

| Bug | Cause | Fix |
|---|---|---|
| Edge missing on Lucidchart import | Self-closing `<mxCell .../>` for edge | Add `<mxGeometry relative="1" as="geometry"/>` child element |
| Edge endpoint floats (not attached to a shape) | `source=` or `target=` references non-existent id | Verify ids; run `scripts/validate.py` |
| Edge clipped by container boundary | Edge `parent` is wrong (not lowest common ancestor) | Set `parent` to LCA — see `container-coords.md` |
| Edge crosses an icon glyph | All in one layer; edge draws over | Use two-layer rendering (Section 1) |
| Edge takes a weird L-shape | Auto-picked entry/exit sides | Force `exitX/entryX` explicitly |
| Edge label far from the edge | Default label position (midpoint) overlaps another shape | Adjust label's `x` to slide along the edge, or `y` to offset perpendicular |
