# workflow-deep.md — Full pipeline steps by profile

Read this file when you need the step-by-step detail for a given profile. The profile selector in SKILL.md tells you which profile to run; come here for the exact commands and sub-steps.

---

## Profile: production (default)

All features on. Use for client deliverables, team documentation, regulated diagrams.

```yaml
output_mode: auto
quality_gate: on
grounding_manifest: on
auto_layout: auto
text_metrics: auto
font_fit: auto
edge_routing: auto
```

~93K tokens · ~80–180 s end-to-end for a 50–60 element diagram.

### Production pipeline

**Step 1. PLAN (JSON, in scratchpad)**

- List containers, shapes, edges with parent IDs + grid cell assignments
- Validate: every shape's parent exists; no two shapes share a grid cell; every edge endpoint is a valid id

**Step 1.2. CORRIDOR PLANNING** (when `edge_routing != off` AND edges > 15)

- Read `references/routing-corridors.md`
- Add `corridors[]` array to plan: one horizontal band between each shape row, one vertical strip between each shape column — min 40 px wide/tall
- For any edge whose straight-line path crosses a non-endpoint shape, add `waypoints[]` routing it through the nearest corridor
- Re-validate: no corridor overlaps a shape AABB; corridors clear by >= 20 px

**Step 1.5. TEXT METRICS** (when `text_metrics != off`)

```bash
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
```

- For each shape/container where `text_safe.overflow == true`:
  - Set `width  = max(declared_width,  text_safe.min_width)`
  - Set `height = max(declared_height, text_safe.min_height)`
  - If swimlane: update `startSize = max(declared_startSize, text_safe.min_startSize)`
- Re-check grid collisions (nodes may have grown); adjust neighbours if needed
- Use `diagram.annotated.plan.json` as the plan going forward

**Step 2. EMIT XML**

- Read matching template from `templates/`
- Fill placeholders from plan; apply container-relative coordinates; wire two-layer edges

**Step 3. SELF-CHECK** (run pre-flight checklist — see SKILL.md)

**Step 4. WRITE file** with the Write tool

**Step 5. VALIDATE**

```bash
python3 scripts/validate.py <file>.drawio
```

Expect 0 E0xx errors, G503 100% cited.

**Step 6. OVERLAP REMOVAL** (mandatory for dense/complex diagrams)

```bash
python3 scripts/elk-layout.py <file>.drawio --engine neato
```

**Step 6.5. EDGE ROUTING** (when `edge_routing != off`)

```bash
python3 scripts/route-edges.py <file>.drawio
```

Inserts waypoints around any shapes that edges still intersect post-ELK. Then re-run validate to confirm Q401 crossings = 0.

**Step 7. FIT FONTS**

```bash
python3 scripts/fit-fonts.py <file>.drawio --mode auto
```

**Step 8. RE-VALIDATE**

```bash
python3 scripts/validate.py <file>.drawio
```

Confirm clean: 0 errors, W106/W107/W108 = 0.

---

## Profile: draft

For exploration and rough ideation. Skips grounding, text measurement, layout engine, and quality metrics. Produces structurally valid XML (correct parent IDs, container-relative coords, edge geometry) but without cite traceability, label-fit guarantees, or auto-layout.

**Switch back to production before any delivery.**

```yaml
output_mode: auto
quality_gate: off
grounding_manifest: off
auto_layout: off
text_metrics: off
font_fit: off
edge_routing: off
```

~58K tokens · ~50–110 s (~37% faster than production).

### Draft pipeline

**Step 1. READ 4 references** (skip `layout-engines.md`, `gestalt-rules.md`)

- `container-coords.md`
- `edge-routing.md`
- `plan-format.md`
- `style-dictionary.md`

**Step 2. PLAN** — JSON plan, no `cite` fields required

**Step 3. EMIT XML** — bare `<mxGraphModel>`, apply container-relative coords, two-layer edges

**Step 4. SELF-CHECK** (structural only)

| | Check |
|---|---|
| OK | Every edge has `<mxGeometry relative="1">` |
| OK | All IDs unique |
| OK | Every `parent=` exists |
| OK | Children use container-relative coordinates |
| OK | Cross-container edges have `parent = LCA` |
| OK | No XML comments inside model |
| OK | HTML in `value` is escaped |
| OK | `startSize` on all swimlane containers |
| OK | Edges in layer before icon layer |
| best-effort | Style allowlist |
| skipped | Font sizes / label fit (no `text_metrics`) |

**Step 5. WRITE file** with the Write tool

**Step 6. VALIDATE** structural errors only (E0xx) — no Q/G metrics

```bash
python3 scripts/validate.py <file>.drawio
```

---

## Profile: dense

Production pipeline plus forced ELK and grow-mode font fitting. Use when diagram has > 50 elements.

Enable via override comment on the first line of the source plan:

```
<!-- lucid:auto_layout=elk lucid:font_fit=grow -->
```

### Dense pipeline

Same as **production** (all steps 1–8) with these differences:

- **Step 6**: always run ELK regardless of vertex count (`--engine elk`, not `--engine neato`)
- **Step 7**: run `fit-fonts.py --mode grow` (expand cells before shrinking fonts, since ELK may have enlarged shapes)

```bash
python3 scripts/elk-layout.py <file>.drawio --engine elk
python3 scripts/fit-fonts.py <file>.drawio --mode grow
python3 scripts/validate.py <file>.drawio
```

---

## Grounding manifest (F3) — `grounding_manifest`

When `grounding_manifest: on` (default in production), **every** container, shape, and edge in the plan MUST include a non-empty `cite` field that traces the element to its source (file:line, doc:section, `user-stated`, `inferred from ...`, or `assumption:...`). The validator rejects any uncited entity with `G501`.

Goal: no hallucinated boxes on client deliverables. Every element on the diagram is traceable back to an artifact the user can verify.

Persist the plan next to the diagram as `<name>.plan.json` so `scripts/validate.py` auto-detects it (or pass `--plan path/to/plan.json` explicitly).

Disable per-diagram with `--features grounding_manifest=off` for sketchy exploration; turn back on before delivery.
