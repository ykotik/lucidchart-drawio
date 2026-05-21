# Gestalt Design Rules for draw.io Diagrams

## Rule 1: Flow direction — pick one, stick to it
- **Top-down (TB)**: hierarchy, org charts, dependency trees
- **Left-right (LR)**: pipelines, data flows, process sequences
- Never mix flow directions within a single diagram
- Place actors/sources at entry edge, consumers/outputs at exit edge

## Rule 2: Grouping and containers
- Use `swimlane` containers to show system boundaries, tenants, trust zones
- Max 2 levels of nesting (scope → group → shape); 3 levels only when unavoidable
- Name every container with a short, bold title (swimlane header)
- Same visual category = same container; don't group by accident (proximity creates implied grouping)

## Rule 3: Spacing and alignment
- Grid: 24px; all x/y coordinates = multiples of 24
- Minimum gap between shapes: 48px
- Preferred horizontal gap between columns: 120–240px
- Preferred vertical gap between rows: 72–96px
- Align shapes on the same row to identical y; same column to identical x
- Container padding: 24px from edge to first child

## Rule 4: Connectors
- Use `edgeStyle=orthogonalEdgeStyle` always (right-angle routing)
- One flow direction per diagram (all edges go TB or all go LR)
- Minimum straight segment before arrowhead: 20px (avoid arrowhead-on-bend artifacts)
- Avoid crossings; use waypoints to route around shapes if needed
- Max 3 edges entering or leaving a single shape before splitting into a sub-diagram

## Rule 5: Shape vocabulary — consistent semantic mapping
- **Rounded rect**: service / component / app
- **Cylinder** (`shape=cylinder3`): database / storage
- **Ellipse**: human actor / user role
- **Swimlane**: scope boundary / container / trust zone
- **Diamond** (`rhombus`): decision / branch point
- Don't use diamonds in architecture diagrams — use branching flows or separate lanes
- Keep shape vocabulary consistent within a diagram set

## Rule 6: Typography
- Diagram title: fontSize=14, fontStyle=1 (bold)
- Container header: fontSize=12, fontStyle=1
- Component label: fontSize=11
- Edge label: fontSize=10 (never smaller)
- Sub-labels (e.g. "⚠ Auth Gap"): fontSize=10, use HTML `&lt;br&gt;` for line breaks
- Never use fontSize < 10

## Rule 7: Color as semantic signal
- Green (#2E7D32): internal / owned / healthy
- Grey (#757575): neutral / vendor / external SaaS
- Purple (#512DA8): B2B partner / regulated external
- Red (#C62828): gap / risk / remediation needed
- Amber (#F9A825): milestone / planned / in-flight
- Blue (#1565C0): actor / user persona
- Do NOT use color decoratively — every color must carry meaning

## Rule 8: Hierarchy via visual weight
- Hero shape (1 per diagram): strokeWidth=3, larger (200–400px wide)
- Primary enablers: strokeWidth=2, medium size (160–240px wide)
- Standard components: strokeWidth=1.5, normal size (120–200px wide)
- Supporting/minor: strokeWidth=1, smaller (80–160px wide)

## Rule 9: Density and splitting
- Max 12 primary shapes per diagram page (excluding containers and legend)
- If > 12 shapes needed: split into A/B/C variants (different layout, same content)
- Prefer wider containers over taller ones for LR diagrams
- Use sub-groups inside containers when > 5 shapes share a sub-category

## Rule 10: Swimlane-specific rules
- Each lane = exactly one semantic category (trust zone, cadence, tenant, domain)
- Lanes run full-width; never leave gaps in lane rows
- Cross-boundary edges: route horizontally, enter/exit at lane perimeter
- Lane header size (startSize): 120–200px width for left headers on horizontal lanes (rows, horizontal=0); 24–30px height for top headers on vertical lanes (columns, horizontal=1).
- Don't put edges between shapes that share a lane through the lane boundary — keep them inside
