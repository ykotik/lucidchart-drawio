# Layout Engines (F5)

The skill normally relies on the LLM to assign coordinates from named templates and grid heuristics. For complex diagrams where edges still cross or shapes don't align cleanly, run the diagram through a layout engine after emission.

Controlled by the `auto_layout` feature flag in SKILL.md frontmatter:
`off` / `elk` / `dot` / `auto`. **Default: `auto`** — runs ELK only when the diagram has >20 vertices (threshold configurable via `--auto-threshold N`).

| Value | Behavior |
|---|---|
| `off` | Never run a layout engine. Use LLM coords as-is. |
| `elk` | Always run ELK Layered. |
| `dot` | Always run Graphviz dot (no nested container support). |
| `auto` (default) | Count vertices; if `> 20`, run ELK. Otherwise no-op — small diagrams usually have clean LLM coords. |

## When to use

- Diagram has >20 shapes (the `auto` default triggers automatically)
- Validator's `Q401` (edge crossings) fires on a smaller diagram → override with `--features auto_layout=elk`
- Container nesting >2 levels deep — LLM coord math degrades fast
- You're regenerating a diagram with new content but the same logical graph

Do NOT use for sequence diagrams (lifelines must stay vertical at fixed columns), grid-matrix (cells are positional by design), or BPMN (lane assignment is semantic, not layout). For these, set `auto_layout=off` per-diagram.

## Engines

### ELK Layered (`auto_layout=elk` — recommended)

Eclipse Layout Kernel. **Validated against** eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html:

> "This implementation supports different routing styles (straight, orthogonal, splines); if orthogonal routing is selected, arbitrary port constraints are respected... full layout of compound graphs with cross-hierarchy edges is supported when the respective option is activated on the top level."

Options the script sets:

| ELK option | Value | Reason |
|---|---|---|
| `elk.algorithm` | `layered` | Sugiyama-style hierarchical layout |
| `elk.direction` | `RIGHT` (default) / `DOWN` / `LEFT` / `UP` | Per-pattern flow |
| `elk.layered.nodePlacement.strategy` | `BRANDES_KOEPF` | ELK default, the "straight long edges" placement |
| `elk.layered.nodePlacement.bk.edgeStraightening` | `IMPROVE_STRAIGHTNESS` | ELK default; trades width for fewer bends |
| `elk.edgeRouting` | `ORTHOGONAL` | Right-angle edges — what architecture diagrams use |
| `elk.hierarchyHandling` | `INCLUDE_CHILDREN` | Lay out nested containers as one graph |
| `elk.spacing.nodeNode` | `60` | Comfortable gutter for 160×64 shapes |
| `elk.layered.spacing.nodeNodeBetweenLayers` | `80` | Between Sugiyama layers |
| `elk.spacing.edgeNode` | `20` | Keep edges off shape edges |
| `elk.spacing.edgeEdge` | `16` | Avoid parallel edge bundling |

**Runtime:** Node.js (`npx -y elkjs`) — the script auto-installs elkjs on first run via `npx`.

**Direction guide per pattern:**

| Pattern | `--direction` |
|---|---|
| hub-radial | `DOWN` (hub at top) |
| pipeline | `RIGHT` (sources → consumers) |
| swimlanes | `RIGHT` (within each lane) |
| c4-container | `DOWN` (front-end → middle → data) |
| flowchart-dag | `DOWN` |
| tree-hierarchy | `DOWN` |

### Graphviz `dot` (`auto_layout=dot` — fallback)

Used when Node.js / npx is not available. Older engine, output is functional but less polished. Does NOT handle nested containers — child shapes get flattened. Use only when ELK is unavailable.

**Runtime:** `brew install graphviz` (macOS) / `apt install graphviz` (Linux).

## Usage

```bash
# Default — ELK layered, left-to-right
python3 scripts/elk-layout.py path/to/diagram.drawio

# Custom direction for a flowchart
python3 scripts/elk-layout.py flowchart-dag.drawio --direction DOWN

# Graphviz fallback
python3 scripts/elk-layout.py pipeline.drawio --engine dot

# Specify output path
python3 scripts/elk-layout.py in.drawio out.drawio

# No-op (turn off via feature flag)
python3 scripts/elk-layout.py diagram.drawio --features auto_layout=off
```

Default output path: `<input-stem>.laid-out.drawio` — the source is never overwritten.

## What the script does

1. Parses the input `.drawio`.
2. Walks all `mxCell` vertex / edge entries → builds an ELK JSON graph that preserves container nesting (each container becomes an ELK compound node with its own `children` array).
3. Pipes the graph through `npx elkjs` (or `dot`).
4. Reads back the laid-out node coordinates.
5. Writes new `x` / `y` / `width` / `height` into the original `mxGeometry` elements.
6. Saves to `<output>.drawio`.

Container-relative coordinates are preserved automatically — ELK reports each node's position relative to its parent container, which matches mxGraph's convention exactly.

## Caveats

- **Vendor icons:** ELK uses the cell's `width`/`height` from the source `.drawio`. If you import shapes without geometry (e.g., from a vendor sidebar drag), the layout may treat them as default 160×64.
- **Edges with waypoints:** ELK computes its own waypoints and writes them into the output. Pre-existing waypoints in the source are overwritten.
- **Labels:** ELK doesn't move edge labels. If you have label positioning issues post-layout, re-run the skill's standard edge-label step.
- **Validation:** After running ELK, **re-run `scripts/validate.py`** to confirm `Q401` (crossings) and `Q402` (orthogonality) improved.
