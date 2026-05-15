# Layout Patterns Reference

## Table of Contents
1. [Hub-Radial](#1-hub-radial)
2. [Scope-Columns (CIAM dual-boundary)](#2-scope-columns-ciam-dual-boundary)
3. [Horizontal Swimlanes](#3-horizontal-swimlanes)
4. [LR Data Pipeline](#4-lr-data-pipeline)
5. [Tenant-Namespace](#5-tenant-namespace)

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
