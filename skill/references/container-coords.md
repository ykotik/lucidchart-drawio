# Container-Relative Coordinates (THE #1 RULE)

> **The #1 source of swimlane / nested-container bugs from LLMs is using absolute
> canvas coordinates for children of containers instead of coordinates relative to
> the container's top-left corner.**

Every shape inside a `swimlane` container or `container=1` shape uses coordinates
**relative to the parent's top-left corner**, not absolute canvas coordinates.

---

## The coord rule, three levels deep

```
Canvas (parent="1")
├── Pool             parent="1"        x=40   y=40    w=1520  h=820     ← absolute (canvas coords)
│   ├── Lane A       parent="pool"     x=0    y=30    w=1520  h=260     ← relative to Pool
│   │   ├── Shape1   parent="lane_a"   x=40   y=40    w=160   h=64      ← relative to Lane A
│   │   └── Shape2   parent="lane_a"   x=220  y=40    w=160   h=64      ← relative to Lane A
│   └── Lane B       parent="pool"     x=0    y=290   w=1520  h=260     ← relative to Pool
│       └── Shape3   parent="lane_b"   x=40   y=40    w=160   h=64      ← relative to Lane B
└── (other top-level shapes use canvas coords with parent="1")
```

In XML:

```xml
<mxCell id="pool" value="Pool" style="swimlane;startSize=30;..." vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="1520" height="820" as="geometry"/>
</mxCell>

<mxCell id="lane_a" value="Lane A" style="swimlane;startSize=30;..." vertex="1" parent="pool">
  <mxGeometry x="0" y="30" width="1520" height="260" as="geometry"/>
</mxCell>

<mxCell id="shape1" value="API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="lane_a">
  <mxGeometry x="40" y="40" width="160" height="64" as="geometry"/>
</mxCell>
```

Note: `lane_a` has `y=30` because the Pool's `startSize=30` reserves the top 30px
for the Pool's header label. The first lane starts at `y=30`, not `y=0`.

---

## The `startSize` rule

Every container reserves a strip for its own header label. The size of that strip is
the `startSize` value in its style:

| Header position | Style fragment | Reserved area | First child starts at |
|---|---|---|---|
| Top (horizontal swimlane) | `horizontal=1;startSize=30` | top 30px | `y=30` |
| Left (vertical swimlane) | `horizontal=0;startSize=120` | left 120px | `x=120` |

**Default for `swimlane` is `horizontal=1` (top header) with `startSize=20`** — always
set `startSize` explicitly so you remember the offset.

---

## Cross-container edges (the second-most-common bug)

An edge that connects two shapes in **different** containers must have its `parent`
attribute set to the **lowest common ancestor**, not to `"1"`.

```
Pool (id=pool)
├── Lane A
│   └── Shape1 (id=shape1)
└── Lane B
    └── Shape2 (id=shape2)

Edge Shape1 → Shape2 :  parent="pool"  (lowest common ancestor)
                       source="shape1"
                       target="shape2"
```

If you set `parent="1"` on a cross-lane edge, draw.io will:
- still render the edge between the two shapes correctly **in the editor**,
- but the edge may be **clipped** by the pool's bounding box on import to Lucidchart, and
- the edge's coordinates will be interpreted as canvas-absolute on round-trips,
  causing drift if the pool is moved.

**Rule:** the edge's `parent` is the deepest container that contains both endpoints.

| Endpoints | parent of edge |
|---|---|
| Two shapes in the same lane | the lane id |
| Two shapes in different lanes of the same pool | the pool id |
| Two shapes in different pools | `"1"` (canvas) |
| One shape in a pool, one outside any container | `"1"` (canvas) |

---

## Worked example — converting absolute to relative

You want shape `API` at canvas position `(280, 110)` and the pool starts at `(40, 40)`
with `startSize=30`, lane A is the first lane (y=30 inside pool, height 260).

```
Pool canvas top-left:          (40, 40)
Lane A canvas top-left:        (40, 70)        ← pool y + pool startSize
Lane A's interior top-left:    (40, 70)        ← same as Lane A's top-left for horizontal
Shape canvas target:           (280, 110)
Shape relative to Lane A:      (240, 40)       ← 280 - 40, 110 - 70
```

So in XML:

```xml
<mxCell id="api" parent="lane_a" ...>
  <mxGeometry x="240" y="40" width="160" height="64" as="geometry"/>
</mxCell>
```

---

## Nested containers (e.g. tenant > namespace > service)

The rule recurses. Each level uses coords relative to its **immediate** parent:

```
Pool (parent="1", x=40, y=40)
└── Tenant container (parent="pool", x=20, y=30, w=600, h=400)
    └── Namespace (parent="tenant", x=20, y=30, w=560, h=200)
        └── Service shape (parent="namespace", x=20, y=20, w=160, h=64)
```

Canvas position of the Service shape: `40+20+20+20 = 100, 40+30+30+20 = 120`. You
don't need to compute this manually — draw.io renders it correctly as long as each
mxGeometry uses coords relative to its parent.

---

## Anti-patterns to recognize

| Anti-pattern | Why it's broken | Fix |
|---|---|---|
| `parent="1"` on a shape that visually sits inside a container | Shape ignores container; floats independently when container moves | Set `parent="<container-id>"` and convert coords to relative |
| `parent="<container-id>"` but coords are still canvas-absolute (e.g. x=320) | Shape appears far outside the container | Subtract container's canvas position from shape's canvas position |
| `parent="1"` on edge between two lane-shapes | Edge clipped on import / drifts on container move | Use lowest common ancestor as edge parent |
| `startSize=30` on container but first child at `y=0` | Child overlaps the container's title strip | For `horizontal=1` (top header), `y >= startSize`. For `horizontal=0` (left header), `x >= startSize`. |
| Container without `startSize` set | Defaults to `startSize=20`; layout assumes more | Always set `startSize` explicitly |
| Hub-radial center shape overlaps quadrants | Hub shape is larger than the gap between surrounding containers | Ensure gap `width >= hub width` and gap `height >= hub height`. |

---

## Checklist before emitting XML

1. For each shape: is its `parent` the visual container it sits in? (not always `"1"`)
2. For each shape: are `x` and `y` relative to that parent's top-left? (not canvas-absolute)
3. For each container: does the first child clear the `startSize` header strip?
4. For each edge: is `parent` the lowest common ancestor of source and target?
5. For each container: do all children fit within the container's `width` and `height`?
