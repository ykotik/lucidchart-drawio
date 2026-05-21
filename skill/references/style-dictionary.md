# Style Dictionary

## Scope containers (CIAM dual-boundary style)

```
GREEN scope (FMI internal / primary org boundary):
  swimlane;startSize=26;dashed=1;strokeColor=#2E7D32;strokeWidth=2;
  fillColor=none;fontColor=#2E7D32;fontSize=12;fontStyle=1;

BLACK scope (vendor SaaS / external orgs):
  swimlane;startSize=26;dashed=1;strokeColor=#424242;strokeWidth=1.5;
  fillColor=none;fontColor=#424242;fontSize=12;fontStyle=1;

BLUE scope (cloud zone / AWS / Azure):
  swimlane;startSize=26;dashed=1;strokeColor=#1565C0;strokeWidth=2;
  fillColor=none;fontColor=#1565C0;fontSize=12;fontStyle=1;

ORANGE scope (regulated / EU sovereign):
  swimlane;startSize=26;dashed=1;strokeColor=#E65100;strokeWidth=2;
  fillColor=none;fontColor=#E65100;fontSize=12;fontStyle=1;

PURPLE scope (GxP / Part 11 validated zone):
  swimlane;startSize=26;dashed=1;strokeColor=#6A1B9A;strokeWidth=2;
  fillColor=none;fontColor=#6A1B9A;fontSize=12;fontStyle=1;

RED scope (security boundary / restricted):
  swimlane;startSize=26;dashed=1;strokeColor=#C62828;strokeWidth=1.5;
  fillColor=none;fontColor=#C62828;fontSize=12;fontStyle=1;
```

## DECOM (decommissioned system) styles

Decommissioned / retiring systems use **grey dashed** styling — never red.
Red is reserved for active security boundaries and auth-gap warnings.

```
DECOM shape (grey dashed):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#9E9E9E;
  strokeWidth=1.5;fontSize=11;dashed=1;fontColor=#757575;

DECOM edge (grey dashed):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;
  html=1;fontSize=10;dashed=1;strokeColor=#9E9E9E;fontColor=#757575;
```

Label convention: append `[DECOM]` suffix to the shape label.

## Component fill styles

```
HERO (primary system, e.g. S/4, Okta):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#2E7D32;strokeWidth=3;fontSize=13;fontStyle=1;

INTERNAL enabler (green fill):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=2;fontSize=12;fontStyle=1;

INTERNAL standard (lighter green):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#2E7D32;strokeWidth=1.5;fontSize=11;

VENDOR / SaaS (white, grey border):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;strokeWidth=1;fontSize=11;

EXTERNAL partner (purple tint):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#EDE7F6;strokeColor=#512DA8;strokeWidth=1;fontSize=11;

AUTH GAP (red warning):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#C62828;strokeWidth=1.5;fontSize=11;

MILESTONE / timeline note (amber):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF9C4;strokeColor=#F9A825;strokeWidth=1.5;fontSize=11;

DATABASE cylinder:
  shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#757575;strokeWidth=1;fontSize=11;

ACTOR ellipse:
  ellipse;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1565C0;fontSize=11;

TEXT label only:
  text;html=1;fontSize=11;fontStyle=1;
```

## Kafka / streaming diagram palette

```
KAFKA TOPIC (yellow/orange):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;strokeWidth=1.5;fontSize=11;

SINK CONNECTOR (blue):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;strokeWidth=1.5;fontSize=11;

FLINK JOB (pink):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#FFE6F0;strokeColor=#CC3366;strokeWidth=1.5;fontSize=11;

DB TABLE / VIEW (light grey):
  rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#666666;strokeWidth=1;fontSize=11;

TENANT container:
  swimlane;startSize=24;dashed=0;strokeColor=#6C8EBF;strokeWidth=1.5;
  fillColor=#EFF5FF;fontColor=#1A237E;fontSize=11;fontStyle=1;

POSTGRES group:
  swimlane;startSize=22;dashed=0;strokeColor=#757575;strokeWidth=1;
  fillColor=#FAFAFA;fontSize=10;fontStyle=1;
```

## Edge styles

```
STANDARD flow:
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;

BIDIRECTIONAL (bi-dir):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
  startArrow=classic;startFill=1;endArrow=classic;endFill=1;

DASHED (async/optional):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
  dashed=1;

GREEN emphasis (primary data path):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
  strokeColor=#2E7D32;strokeWidth=2;

RED remediation (auth gap / warning path):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
  dashed=1;strokeColor=#C62828;

DASHED grey (future/planned):
  edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;fontSize=10;
  dashed=1;strokeColor=#757575;
```

## Legend snippet (reusable XML)

```xml
<mxCell id="leg_t" value="Legend" style="text;html=1;fontSize=11;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="20" y="20" width="60" height="20" as="geometry"/>
</mxCell>
<mxCell id="leg_g" value="FMI Internal" style="text;html=1;fontSize=10;fontColor=#2E7D32;" vertex="1" parent="1">
  <mxGeometry x="20" y="44" width="160" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg_b" value="Vendor / External" style="text;html=1;fontSize=10;fontColor=#424242;" vertex="1" parent="1">
  <mxGeometry x="20" y="64" width="160" height="16" as="geometry"/>
</mxCell>
<mxCell id="leg_r" value="Auth Gap (remediation)" style="text;html=1;fontSize=10;fontColor=#C62828;" vertex="1" parent="1">
  <mxGeometry x="20" y="84" width="160" height="16" as="geometry"/>
</mxCell>
```

## Color palette quick-ref

| Role | Fill | Stroke |
|---|---|---|
| FMI internal (green) | #E8F5E9 | #2E7D32 |
| Cloud zone (blue) | #E3F2FD | #1565C0 |
| Regulated / EU sovereign (orange) | #FFF3E0 | #E65100 |
| GxP / Part 11 validated (purple) | #F3E5F5 | #6A1B9A |
| Vendor SaaS | #FFFFFF | #757575 |
| External partner | #EDE7F6 | #512DA8 |
| Auth gap / restricted (red) | #FFEBEE | #C62828 |
| DECOM (grey dashed) | #FAFAFA | #9E9E9E |
| Milestone | #FFF9C4 | #F9A825 |
| Kafka topic | #FFF2CC | #D6B656 |
| Sink connector | #DAE8FC | #6C8EBF |
| Flink job | #FFE6F0 | #CC3366 |
| DB table/view | #F5F5F5 | #666666 |
| Actor ellipse | #E3F2FD | #1565C0 |
| Tenant container | #EFF5FF | #6C8EBF |
