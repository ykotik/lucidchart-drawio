# Skill Feature Analysis — drawio-architect v2.1

**Date:** 2026-05-20  
**Scope:** 6 production feature flags + workflow step maps + engine comparison + skill comparison  
**Reference diagram size:** 50–60 elements (≈ 35 shapes + 5 containers + 30 edges)

> `diagram_eval` and `eval_harness` are CI-only tools, not per-diagram features.  
> They are excluded from this analysis and from all generation profiles.

---

## 1. Feature Catalogue

The skill exposes 6 independently togglable per-diagram features via YAML frontmatter in `skill/SKILL.md`. Each can be overridden per-diagram with `<!-- lucid:feature=value -->` or via `--features key=value` on CLI scripts.

| # | Flag | Values | Default | Ref doc |
|---|---|---|---|---|
| F1 | `output_mode` | `bare` / `wrapped` / `auto` | `auto` | SKILL.md §Output mode |
| F2 | `quality_gate` | `on` / `off` | `on` | `references/validator.md` §Q4xx |
| F3 | `grounding_manifest` | `on` / `off` | `on` | `references/plan-format.md` §F3 |
| F4 | `auto_layout` | `off` / `elk` / `dot` / `auto` | `auto` | `references/layout-engines.md` |
| F5 | `text_metrics` | `off` / `auto` | `auto` | `references/text-metrics.md` |
| F6 | `font_fit` | `off` / `auto` / `grow` | `auto` | `references/font-fit.md` |

---

## 2. Feature Evaluation Matrix

### Rating key

| Dimension | Scale | Notes |
|---|---|---|
| Impact | High / Medium / Low | Effect on diagram quality when enabled vs disabled |
| Complexity | High / Medium / Low | Conceptual + implementation complexity |
| Reliability | High / Medium / Low | How often it produces correct, predictable results |
| Weight | Light / Medium / Heavy | Runtime resource footprint (CPU, deps, wall time) |
| Token Δ | +N tokens | Additional LLM tokens consumed (input+output combined) |
| Exec time | ms / s | Wall-clock time added to the pipeline |
| Tool usage | List | Claude tools or external tools invoked |

---

### F1 — `output_mode`

**Purpose:** Controls the XML wrapper format. `bare` emits a standalone `<mxGraphModel>` fragment; `wrapped` emits the full `<mxfile><diagram>...</diagram></mxfile>` document. `auto` picks based on page count.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **High** | Bare format reduces nesting levels → lower XML syntax-error rate. Wrong mode breaks multi-page imports entirely. |
| Complexity | **Low** | Simple conditional on `diagrams.length`. No logic beyond template selection. |
| Reliability | **High** | Deterministic. draw.io accepts both formats; auto-wraps bare on open. Lucidchart also accepts both. |
| Weight | **Light** | Zero extra compute. String template choice only. |
| Token Δ | **−500 tokens** | Bare format removes `<mxfile>` + `<diagram>` wrapper XML from output. |
| Exec time | < 1 ms | No external process. |
| Tool usage | None | Pure output formatting decision. |

**Verdict:** Zero-cost quality win. Default `auto` is correct. Only override to `wrapped` for multi-page diagrams.

---

### F2 — `quality_gate`

**Purpose:** Post-emission quality metrics via `validate.py`. Checks edge crossings (sweep-line proxy), orthogonality conformance %, edge-length coefficient of variation, area utilization, and text overflow. Emits Q401–Q405 codes.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **High** | Catches layout regressions invisible to structural checks. Q401 (crossings) and Q404 (utilization) are the two leading visual quality failures in LLM-generated diagrams. |
| Complexity | **Medium** | Sweep-line crossing detection + AABB resolution across parent chains. Text-overflow estimate is simpler (char-width proxy). |
| Reliability | **Medium** | Q401 uses straight-line proxy, not actual routed paths — may overcount crossings on orthogonal layouts. Q402 (80% orthogonality threshold) is heuristic. |
| Weight | **Light** | Pure Python stdlib. O(n²) AABB comparisons — fast for < 200 elements. |
| Token Δ | **0** | CLI script, no LLM tokens. |
| Exec time | 1–3 s | For 60 elements: ~300 AABB pairs, ~1,800 edge endpoint resolutions. |
| Tool usage | `Bash` — runs `validate.py`. Output read into context only if violations found. |

**Verdict:** High-ROI gatekeeper. Default `on` is correct. Only disable for rapid exploratory sketches.

---

### F3 — `grounding_manifest`

**Purpose:** Requires every container, shape, and edge in the JSON plan to include a non-empty `cite` field tracing the element to a source artifact. Validator rejects uncited elements with `G501` ERROR.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **High** | Prevents hallucinated boxes in client deliverables. Shifts LLM from "invent plausible" to "justify explicitly". Single most important trust feature for professional use. |
| Complexity | **Low** (user) / **Medium** (LLM) | Users read the output. LLM must produce a `cite` per element — forces deliberate reasoning during plan construction. |
| Reliability | **High** | Purely structural — validator checks field presence, not semantic content. G501 fires exactly when `cite` is absent or empty. |
| Weight | **Light** | O(n) field presence check on plan JSON. |
| Token Δ | **+1,500–2,500 tokens** | ~25 tokens per element × 70 elements ≈ 1,750 extra tokens in plan output. |
| Exec time | < 100 ms | Part of `validate.py` — negligible additional cost. |
| Tool usage | None during generation. `Bash` for post-emit validation. |

**Verdict:** Essential for production diagrams. Token overhead is modest given the trust guarantee. Turn off only for personal exploration.

---

### F4 — `auto_layout`

**Purpose:** Replaces LLM-assigned coordinates with ELK Layered (preferred) or Graphviz `dot`/`neato` (fallback). `auto` triggers ELK when vertex count > 20. `neato` engine does constraint-based overlap removal without full relayout.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **High** | Eliminates shape overlaps and reduces edge crossings on dense diagrams. Most impactful feature for > 30 elements. ELK handles nested containers correctly (INCLUDE_CHILDREN). |
| Complexity | **High** | Parse mxGraphModel → build ELK compound JSON graph → invoke npx elkjs → map coordinates back. Container-relative coordinates must survive the round-trip. |
| Reliability | **Medium** | ELK output is high quality but: (1) pre-existing waypoints overwritten; (2) edge labels not repositioned; (3) requires Node.js. `neato` (overlap-only) is more reliable for diagrams with intentional structure. |
| Weight | **Heavy** | Node.js + elkjs subprocess. npx auto-installs elkjs (~25 MB) on first run. |
| Token Δ | **0** | Post-emit script, no LLM tokens. |
| Exec time | **10–30 s** (ELK full); **2–5 s** (neato overlap-only). First-ever run: +60 s for npx install. |
| Tool usage | `Bash` — runs `elk-layout.py`, internally spawns `npx elkjs`. |

**Verdict:** Highest-impact post-processor for complex diagrams. `auto` default (triggers at > 20 vertices) is well-calibrated for a 50–60 element diagram. Do NOT use on sequence, BPMN, or grid-matrix patterns (semantic layout, not graph layout).

See §4 for the full ELK vs Graphviz engine analysis.

---

### F5 — `text_metrics`

**Purpose:** Runs `scripts/text-metrics.js` between plan construction and XML emission. Measures every label using an Arial character-width table, producing `text_safe.{min_width, min_height, overflow}` annotations. The LLM applies these as geometry lower bounds before writing XML.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **High** | Prevents text clipping — the most common visual defect in LLM-generated diagrams. Long C4-style labels (name + type + description) reliably overflow default geometries without this. |
| Complexity | **Medium** | Char-width table + greedy word-wrap + HTML tag parsing. Per-element annotation → plan update → grid-collision recheck cycle adds a full LLM pass. |
| Reliability | **Medium-High** | ±8% vs browser canvas; 10% safety margin applied automatically. Handles `<b>`, `<br/>`, HTML entities, per-run font sizes. Known gaps: CJK (2× width underestimate), mixed font families. |
| Weight | **Light** | Pure JS, zero native deps (char-table mode). `--canvas` mode requires libcairo but is opt-in. |
| Token Δ | **+2,000–4,000 tokens** | Annotated plan JSON adds `text_safe` blocks to each element (~43 tokens × 70 elements ≈ 3,000 extra tokens fed to XML emission step). |
| Exec time | < 200 ms | Char-table measurement; no I/O except JSON file read/write. |
| Tool usage | `Bash` — runs `text-metrics.js`; `Read` — reads annotated plan JSON back into context. |

**Verdict:** High impact for C4, BPMN, ERD (verbose labels). Token cost is moderate but justified — prevents a downstream re-generation loop when labels clip. Default `auto` is correct.

---

### F6 — `font_fit`

**Purpose:** Lightweight post-processor that rescales `fontSize` in emitted XML. `auto`: shrinks font when label overflows cell. `grow`: also enlarges when ELK expanded shapes and there is headroom. Runs after `auto_layout`, before `validate.py`.

| Dimension | Rating | Notes |
|---|---|---|
| Impact | **Medium** | Catches text overflow bugs that F5 missed (±8% accuracy gap) or that `auto_layout` introduced by resizing cells. Complements F5 rather than replacing it. |
| Complexity | **Low** | Pure Python stdlib. Stepwise font shrink/grow with char-width approximation (fontSize × 0.55). No external deps. |
| Reliability | **High** | Conservative: fails safe (may shrink one step too aggressively; never produces unreadable text). Skips edge labels and `text;` cells correctly. Known gap: serif fonts (5% error), CJK (2× error). |
| Weight | **Light** | Python stdlib. O(n) pass over XML cells. |
| Token Δ | **0** | Post-emit script, no LLM calls. |
| Exec time | < 50 ms | For 60 elements: trivial. |
| Tool usage | `Bash` — runs `fit-fonts.py`. Modifies `.drawio` file in place. |

**Verdict:** Cheap safety net. Default `auto` is correct. Use `grow` only after `auto_layout=elk`. Turn off for CJK/RTL labels or pixel-perfect designer output.

---

## 3. Feature Categorisation

### By function

```
Output Formatting
└── F1: output_mode

Layout & Geometry
├── F4: auto_layout       ← ELK/dot coordinate assignment
├── F5: text_metrics      ← pre-emit geometry lower bounds
└── F6: font_fit          ← post-emit font scaling

Quality Assurance
├── F2: quality_gate      ← structural + visual metrics
└── F3: grounding_manifest← source-traceability enforcement
```

### By execution phase

```
Phase 0 — Template/reference reading
  (no feature flag; always runs)

Phase 1 — JSON plan construction
  F3: grounding_manifest    (adds cite fields)

Phase 1.5 — Pre-emit geometry
  F5: text_metrics          (annotates min_width/min_height)

Phase 2 — XML emission
  F1: output_mode           (bare vs wrapped wrapper)

Phase 3 — Post-emit geometry
  F4: auto_layout           (ELK/neato coordinate rewrite)
  F6: font_fit              (fontSize scaling)

Phase 4 — Validation & metrics
  F2: quality_gate          (Q4xx metrics)
  F3: grounding_manifest    (G5xx cite checks)
```

### By cost profile

| Feature | Token cost | Time cost | Infra cost |
|---|---|---|---|
| F1 output_mode | Saves ~500 tokens | Negligible | None |
| F2 quality_gate | Zero | 1–3 s | Python (stdlib) |
| F3 grounding_manifest | +1,500–2,500 tokens | < 100 ms | Python (stdlib) |
| F4 auto_layout | Zero | 10–30 s | Node.js + elkjs |
| F5 text_metrics | +2,000–4,000 tokens | < 200 ms | Node.js (stdlib only) |
| F6 font_fit | Zero | < 50 ms | Python (stdlib) |

### Feature impact vs cost ranking

| Rank | Feature | Impact | Cost | Ratio |
|---|---|---|---|---|
| 1 | F1 output_mode | High | Saves tokens | **Excellent** |
| 2 | F6 font_fit | Medium | Near-zero | **Excellent** |
| 3 | F2 quality_gate | High | 1–3 s, 0 tokens | **Excellent** |
| 4 | F3 grounding_manifest | High | +2,000 tokens | **Good** |
| 5 | F5 text_metrics | High | +3,000 tokens, <1 s | **Good** |
| 6 | F4 auto_layout | High (> 20 nodes) | 10–30 s, 0 tokens | **Good** |

---

## 4. Auto-Layout Engine Analysis: ELK vs Graphviz

The skill's `auto_layout` flag accepts four engine values: `elk`, `dot` (Graphviz), `auto` (elk when > 20 vertices), and `neato` (Graphviz overlap removal). These are two fundamentally different tools.

---

### Architecture

| Aspect | ELK (elkjs) | Graphviz |
|---|---|---|
| Core algorithm | Sugiyama layered (ELK Layered) | Dot (hierarchical), neato (force-directed), fdp/sfdp (spring), circo (radial) |
| Primary target | Architecture / software diagrams | General graphs, DAGs, call graphs |
| Container support | Native compound graphs (`INCLUDE_CHILDREN`) | None — children flattened to top level |
| Edge routing | Orthogonal, straight, splines | Polyline; orthogonal only via `ortho` attribute (limited) |
| Runtime | Node.js (`npx elkjs`) | Native C binary (`brew install graphviz`) |
| Installation | Auto via `npx` on first run (~25 MB) | Package manager, < 10 MB, no runtime dep |
| Startup overhead | 1–3 s (Node.js + elkjs load) | < 100 ms |
| Maintenance | Active (Eclipse Foundation, 2024) | Mature / stable (AT&T Research, 1990s) |

---

### Head-to-head comparison

| Criterion | ELK Layered | Graphviz `dot` | Graphviz `neato` |
|---|---|---|---|
| **Architecture diagrams** | ✅ Excellent — purpose-built | ⚠️ Functional — flattens containers | ✅ Good for overlap removal |
| **Nested containers** | ✅ First-class (`INCLUDE_CHILDREN`) | ❌ Not supported | ⚠️ Partial (position only) |
| **Swimlane layouts** | ✅ Preserves lane assignment | ❌ Destroys lane structure | ✅ Moves shapes, keeps parenting |
| **Cross-hierarchy edges** | ✅ Correct (`INCLUDE_CHILDREN`) | ❌ Ignores hierarchy | ⚠️ Treats all as global |
| **Orthogonal edge routing** | ✅ Native (`edgeRouting=ORTHOGONAL`) | ⚠️ Limited (`splines=ortho`, inconsistent) | ❌ Spring forces only |
| **Edge crossing reduction** | ✅ Brandes-Koepf node placement | ✅ Coffman-Graham layer assignment | ⚠️ Stochastic, not guaranteed |
| **Pipeline diagrams (LR)** | ✅ `direction=RIGHT` | ✅ `rankdir=LR` | ⚠️ No concept of direction |
| **Tree / org chart** | ✅ `direction=DOWN` | ✅ Very clean | ❌ Poor for trees |
| **Overlap removal only** | ⚠️ Full relayout (changes structure) | ❌ Full relayout | ✅ Purpose-built (`--engine neato`) |
| **Preserves intentional layout** | ❌ Overwrites all coordinates | ❌ Overwrites all coordinates | ✅ Moves shapes minimally |
| **Flowchart / DAG** | ✅ Good | ✅ Excellent | ❌ Not appropriate |
| **No Node.js required** | ❌ Requires Node.js | ✅ Pure binary | ✅ Pure binary |
| **First run speed** | ⚠️ +60 s (npx install) | ✅ Instant | ✅ Instant |
| **Subsequent runs** | ✅ 10–25 s | ✅ 2–5 s | ✅ 2–5 s |
| **Waypoints after layout** | ⚠️ ELK computes new waypoints (old ones overwritten) | ⚠️ Same | ✅ Unchanged |
| **Edge labels** | ⚠️ Not repositioned | ⚠️ Not repositioned | ✅ Not touched |

---

### Recommendation by diagram pattern

| Pattern | Recommended engine | Reason |
|---|---|---|
| hub-radial | `elk` (`direction=DOWN`) | Hub-spoke → hierarchical naturally |
| pipeline / ETL | `elk` (`direction=RIGHT`) | Layered stages map perfectly to Sugiyama layers |
| swimlanes | `elk` (`direction=RIGHT`) | INCLUDE_CHILDREN preserves lane structure |
| c4-container / component | `elk` (`direction=DOWN`) | Front-end → middle → data tiers |
| tenant-namespace | `elk` | Nested containers are the core challenge |
| flowchart-dag | `elk` (`direction=DOWN`) | Handles decision diamonds correctly |
| tree-hierarchy | `elk` or `dot` | `dot` is slightly faster and cleaner for pure trees |
| erd-crowfoot | `neato` (overlap removal only) | ER has no natural direction; neato preserves relatedness |
| uml-class | `neato` | Same as ERD — proximity meaningful |
| sequence | **off** | Column order is semantic; any relayout breaks it |
| bpmn-process | **off** | Lane order is semantic |
| grid-matrix | **off** | Cell positions are the data |
| scope-columns | `neato` | Two-column structure must be preserved |

---

### When to prefer Graphviz over ELK

1. **Node.js is not available** — pure Python / C environment, no npm access
2. **Overlap removal only** — use `neato`. It uses spring-model forces to push overlapping nodes apart without changing the overall topology. Much safer than a full ELK relayout when the LLM's layout is mostly correct but a few nodes collide.
3. **Pure DAG / tree with no containers** — `dot` is 5× faster than ELK and produces cleaner straight-line hierarchies for simple graphs.
4. **CI environment without Node.js** — `dot` is always available after `apt install graphviz`.

### Practical recommendation

**Default stack (this skill):** `auto_layout=auto` (ELK when > 20 vertices) is the right default for architecture diagrams. ELK's container-awareness is the deciding factor — Graphviz `dot` cannot handle swimlanes or nested tenants correctly.

**For overlap removal after a mostly-good LLM layout:** use `--engine neato`. This is the safest operation when you trust the LLM's spatial logic but just need to separate colliding nodes.

**Fallback chain:** `elk` → `neato` → `dot` → `off` (in degrading quality order for architecture diagrams).

---

## 5. Step Maps

### 5.1 Production Profile (all defaults)

**Config:**
```yaml
output_mode: auto
quality_gate: on
grounding_manifest: on
auto_layout: auto
text_metrics: auto
font_fit: auto
```

**Reference diagram:** swimlane, 3 lanes, 35 shapes + 5 containers + 30 edges = 70 elements

| Step | Action | Tool | Tokens (in+out) | Wall time |
|---|---|---|---|---|
| 0 | Skill load | — | ~4,200 | < 1 s |
| 1A | Read 6 reference files (container-coords, edge-routing, plan-format, style-dictionary, gestalt-rules, layout-engines) | `Read` × 6 | ~11,800 | 2–5 s |
| 1B | Build JSON plan — 70 elements with `cite` fields (F3) | LLM reasoning | ~15,100 | 20–45 s |
| 1.5 | Run text-metrics.js → annotated plan; read back; LLM applies geometry lower bounds (F5) | `Bash` + `Read` + LLM | ~13,500 | 6–11 s |
| 2 | Emit bare mxGraphModel XML for 70 elements (F1) | LLM generation | ~31,000 | 30–60 s |
| 3 | Self-check — 13-item pre-flight checklist | LLM reasoning | ~16,000 | 10–25 s |
| 4 | Write `.drawio` file | `Write` | ~200 | < 1 s |
| 5 | Validate (F2 Q4xx + F3 G5xx) | `Bash` | ~1,000 | 1–3 s |
| 6 | ELK auto-layout, 40 vertices → triggers (F4) | `Bash` → `npx elkjs` | 0 | 10–25 s |
| 7 | Font fit — shrink overflowing labels (F6) | `Bash` | 0 | < 1 s |
| 8 | Re-validate post-layout | `Bash` | ~500 | 1–3 s |
| **Total** | | | **~93,300 tokens** | **~80–180 s** |

**Token breakdown:**

| Category | Tokens | % |
|---|---|---|
| System prompt + skill load | ~4,200 | 4.5% |
| Reference file reads | ~11,800 | 12.7% |
| Plan + F3 cite fields | ~15,100 | 16.2% |
| Annotated plan re-read (F5) + adjustment | ~13,500 | 14.5% |
| XML emission (F1 bare) | ~31,000 | 33.2% |
| Self-check + corrections | ~16,200 | 17.4% |
| Script outputs | ~1,500 | 1.6% |
| **Total** | **~93,300** | 100% |

---

### 5.2 Fast Draft Profile

**Purpose:** Quick visual exploration. No source-tracing, no geometry enforcement, no layout engine. Switch back to production before any delivery.

**Config:**
```yaml
output_mode: auto
quality_gate: off
grounding_manifest: off
auto_layout: off
text_metrics: off
font_fit: off
```

**What gets skipped vs production:**

| Skipped item | Token saving | Time saving |
|---|---|---|
| F3 cite fields in plan | −1,800 tokens | — |
| F5 text-metrics run + annotated plan re-read + geometry adjustment | −13,500 tokens | −6–11 s |
| F4 ELK layout | 0 tokens | −10–25 s |
| F6 font fit | 0 tokens | −1 s |
| F2 Q4xx validation | 0 tokens | −1–3 s |
| F3 G5xx validation | 0 tokens | −1 s |
| `layout-engines.md` reference read | −1,800 tokens | −1 s |
| `gestalt-rules.md` reference read | −1,500 tokens | −1 s |
| **Total savings** | **−18,600 tokens** | **−20–43 s** |

**Reference reads (fast draft — 4 files, not 6):**

| Reference | Tokens | Why still needed |
|---|---|---|
| `container-coords.md` | ~2,000 | Container-relative coords still mandatory |
| `edge-routing.md` | ~2,000 | LCA edge parents still mandatory |
| `plan-format.md` | ~2,500 | Plan schema (cite fields omitted) |
| `style-dictionary.md` | ~2,000 | Style allowlist still applies |

**Fast draft step-by-step:**

| Step | Action | Tool | Tokens (in+out) | Wall time |
|---|---|---|---|---|
| 0 | Skill load | — | ~4,200 | < 1 s |
| 1A | Read 4 reference files (skip layout-engines, gestalt-rules) | `Read` × 4 | ~8,500 | 1–3 s |
| 1B | Build JSON plan — 70 elements, **no cite fields** | LLM reasoning | ~5,300 | 15–30 s |
| 2 | Emit bare mxGraphModel XML — 70 elements (F1) | LLM generation | ~26,500 | 25–50 s |
| 3 | Self-check — abbreviated (structural only; skip font/gestalt checks) | LLM reasoning | ~13,000 | 8–20 s |
| 4 | Write `.drawio` file | `Write` | ~200 | < 1 s |
| 5 | Structural validate only (E0xx errors — no Q/G checks) | `Bash` | ~400 | < 1 s |
| **Total** | | | **~58,100 tokens** | **~50–110 s** |

**Fast draft token breakdown:**

| Category | Tokens | % | vs Production |
|---|---|---|---|
| System prompt + skill load | ~4,200 | 7.2% | same |
| Reference file reads (4 files) | ~8,500 | 14.6% | −3,300 |
| Plan (no cite fields) | ~5,300 | 9.1% | −9,800 |
| XML emission (F1 bare) | ~26,500 | 45.6% | −4,500 |
| Self-check (abbreviated) | ~13,000 | 22.4% | −3,200 |
| Script output | ~400 | 0.7% | −1,100 |
| **Total** | **~58,100** | 100% | **−37% vs production** |

**Self-check scope difference (fast draft):**

| Check | Production | Fast draft |
|---|---|---|
| Every edge has `<mxGeometry>` | ✅ | ✅ |
| All IDs unique | ✅ | ✅ |
| Every parent exists | ✅ | ✅ |
| Container-relative coordinates | ✅ | ✅ |
| Cross-container edges LCA parent | ✅ | ✅ |
| No XML comments in model | ✅ | ✅ |
| HTML in value escaped | ✅ | ✅ |
| startSize on swimlane containers | ✅ | ✅ |
| 40px gutter on all sides | ✅ | ⚠️ Best-effort only |
| Edges in layer before icon layer | ✅ | ✅ |
| Styles from allowlist | ✅ | ⚠️ Best-effort only |
| Font sizes consistent | ✅ | ❌ Skipped |
| Labels fit geometry | ✅ | ❌ Skipped (no F5) |

**Time breakdown (fast draft):**

| Phase | Time | Dominant factor |
|---|---|---|
| Reference reads (4 files) | 1–3 s | File I/O |
| LLM plan (no cite) | 15–30 s | Shorter output |
| LLM XML emission | 25–50 s | Large output (~12K tokens) |
| LLM self-check | 8–20 s | Abbreviated checklist |
| File write + validate | < 2 s | Disk I/O + Python |
| **Total** | **~50–110 s** | Dominated by LLM generation |

---

### 5.3 Dense Diagram Profile (> 50 elements, forced ELK)

Override the `auto` threshold and use `grow` mode after ELK expands shapes:

```yaml
# Per-diagram override — add to first line of source plan:
# <!-- lucid:auto_layout=elk lucid:font_fit=grow -->
auto_layout: elk        # bypass auto threshold, always run ELK
font_fit: grow          # ELK enlarged shapes → grow font to fill headroom
```

Same step sequence as production, but Step 6 always runs ELK regardless of vertex count, and Step 7 uses `grow` mode.

---

## 6. Comparison: drawio-architect vs `drawio-skill`

### Scope

| Axis | drawio-architect (this repo) | drawio-skill (anthropic-skills) |
|---|---|---|
| Primary output | `.drawio` XML file | `.drawio` XML + PNG/SVG/PDF/JPG export |
| Visual feedback | None — XML only | Built-in: CLI export + vision self-check loop |
| User iteration | Single-shot generation | Interactive review loop (up to 5 rounds) |
| Target tool | Lucidchart, draw.io, any mxGraph reader | draw.io desktop specifically |
| Workflow model | Plan → emit → validate → layout | Generate → export → self-check → review → final export |

---

### Feature-by-feature comparison

| Feature | drawio-architect | drawio-skill |
|---|---|---|
| **Layout patterns** | 15 named patterns with templates | Ad-hoc — user describes what they want |
| **Starter templates** | 15 `.drawio` skeleton files per pattern | None |
| **Plan-then-emit** | Mandatory JSON plan step | Direct XML generation |
| **Grounding manifest** | Yes — `cite` on every element (F3) | No |
| **Auto-layout** | ELK + neato post-processor (F4) | No post-processing |
| **Text metrics** | Pre-emit label measurement (F5) | No |
| **Font fit** | Post-emit font scaling (F6) | No |
| **Quality gate** | 5 structural/visual metrics (F2) | Visual self-check via PNG + vision (step 5) |
| **Validator** | `validate.py` — 9 errors + 10 warnings + 5 quality codes | No validator script |
| **Visual self-check** | No | Yes — model reads exported PNG, auto-fixes up to 2 rounds |
| **Review loop** | No | Yes — shows user the PNG, iterates on feedback |
| **CLI export** | No — XML only | Yes — PNG/SVG/PDF/JPG via draw.io desktop CLI |
| **Embedded XML export** | No | Yes — `-e` flag, `.drawio.png` double extension |
| **PNG repair** | No | Yes — `repair_png.py` fixes truncated IEND chunk (bug #8) |
| **Browser fallback** | No | Yes — `encode_drawio_url.py` → diagrams.net viewer URL |
| **Style presets** | No | Yes — user-defined named presets + built-in (`default`, `corporate`, `handdrawn`) |
| **Vendor icons** | Yes — AWS, Azure, GCP, UML, ERD, BPMN vocabularies | Basic shape keywords only |
| **Container-relative coords** | Enforced via plan + validator (W109) | Documented but not programmatically enforced |
| **Two-layer edge rendering** | Enforced (edges_layer before icon layer) | Not defined |
| **Edge entry/exit point rules** | Documented in `edge-routing.md`, validated | Documented in skill body (perimeter distribution) |
| **Diagram type presets** | 15 patterns implicit in templates | 6 named types (`references/diagram-types.md`) |
| **Output wrapper control** | `output_mode` flag (bare/wrapped/auto) | Always `<mxfile>` wrapped |
| **Multi-page diagrams** | Supported (wrapped mode) | Supported (`--page-index` flag) |
| **Animated edges** | Not mentioned | `flowAnimation=1` style attribute |
| **Sandbox / env handling** | No special handling | Explicit macOS sandbox isolation fallback chain |
| **File naming convention** | `NN_DiagramName/V_layout-name.drawio` | User's working dir or explicit path |
| **Dependencies** | Node.js (elkjs) + Python (validate/layout/font) | Python (scripts) + draw.io desktop CLI |
| **Token budget (50-element diagram)** | ~93K tokens (production) / ~58K (fast draft) | ~40–70K tokens (includes self-check + edit rounds) |
| **End-to-end time** | 80–180 s | 90–300 s (includes export + vision + review) |

---

### Strengths and weaknesses

**drawio-architect strengths:**
- Far deeper layout discipline — 15 patterns, templates, container coords enforced
- Grounding manifest prevents hallucinated elements (critical for client diagrams)
- Quantitative quality metrics (Q401–Q405 codes)
- ELK auto-layout handles complex nested diagrams automatically
- Rich vendor icon vocabularies (AWS/Azure/GCP/UML/BPMN)
- Deterministic overlap removal via neato
- Separation of concerns: plan → validate → emit → layout → font-fit pipeline

**drawio-architect weaknesses:**
- No visual output — user cannot see the diagram without opening draw.io separately
- No iterative feedback loop — single-shot generation
- No style personalization (no preset system)
- Heavier token budget per diagram
- Requires Node.js for ELK

**drawio-skill strengths:**
- Full lifecycle: generates XML, exports PNG, shows it to user, iterates
- Vision self-check catches obvious visual errors automatically
- Animated edge support (`flowAnimation=1`)
- Style preset system for visual identity consistency
- Works entirely without knowing about layout algorithms
- Handles CLI unavailability gracefully (sandbox detection, fallback chain)
- Simpler to use — no plan format to understand

**drawio-skill weaknesses:**
- No structural validation — malformed XML silently accepted until export
- No layout engine — overlapping shapes require manual user feedback
- No grounding — elements not traced to sources
- No vendor icon vocabularies — limited to generic shape keywords
- Container-relative coordinates not enforced — a common source of layout bugs
- No concept of diagram patterns — each diagram reinvented from scratch
- Token efficiency lower on multi-round review loops

---

### Decision guide: which skill to use?

| Scenario | Use |
|---|---|
| Client-facing architecture deliverable | **drawio-architect** — grounding + quality gate |
| Quick personal sketch / prototype | **drawio-skill** — visual feedback loop, faster iteration |
| Complex nested containers (multi-tenant, swimlanes) | **drawio-architect** — ELK INCLUDE_CHILDREN |
| Need PNG/SVG/PDF right now | **drawio-skill** — built-in CLI export |
| Diagram with AWS/Azure/GCP icons | **drawio-architect** — full shape vocabularies |
| User wants to see and tweak interactively | **drawio-skill** — review loop |
| Regulated / auditable diagrams | **drawio-architect** — grounding manifest traces every element |
| General flowchart or sequence diagram | **drawio-skill** — simpler workflow, same quality |
| Dense diagram (> 30 nodes) | **drawio-architect** — ELK auto-layout critical |
| Consistent visual brand across diagrams | **drawio-skill** — style preset system |

---

## 7. Recommended Profiles

### Production (default)

```yaml
output_mode: auto
quality_gate: on
grounding_manifest: on
auto_layout: auto
text_metrics: auto
font_fit: auto
```
Expected: ~93K tokens, ~80–180 s end-to-end.  
Use for: client deliverables, team documentation, regulated diagrams.

---

### Fast Draft

```yaml
output_mode: auto
quality_gate: off
grounding_manifest: off
auto_layout: off
text_metrics: off
font_fit: off
```
Expected: ~58K tokens (~37% savings), ~50–110 s end-to-end.  
Use for: exploration, rough ideation, internal whiteboarding. Switch to production before delivery.

**What you get vs production:** structurally valid XML with correct parent IDs, edge geometry, and container-relative coordinates. You do **not** get: cite traceability, label-fit guarantees, auto-layout, font scaling, or quality metrics.

---

### Dense Diagram (> 50 elements, forced ELK)

```yaml
output_mode: auto
quality_gate: on
grounding_manifest: on
auto_layout: elk          # bypass auto threshold
text_metrics: auto
font_fit: grow            # ELK enlarged shapes — grow font to fill
```
Override per-diagram: `<!-- lucid:auto_layout=elk -->` + `<!-- lucid:font_fit=grow -->` on first line of source plan.
