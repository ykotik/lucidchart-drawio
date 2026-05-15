# draw.io mxGraph XML Schema Reference

## Document skeleton

```xml
<mxfile host="app.diagrams.net" type="device" version="24.0.0">
  <diagram name="Page Title" id="unique-id">
    <mxGraphModel dx="1600" dy="900" grid="1" gridSize="24" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="900" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- shapes and edges here, parent="1" for top-level -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## mxGraphModel key attributes

| Attribute | Description | Typical value |
|---|---|---|
| `gridSize` | Snap grid (use 24 for 24px grid) | 24 |
| `pageWidth/Height` | Canvas size in px | 1600×900 or 1600×1040 |
| `adaptiveColors` | Auto dark-mode color inversion | `"auto"` |

## mxCell shape

```xml
<mxCell id="s1" value="Label" style="..." vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="160" height="64" as="geometry"/>
</mxCell>
```

| Attribute | Notes |
|---|---|
| `id` | Unique string, never reuse |
| `value` | Label text; HTML allowed when style has `html=1` |
| `style` | Semicolon-separated key=value pairs |
| `vertex="1"` | Required for shapes |
| `parent` | `"1"` for top-level; container `id` for children |

## mxCell edge — CRITICAL

```xml
<mxCell id="e1" value="label" style="edgeStyle=orthogonalEdgeStyle;..."
        edge="1" source="s1" target="s2" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

**Never self-close edge cells.** Always include the `<mxGeometry>` child.

### Edge with waypoints

```xml
<mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="a" target="b" parent="1">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="300" y="150"/>
      <mxPoint x="300" y="250"/>
    </Array>
  </mxGeometry>
</mxCell>
```

## Container (swimlane)

```xml
<mxCell id="c1" value="Container Title" style="swimlane;startSize=26;..." vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="500" height="400" as="geometry"/>
</mxCell>
<!-- child uses relative coords + parent="c1" -->
<mxCell id="c1_child" value="Child" style="rounded=1;..." vertex="1" parent="c1">
  <mxGeometry x="20" y="40" width="160" height="64" as="geometry"/>
</mxCell>
```

## Geometry rules

- Children coordinates are **relative to the container's top-left**, offset by `startSize` (the header height)
- `startSize=26` means content area starts at y=26 inside the container
- Always align to grid (multiples of 24): x=24, 48, 72 …
- Minimum node spacing: 48px; preferred: 120px horizontal, 96px vertical

## Layers

Additional layers: `<mxCell id="L2" value="Layer Name" parent="0"/>` — assign shapes to layer with `parent="L2"`.

## Style property quick-ref

### Shape
```
rounded=1;whiteSpace=wrap;html=1;
fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=11;
```

### Swimlane container
```
swimlane;startSize=26;dashed=1;strokeColor=#2E7D32;strokeWidth=2;
fillColor=none;fontColor=#2E7D32;fontSize=12;fontStyle=1;
```

### Cylinder (database)
```
shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;
```

### Ellipse (actor)
```
ellipse;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1565C0;
```

### Edge styles
```
edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
```

Bidirectional: add `startArrow=classic;startFill=1;endArrow=classic;endFill=1;`
Dashed: add `dashed=1;`
Colored: add `strokeColor=#2E7D32;strokeWidth=2;`

## fontStyle values
- 0 = normal, 1 = bold, 2 = italic, 3 = bold+italic
