# Legend Block Pattern

## When to include a legend

Include a legend container when **either** condition is true:

1. **≥ 2 distinct edge semantic types** — different stroke color, dash pattern, or arrowhead
   meaning (e.g. solid blue = API call, dashed red = auth gap, dotted grey = async/planned).
2. **≥ 3 vendor namespaces** — diagram mixes shapes from 3+ of `mxgraph.aws4.*`,
   `mxgraph.azure2.*`, `mxgraph.gcp2.*`, or other vendor prefixes.

A legend is optional (but recommended) when only one condition is borderline (e.g. exactly
2 edge types that are visually obvious from context).

Do **not** add a legend for single-edge-style diagrams with one vendor — it adds visual noise.

---

## Layout rules

| Property | Value |
|---|---|
| Default position | Top-right corner of canvas, or bottom-left if top-right is crowded |
| Width | 220 px (fixed) |
| Height | auto — 28 px title + 22 px per entry |
| Min entries | 1 |
| Max entries | 8 (split into two columns if >8) |
| Container style | `legend_container` (see style-dictionary.md) |
| Title style | `legend_title` |
| Entry label style | `legend_entry` |

The legend must not overlap any diagram content. Place it ≥ 40 px from the nearest shape
or container edge. It is a **floating** container — `parent="1"`, not inside any swimlane.

---

## Entry anatomy

Each entry consists of two sibling cells inside the legend container:

1. **Swatch** — a short line (for edges) or a 24×24 icon (for vendor shapes), using the
   actual style from the diagram. Swatches are positioned at `x=12, y=<row>`.
2. **Label** — `legend_entry` text cell at `x=60, y=<row>`, width=150 px, height=20 px.

Row height = 22 px; first entry starts at `y=32` (after the 28 px title row).

### Edge swatches

| Style name | Style string |
|---|---|
| `legend_swatch_solid` | `endArrow=block;endFill=1;edgeStyle=orthogonalEdgeStyle;strokeColor=<color>;` |
| `legend_swatch_dashed` | `endArrow=block;endFill=0;dashed=1;strokeColor=<color>;` |
| `legend_swatch_dotted` | `endArrow=open;dashed=1;dashPattern=1 4;strokeColor=<color>;` |

Width=40, height=0 for all swatch edges (horizontal sample line).

### Vendor icon swatches

Use the same `shape=mxgraph.<vendor>.<name>` style as the diagram but constrain to
`width=24;height=24`. No label. Place at `x=12, y=<row>+(-1)` (vertically centered in row).

---

## Worked XML example

Legend container with 3 entries: solid edge, dashed edge, AWS icon.

```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>

    <mxCell id="leg_c" value="Legend"
      style="swimlane;startSize=28;fillColor=#F5F5F5;strokeColor=#BDBDBD;
             fontStyle=1;fontSize=12;fontColor=#212121;
             rounded=1;arcSize=4;"
      vertex="1" parent="1">
      <mxGeometry x="900" y="40" width="220" height="100" as="geometry"/>
    </mxCell>

    <mxCell id="leg_e1" value=""
      style="endArrow=block;endFill=1;edgeStyle=orthogonalEdgeStyle;
             strokeColor=#1565C0;strokeWidth=2;"
      edge="1" parent="leg_c" source="" target="">
      <mxGeometry x="12" y="50" width="40" height="0" relative="1" as="geometry">
        <Array as="points"/>
      </mxGeometry>
    </mxCell>
    <mxCell id="leg_l1" value="API call"
      style="text;html=1;fontSize=10;fontColor=#212121;align=left;"
      vertex="1" parent="leg_c">
      <mxGeometry x="60" y="40" width="150" height="20" as="geometry"/>
    </mxCell>

    <mxCell id="leg_e2" value=""
      style="endArrow=block;endFill=0;dashed=1;strokeColor=#C62828;strokeWidth=1;"
      edge="1" parent="leg_c" source="" target="">
      <mxGeometry x="12" y="72" width="40" height="0" relative="1" as="geometry">
        <Array as="points"/>
      </mxGeometry>
    </mxCell>
    <mxCell id="leg_l2" value="Auth gap (remediation)"
      style="text;html=1;fontSize=10;fontColor=#212121;align=left;"
      vertex="1" parent="leg_c">
      <mxGeometry x="60" y="62" width="150" height="20" as="geometry"/>
    </mxCell>

    <mxCell id="leg_ic1" value=""
      style="shape=mxgraph.aws4.ec2;fillColor=#FF9900;strokeColor=#232F3E;
             width=24;height=24;"
      vertex="1" parent="leg_c">
      <mxGeometry x="12" y="84" width="24" height="24" as="geometry"/>
    </mxCell>
    <mxCell id="leg_l3" value="EC2 instance"
      style="text;html=1;fontSize=10;fontColor=#212121;align=left;"
      vertex="1" parent="leg_c">
      <mxGeometry x="60" y="84" width="150" height="20" as="geometry"/>
    </mxCell>

  </root>
</mxGraphModel>
```

---

## LLM checklist before emitting

- [ ] Legend `id` contains the string `legend` (lowercase) so W122 can detect it
- [ ] Every edge style in the diagram has exactly one legend entry
- [ ] No orphan legend entries (entry with no matching edge in diagram)
- [ ] Legend container does not overlap any diagram shape (≥40 px gap)
- [ ] Legend parent is `"1"` (canvas root), not inside a swimlane
- [ ] Swatch edges have empty `source=""` and `target=""` — they are decoration only
