# UML / ERD / BPMN Shape Vocabulary

Generic notation systems supported natively by draw.io / mxGraph.

---

## UML Class diagram

A UML class is a 3-compartment rectangle: title, attributes, operations.

### Class shape (3 compartments)

```xml
<mxCell id="class_user" value="User" style="shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;fontSize=12;fillColor=#FFFFFF;strokeColor=#424242;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="220" height="160" as="geometry"/>
</mxCell>

<!-- attributes compartment -->
<mxCell id="class_user_attr" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;strokeColor=#424242;top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=#FFFFFF;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;" vertex="1" parent="class_user">
  <mxGeometry y="30" width="220" height="64" as="geometry"/>
</mxCell>

<mxCell id="class_user_attr_1" value="- id: UUID" style="shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=4;" vertex="1" parent="class_user_attr">
  <mxGeometry width="220" height="22" as="geometry"/>
</mxCell>

<mxCell id="class_user_attr_2" value="- email: String" style="shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=4;" vertex="1" parent="class_user_attr">
  <mxGeometry y="22" width="220" height="22" as="geometry"/>
</mxCell>

<!-- operations compartment -->
<mxCell id="class_user_ops" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;strokeColor=#424242;top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=#FFFFFF;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;" vertex="1" parent="class_user">
  <mxGeometry y="94" width="220" height="66" as="geometry"/>
</mxCell>

<mxCell id="class_user_op_1" value="+ login(): Token" style="shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=4;" vertex="1" parent="class_user_ops">
  <mxGeometry width="220" height="22" as="geometry"/>
</mxCell>
```

### Class relationships (edges)

| Relationship | Style fragment |
|---|---|
| Association | `endArrow=none;html=1;` |
| Directed association | `endArrow=open;html=1;` |
| Inheritance / generalization | `endArrow=block;endFill=0;html=1;` |
| Realization (implements) | `endArrow=block;endFill=0;dashed=1;html=1;` |
| Aggregation (open diamond) | `endArrow=open;startArrow=diamondThin;startFill=0;html=1;` |
| Composition (filled diamond) | `endArrow=open;startArrow=diamondThin;startFill=1;html=1;` |
| Dependency | `endArrow=open;dashed=1;html=1;` |

Edge multiplicity labels: put `1`, `*`, `0..1`, `1..*` etc. in the edge label.

---

## Entity-Relationship Diagram (crow's foot)

### Entity shape (with attributes)

Use the same `shape=table` pattern as UML class but typically 2 compartments (entity
name + attribute list):

```xml
<mxCell id="ent_customer" value="Customer" style="shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;fontSize=12;fillColor=#E3F2FD;strokeColor=#1565C0;fontColor=#1565C0;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="220" height="140" as="geometry"/>
</mxCell>

<mxCell id="ent_customer_fields" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;strokeColor=#1565C0;top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=none;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;" vertex="1" parent="ent_customer">
  <mxGeometry y="30" width="220" height="110" as="geometry"/>
</mxCell>

<mxCell id="ent_customer_pk" value="PK  customer_id" style="shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=4;fontStyle=4;" vertex="1" parent="ent_customer_fields">
  <mxGeometry width="220" height="22" as="geometry"/>
</mxCell>

<mxCell id="ent_customer_email" value="email" style="shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=4;" vertex="1" parent="ent_customer_fields">
  <mxGeometry y="22" width="220" height="22" as="geometry"/>
</mxCell>
```

Prefix `PK` (primary key) with `fontStyle=4` (underline). Prefix `FK` (foreign key)
with italics (`fontStyle=2`).

### Crow's-foot relationship edges

| Cardinality at end | endArrow= |
|---|---|
| Exactly one | `ERone` |
| Zero or one | `ERzeroToOne` |
| One or many | `ERoneToMany` |
| Zero or many | `ERzeroToMany` |
| Many | `ERmany` |

Same set works for `startArrow=` on the source end.

Edge style:
```
edgeStyle=entityRelationEdgeStyle;fontSize=12;html=1;endArrow=ERmany;startArrow=ERone;rounded=0;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;
```

---

## BPMN — Business Process Model and Notation

### Events (circles)

```
Start event:        ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=general;outline=standard;strokeColor=#2E7D32;fillColor=none;
Intermediate event: ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=general;outline=throwing;strokeColor=#1565C0;
End event:          ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=general;outline=end;strokeColor=#C62828;
Timer event:        ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=timer;outline=standard;strokeColor=#2E7D32;
Message event:      ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=message;outline=standard;strokeColor=#2E7D32;
Error event:        ellipse;html=1;shape=mxgraph.bpmn.shape;perimeter=ellipsePerimeter;symbol=error;outline=end;strokeColor=#C62828;
```

Size: 40×40

### Activities (rounded rectangles)

```
Task (basic):       rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#FFF;strokeColor=#424242;
User task:          shape=mxgraph.bpmn.task;taskType=user;html=1;strokeColor=#424242;fillColor=#FFF;
Service task:       shape=mxgraph.bpmn.task;taskType=service;html=1;strokeColor=#424242;fillColor=#FFF;
Script task:        shape=mxgraph.bpmn.task;taskType=script;html=1;strokeColor=#424242;fillColor=#FFF;
Send task:          shape=mxgraph.bpmn.task;taskType=send;html=1;strokeColor=#424242;fillColor=#FFF;
Receive task:       shape=mxgraph.bpmn.task;taskType=receive;html=1;strokeColor=#424242;fillColor=#FFF;
Manual task:        shape=mxgraph.bpmn.task;taskType=manual;html=1;strokeColor=#424242;fillColor=#FFF;
Business rule:      shape=mxgraph.bpmn.task;taskType=instantiating;html=1;strokeColor=#424242;fillColor=#FFF;
Subprocess:         shape=mxgraph.bpmn.shape;perimeter=rectanglePerimeter;symbol=general;outline=subProcess;
```

Size: 120×60 typical

### Gateways (diamonds)

```
Exclusive (XOR):    shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=exclusiveGw;
Parallel (AND):     shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=parallelGw;
Inclusive (OR):     shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=inclusiveGw;
Event-based:        shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=eventGw;
Complex:            shape=mxgraph.bpmn.shape;perimeter=rhombusPerimeter;symbol=complexGw;
```

Size: 60×60

### Flows (edges)

```
Sequence flow:      endArrow=block;endFill=1;html=1;
Message flow:       endArrow=open;startArrow=oval;startFill=0;dashed=1;html=1;
Association:        endArrow=open;dashed=1;html=1;
Data association:   endArrow=open;dashed=1;dashPattern=1 3;html=1;
```

### Pools & Lanes (BPMN containers)

Use standard `swimlane` style:
```
Pool:   swimlane;horizontal=0;startSize=20;fontSize=14;fontStyle=1;strokeColor=#424242;fillColor=#FAFAFA;
Lane:   swimlane;horizontal=0;startSize=20;fontSize=12;strokeColor=#424242;fillColor=none;
```

`horizontal=0` makes the title strip vertical (left-aligned) — the BPMN convention.
Use `horizontal=1` for top-title lanes when the diagram flows top-to-bottom.

### Data objects

```
Data object:        shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;darkOpacity=0.05;strokeColor=#424242;fillColor=#FFF;
Data store:         shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;strokeColor=#424242;fillColor=#FFF;
```

---

## Sequence diagram (UML)

### Lifeline (actor at top + dashed vertical line)

```xml
<mxCell id="ll_user" value="User" style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;dropTarget=0;collapsible=0;recursiveResize=0;outlineConnect=0;fontSize=12;strokeColor=#424242;fillColor=#FFF;size=30;" vertex="1" parent="1">
  <mxGeometry x="80" y="40" width="80" height="500" as="geometry"/>
</mxCell>
```

`size=30` is the height of the box at the top of the lifeline.

### Activation bar (vertical rectangle on lifeline)

```xml
<mxCell id="act_user_1" style="html=1;points=[[0,0,0,0,0],[1,0,0,0,0],[0,1,0,0,0],[1,1,0,0,0]];perimeter=orthogonalPerimeter;outlineConnect=0;targetShapes=umlLifeline;portConstraint=eastwest;newEdgeStyle={&quot;curved&quot;:0,&quot;rounded&quot;:0};fillColor=#FFFFFF;strokeColor=#424242;" vertex="1" parent="ll_user">
  <mxGeometry x="32" y="60" width="16" height="80" as="geometry"/>
</mxCell>
```

### Message (synchronous, sync return, async)

```
Sync call:     html=1;verticalAlign=bottom;endArrow=block;rounded=0;edgeStyle=none;curved=0;
Sync return:   html=1;verticalAlign=bottom;endArrow=open;dashed=1;endFill=0;endSize=8;rounded=0;edgeStyle=none;curved=0;
Async:         html=1;verticalAlign=bottom;endArrow=open;endFill=0;rounded=0;edgeStyle=none;curved=0;
Self call:     curved=0;edgeStyle=none;html=1;jumpStyle=arc;jumpSize=8;exitX=1;exitY=0.25;entryX=1;entryY=0.75;
```

Messages typically have explicit waypoints (or are direct horizontal lines between
two lifelines at a specific y).

---

## Common combinations

| Diagram type | Typical shapes |
|---|---|
| Class diagram | shape=table (3 compartments), block-arrow inheritance, open-diamond aggregation |
| Domain model | shape=table (2 compartments), no operations, association labels |
| ERD | shape=table (2 compartments, PK underlined), crow's-foot edges |
| BPMN happy path | start event → user task → exclusive GW → service task → end event |
| Sequence (request/response) | 2 lifelines, sync call edge, sync return dashed edge |
| State machine | rounded rect states, open-arrow transitions with guard labels |
