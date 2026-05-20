# Layout Patterns Reference

## Table of Contents
1. [Hub-Radial](#1-hub-radial)
2. [Scope-Columns (CIAM dual-boundary)](#2-scope-columns-ciam-dual-boundary)
3. [Horizontal Swimlanes](#3-horizontal-swimlanes)
4. [LR Data Pipeline](#4-lr-data-pipeline)
5. [Tenant-Namespace](#5-tenant-namespace)
6. [C4 Context (L1)](#6-c4-context-l1)
7. [C4 Container (L2)](#7-c4-container-l2)
8. [C4 Component (L3)](#8-c4-component-l3)
9. [ERD Crow's Foot](#9-erd-crows-foot)
10. [UML Class](#10-uml-class)
11. [Sequence Diagram](#11-sequence-diagram)
12. [Tree / Hierarchy](#12-tree--hierarchy)
13. [Flowchart DAG](#13-flowchart-dag)
14. [BPMN Process](#14-bpmn-process)
15. [Grid Matrix](#15-grid-matrix)

---

## 1. Hub-Radial

**Use when**: One central system connects to N satellite systems; emphasizing hub-spoke topology.
**Flow**: Top-down or radial; hub at top-center or center.
**Examples**: Workato iPaaS hub, Okta IdP hub, API gateway.

### Coordinate guide (1600×900 canvas)
```
Hub:        x=680, y=80,  w=240, h=80     (center-top)
Left pods:  x=80,  y=200..500 (spacing 120px)
Right pods: x=1160,y=200..500
Bottom:     x=400..1100, y=700
```

### Skeleton structure
```
[SCOPE container — full width]
  [HUB hero shape — center, full width of content area]
  [Satellite group L — left cluster]
    [Sat 1..N — stacked vertically, 120px apart]
  [Satellite group R — right cluster]
    [Sat 1..N — stacked vertically]
  [Bottom consumers — horizontal row]
```

---

## 2. Scope-Columns (CIAM dual-boundary)

**Use when**: Two distinct ownership boundaries: FMI internal (green dashed) vs. vendor/external (black dashed).
**Flow**: Left-to-right reading; internal scope on left, external on right (or top/bottom).
**Examples**: ERP system context, identity zone overview, integration layer.

### Coordinate guide (1600×900 canvas)
```
Left scope (green):   x=40,  y=40, w=880, h=820
Right scope (black):  x=960, y=40, w=600, h=820
Margin between:       80px gap
```

### Inner zone columns (inside left scope)
```
Zone A: x=24+parent, y=40+parent, w=400, h=700
Zone B: x=452+parent, y=40+parent, w=400, h=700
```

### Standard shape grid inside zones
```
Row 1 hero:  y=40, h=72
Row 2:       y=144, h=64  (2 shapes side by side, w=180 each, gap=16)
Row 3:       y=240, h=64
Row 4:       y=336, h=64
```

---

## 3. Horizontal Swimlanes

**Use when**: Multiple parallel lanes by trust zone, cadence, or access tier.
**Flow**: Left-to-right within each lane; cross-boundary edges are vertical.
**Examples**: Trust zone tiers, integration cadence bands (real-time / batch), network zones.

### Coordinate guide (1600×1040 canvas)
```
Canvas: pageWidth=1600, pageHeight=1040
Lane height: 120–160px each
Lane x: 0 (full width)
Lane y: 0, 160, 320, 480, 640, 800, 960  (increments of 160)
Lane startSize (header): 120px (for left-side vertical labels)
```

### Lane header style
```
swimlane;startSize=120;horizontal=0;fillColor=#F5F5F5;strokeColor=#666666;
fontSize=11;fontStyle=1;
```

### Shapes inside lanes
```
Relative x: 40, 200, 380, 560, 740 … (180px spacing)
Relative y: 28 (centered in 80px content height)
w: 160, h: 64
```

---

## 4. LR Data Pipeline

**Use when**: Data flows left to right through processing stages: sources → transform/hub → consumers.
**Flow**: Strictly left-to-right; sources at x=0..200, hub at center, consumers at right.
**Examples**: Kafka streaming pipeline, ETL pipeline, integration middleware flow.

### Coordinate guide (1600×900 canvas)
```
Sources scope (left black):   x=24,  y=40, w=280, h=820
Integration scope (green):    x=344, y=40, w=560, h=820
Consumers scope (right black):x=944, y=40, w=620, h=820

Inside sources — shape groups (vertical stack):
  Group header: y=40+N*290, h=280
  Shapes: y=32, 112, 192 within group (80px rows)

Inside integration — hub shape:
  Hub: x=24, y=40, w=512, h=96
  Process group: x=24, y=168, w=512, h=250
  Core system: x=24, y=448, w=512, h=80
  Support row: x=24, y=560, w=240/240, h=64

Inside consumers — parallel groups (side-by-side):
  Left group: x=16, y=40, w=268, h=N*80
  Right group: x=316, y=40, w=268, h=N*80
```

### Edge routing in pipelines
- Source → Hub: exit right (exitX=1), enter left (entryX=0)
- Hub → Core: internal, vertical
- Core → Consumer: exit right (exitX=1), enter left (entryX=0)
- Add exitX/exitY and entryX/entryY on crossing scope boundaries

---

## 5. Tenant-Namespace

**Use when**: Multiple tenants or namespaces each contain the same component types (e.g., Kafka tenant per region/env).
**Flow**: Cross-tenant dashed edges; within-tenant solid edges, top-down.
**Examples**: Kafka multi-tenant, multi-cloud namespace, per-environment deployment.

### Coordinate guide (1600×900 canvas)
```
Global header shapes (top): y=40, w=200, h=80
Tenant 1 (left):   x=40,  y=160, w=280, h=700
Tenant 2 (center): x=360, y=160, w=680, h=700
Tenant 3 (right):  x=1080,y=160, w=480, h=700
```

### Tenant container style
```
swimlane;startSize=24;dashed=0;strokeColor=#6C8EBF;strokeWidth=1.5;
fillColor=#EFF5FF;fontColor=#1A237E;fontSize=11;fontStyle=1;
```

### Inner Kafka component grid (inside tenant)
```
Topics (yellow):     y=40, rows of 2 side by side, w=160, gap=24
Flink jobs (pink):   y below topics, staggered
Sinks (blue):        y below flink, aligned
DB tables (grey):    grouped in Postgres sub-container, bottom
```

### Cross-tenant edge style
```
edgeStyle=orthogonalEdgeStyle;dashed=1;rounded=0;jettySize=auto;
html=1;fontSize=10;strokeColor=#6C8EBF;
```

### Postgres sub-container (inside tenant)
```
swimlane;startSize=22;dashed=0;strokeColor=#757575;strokeWidth=1;
fillColor=#FAFAFA;fontSize=10;fontStyle=1;
```
Children: table shapes (w=140, h=40), arranged in 2×N grid inside Postgres container.

---

## 6. C4 Context (L1)

**Use when**: Showing the system in scope and the people/external systems it interacts with.
**Flow**: Hub-radial; system-in-scope sits center; people at top; external systems at bottom.
**Examples**: Initial slide for any architecture deck.

### Coordinate guide (1600×900 canvas)
```
Title strip:        x=40,  y=20,  w=1520, h=32
People row (top):   y=120, h=220, w=180   → x=200, 1220 (spread across width)
System hero:        x=640, y=380, w=320, h=180  (deep blue)
External systems:   y=640, h=140, w=280   → x=200, 660, 1120 (3-up row)
Legend:             x=40,  y=800, w=320, h=80
```

### Shape styles
```
Person (umlActor):  shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;fillColor=#08427B;strokeColor=#073B6F;fontColor=#FFFFFF;
System in scope:    rounded=0;fillColor=#1168BD;strokeColor=#0E5BA6;fontColor=#FFFFFF;
External system:    rounded=0;fillColor=#999999;strokeColor=#6C6C6C;fontColor=#FFFFFF;
Title prefix:       <b>Name</b><br/><span style="font-size:10px;">[Person|Software System|External System]</span><br/><br/>Description
```

### Edge styles
```
edgeStyle=orthogonalEdgeStyle;endArrow=block;fontSize=11;
exit/entry: pick sides explicitly per direction.
```

---

## 7. C4 Container (L2)

**Use when**: Drilling into a single C4 system to show its containers (apps, services, datastores).
**Flow**: System boundary (dashed) contains containers; external systems live outside.

### Coordinate guide (1600×900 canvas)
```
Title strip:        x=40,  y=20,  w=1520, h=32
User actor:         x=700, y=80,  w=180, h=160
System boundary:    x=80,  y=280, w=1440, h=440 (dashed, container=1)
  Container row 1:  y=60 (relative),  spacing 280px
  Container row 2:  y=260 (relative)
External systems:   y=780, h=80, w=240, 3-up
```

### Shape styles
```
Container (app/svc):  rounded=0;fillColor=#438DD5;strokeColor=#3C7FC0;fontColor=#FFFFFF;
Container (db):       shape=cylinder3;backgroundOutline=1;size=15;fillColor=#438DD5;strokeColor=#3C7FC0;fontColor=#FFFFFF;
System boundary:      rounded=0;fillColor=none;strokeColor=#0E5BA6;strokeWidth=2;dashed=1;container=1;collapsible=0;verticalAlign=top;align=left;spacingLeft=12;spacingTop=8;fontStyle=2;
```

### Edge styles
```
edgeStyle=orthogonalEdgeStyle;endArrow=block;fontSize=10;
Label: "[Protocol/Format]" e.g. "JSON/HTTPS", "SQL", "GET/SET"
```

---

## 8. C4 Component (L3)

**Use when**: Drilling into a single container to show its internal components.
**Flow**: Container boundary (dashed) contains components in a grid; database below.

### Coordinate guide (1600×900 canvas)
```
Container boundary: x=80,  y=100, w=1440, h=560 (dashed)
  Component row 1:  y=80  (controllers / entry points)
  Component row 2:  y=240 (services / business logic)
  Component row 3:  y=400 (repositories / data access)
  Width per cell:   260, spacing 60
External datastore: x=980, y=500, w=220, h=120 (cylinder, outside)
```

### Shape styles
```
Component:  rounded=0;fillColor=#85BBF0;strokeColor=#5D82A8;fontColor=#000000;
Datastore:  shape=cylinder3;backgroundOutline=1;size=15;fillColor=#438DD5;strokeColor=#3C7FC0;fontColor=#FFFFFF;
```

---

## 9. ERD Crow's Foot

**Use when**: Database schemas, entity relationships, data models.
**Flow**: Entities placed by relationship proximity; foreign keys connected via crow's-foot edges.

### Coordinate guide (1600×900 canvas)
```
Title strip:    x=40,  y=20,  w=1520, h=32
Entity width:   220-240
Entity height:  30 (header) + 22 * N (fields) + padding
Layout:         place by 1..* relationships — parent left/top, child right/bottom
Min gutter:     180px horizontal between entities (room for crow's-foot edges)
```

### Entity shape (table with 2 compartments)
```
Header: shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;
        fillColor=#E3F2FD;strokeColor=#1565C0;fontColor=#1565C0;fontStyle=1;
TableRow (fields container, parent=entity):
        shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;
        strokeColor=#1565C0;top=0;left=0;bottom=0;right=0;fillColor=none;
Field row (PK, FK, attribute):
        shape=partialRectangle;strokeColor=inherit;align=left;spacingLeft=8;fontSize=12;
        PK: fontStyle=4 (underline) + "PK  " prefix
        FK: fontStyle=2 (italic) + "FK  " prefix
        Field height: 22, PK header: 26
```

### Crow's-foot edge styles
```
1..*  : endArrow=ERmany;startArrow=ERone;
*..1  : endArrow=ERone;startArrow=ERmany;
0..1..* : endArrow=ERoneToMany;startArrow=ERzeroToOne;
edgeStyle=entityRelationEdgeStyle;rounded=0;exitX=1;exitY=0.5;entryX=0;entryY=0.5;
```

---

## 10. UML Class

**Use when**: Object-oriented design, domain models, class hierarchies.
**Flow**: Top-down inheritance; left-right composition.

### Coordinate guide (1600×900 canvas)
```
Title strip:       x=40,  y=20,  w=1520, h=32
Abstract/parent:   x=640, y=120, w=240, h=180 (centered top)
Concrete classes:  y=500, w=240, h=160, spaced 380px apart
Composition target: left or right of concrete class, w=200, h=120
```

### Class shape (3 compartments)
```
Header (startSize=30 for normal class, 44 for «abstract» stereotype):
  shape=table;container=1;collapsible=0;childLayout=tableLayout;fillColor=#FFFFFF;
  strokeColor=#424242;fontStyle=1;
Attributes compartment: shape=tableRow;horizontal=0;startSize=0;
Operations compartment: shape=tableRow;horizontal=0;startSize=0;
Field row: shape=partialRectangle;align=left;spacingLeft=8;fontSize=12;
  Visibility prefix: - (private), + (public), # (protected), ~ (package)
```

### Relationship edges
```
Inheritance:   endArrow=block;endFill=0;
Realization:   endArrow=block;endFill=0;dashed=1;
Composition:   endArrow=open;startArrow=diamondThin;startFill=1;startSize=14;
Aggregation:   endArrow=open;startArrow=diamondThin;startFill=0;startSize=14;
Association:   endArrow=open;
Dependency:    endArrow=open;dashed=1;
```

---

## 11. Sequence Diagram

**Use when**: Showing message ordering between participants over time.
**Flow**: Lifelines as vertical columns; time flows top-to-bottom.

### Coordinate guide (1600×900 canvas)
```
Title strip:    x=40,  y=20,  w=1520, h=32
Lifeline width: 120, height 700
Lifeline x:     160, 460, 760, 1060, 1360  (300px spacing, supports 5 lifelines)
Message y:      starts at y=160, increments of 60px per message
Activation bar: 16px wide, positioned at x=32 (centered on 80-wide lifeline base)
```

### Lifeline shape
```
shape=umlLifeline;perimeter=lifelinePerimeter;container=1;dropTarget=0;
collapsible=0;recursiveResize=0;outlineConnect=0;size=40;
strokeColor=#424242;fillColor=#FFFFFF;
```

### Message edges (free-floating, with explicit sourcePoint/targetPoint)
```
Sync call:    endArrow=block;rounded=0;edgeStyle=none;curved=0;
Sync return:  endArrow=open;dashed=1;endFill=0;endSize=8;edgeStyle=none;
Async:        endArrow=open;endFill=0;edgeStyle=none;
Self call:    add waypoints to U-shape: out right, down, back left at same x
```

Messages typically don't have `source=`/`target=` cell ids — use explicit
sourcePoint and targetPoint in the mxGeometry. This anchors the message at a
specific time on each lifeline.

---

## 12. Tree / Hierarchy

**Use when**: Org charts, taxonomies, decision trees, file structures.
**Flow**: Top-down, breadth-first by level.

### Coordinate guide (1600×900 canvas)
```
Title strip:       x=40,  y=20,  w=1520, h=32
Level 0 (root):    x=720, y=120, w=160, h=60 (centered)
Level 1:           y=280, w=180, h=56, spaced across width
Level 2:           y=440, w=160, h=50
Level 3:           y=600, w=160, h=44
Vertical gap:      160px between levels
```

### Node styles (by level)
```
Level 0 (root):   rounded=1;fillColor=#1565C0;strokeColor=#0D47A1;fontColor=#FFFFFF;fontStyle=1;fontSize=13;
Level 1:          rounded=1;fillColor=#1976D2;strokeColor=#0D47A1;fontColor=#FFFFFF;fontStyle=1;fontSize=12;
Level 2:          rounded=1;fillColor=#42A5F5;strokeColor=#1565C0;fontColor=#FFFFFF;fontSize=12;
Level 3+:         rounded=1;fillColor=#90CAF9;strokeColor=#1976D2;fontColor=#0D47A1;fontSize=11;
```

### Edge style
```
edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=none;strokeColor=#424242;
exitX=0.5;exitY=1;entryX=0.5;entryY=0;
```

Use `endArrow=none` for org charts; use `endArrow=block` for decision trees.

---

## 13. Flowchart DAG

**Use when**: Process flows with decision points, start/end, parallel branches.
**Flow**: Top-down primary; left/right for branches.

### Coordinate guide (1600×900 canvas)
```
Title strip:    x=40,  y=20,  w=1520, h=32
Start ellipse:  x=720, y=100, w=120, h=50 (centered)
Process boxes: w=160, h=60, vertical spacing 110px
Decision diamonds: w=160, h=100
Branches:       left/right at 240px offset from main column
End ellipses:   w=140-160, h=50-60
```

### Shape styles
```
Start (terminator):  ellipse;fillColor=#2E7D32;strokeColor=#1B5E20;fontColor=#FFFFFF;fontStyle=1;
Process:             rounded=1;fillColor=#E3F2FD;strokeColor=#1565C0;fontColor=#1565C0;
Decision:            rhombus;fillColor=#FFF8E1;strokeColor=#F57F17;fontColor=#F57F17;fontStyle=1;
End (success):       ellipse;fillColor=#2E7D32;strokeColor=#1B5E20;fontColor=#FFFFFF;fontStyle=1;
End (failure):       ellipse;fillColor=#C62828;strokeColor=#8B1A1A;fontColor=#FFFFFF;fontStyle=1;
Error/exception box: rounded=1;fillColor=#FFEBEE;strokeColor=#C62828;fontColor=#C62828;
```

### Edge styles
```
Normal flow:   edgeStyle=orthogonalEdgeStyle;endArrow=block;strokeColor=#424242;
Yes branch:    strokeColor=#2E7D32;fontColor=#2E7D32;fontStyle=1;  label="Yes"
No branch:     strokeColor=#C62828;fontColor=#C62828;fontStyle=1;  label="No"
```

---

## 14. BPMN Process

**Use when**: Business process modeling with pools, lanes, gateways, events.
**Flow**: Left-to-right within lanes; pool contains all lanes.

### Coordinate guide (1600×900 canvas)
```
Title strip:        x=40,  y=20,  w=1520, h=32
Pool:               x=60,  y=80,  w=1480, h=700  (horizontal=0 → left-title strip)
Lanes inside pool:  x=24 (relative), w=1456, h=200-240 each
Lane content row:   y=76 (relative to lane), shapes flow LR with 200px spacing
Events:             40×40 (circles)
Tasks:              140×60 (rounded rectangles with type icon)
Gateways:           60×60 (diamonds)
```

### Element styles
```
Start event:    shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=general;outline=standard;strokeColor=#2E7D32;
End event:      shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=general;outline=end;strokeColor=#2E7D32 or #C62828;
User task:      shape=mxgraph.bpmn.task;taskType=user;
Service task:   shape=mxgraph.bpmn.task;taskType=service;
Send task:      shape=mxgraph.bpmn.task;taskType=send;
Exclusive GW:   shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=exclusiveGw;
Parallel GW:    shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=parallelGw;
```

### Sequence flow edge
```
edgeStyle=orthogonalEdgeStyle;endArrow=block;endFill=1;strokeColor=#424242;
Gateway labels: "Yes" / "No" with strokeColor matching outcome
Edge parent: lane id if both endpoints in same lane; pool id if cross-lane
```

---

## 15. Grid Matrix

**Use when**: 2D classification — capability map, MoSCoW, BCG matrix, RACI.
**Flow**: No flow; cells are independent classifications.

### Coordinate guide (1600×900 canvas)
```
Title strip:        x=40,  y=20,  w=1520, h=32
Column headers:     y=100, h=50, w=200, spaced 220px starting x=320
Row headers:        x=100, h=180, w=200, spaced 200px starting y=170
Cell width:         200, cell height 180
Cell gap:           20px (cells should touch or have thin gutter)
Total grid:         5 cols × 3 rows fits 1600×900 with margins
```

### Cell styles by tier
```
Headers (col & row):  fillColor=#1565C0/#0D47A1;fontColor=#FFFFFF;fontStyle=1;rounded=0;
Tier 1 (strategic):   fillColor=#E3F2FD;strokeColor=#1565C0;fontColor=#0D47A1;
Tier 2 (operational): fillColor=#FFF8E1;strokeColor=#F57F17;fontColor=#5D4037;align=left;verticalAlign=top;spacingLeft=8;spacingTop=8;
Tier 3 (supporting):  fillColor=#E8F5E9;strokeColor=#2E7D32;fontColor=#1B5E20;
```

Cells are simple rectangles — no edges between them. Color encodes the row/tier.
