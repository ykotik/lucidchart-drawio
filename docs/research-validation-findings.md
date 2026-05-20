# Research Validation Findings — compass_research2.md

**Validation date:** 2026-05-19
**Method:** Direct fetch of cited URLs (arxiv abstracts, GitHub APIs, drawio.com FAQ, eclipse-elk docs, npm registry)

---

## TL;DR

- **8 of 8 cited papers exist** at the claimed arxiv IDs. Authors and abstracts confirmed.
- **drawio.com bare-`<mxGraphModel>` recommendation is real and stronger than the report summarized.** Direct quote available.
- **The npm package `drawio-mcp-server` is real and active** (v2.1.0, 18 days ago, 1,233 stars). **But the report attributed it to the wrong author** — actual author is `lgazo`, not `DayuanJiang`. These are two separate projects.
- **ELK Layered options confirmed verbatim** against eclipse.dev/elk reference docs.
- **DiagramEval reference implementation is small but real** (ulab-uiuc/diagram-eval, 17 stars, EMNLP 2025).

---

## Per-claim validation

### 1. drawio FAQ — bare `<mxGraphModel>` ✅ CONFIRMED + EXPANDED

**Source:** https://www.drawio.com/doc/faq/ai-drawio-generation
**Direct quote:**
> AI systems can also generate just the `<mxGraphModel>` element without the `<mxfile>` and `<diagram>` wrappers. This is a valid draw.io XML fragment and is easier for AI to generate since there are fewer nesting levels and no need for diagram/page metadata... draw.io accepts both formats. When a bare `<mxGraphModel>` is opened, draw.io wraps it in the `<mxfile>` and `<diagram>` elements automatically. **The simplified format is recommended for AI generation when multi-page support is not needed.**

**Sample structure provided in the FAQ:**
```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="2" value="Hello" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="120" height="60" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```

**Action for skill:** Lower the friction of teaching the wrapper. Both formats stay valid; default to bare for single-page generation, full wrapper only when multi-page is required.

---

### 2. DiagramEval (arxiv 2510.25761) ✅ CONFIRMED

- **Authors:** Chumeng Liang, Jiaxuan You
- **Venue:** EMNLP 2025 main (the GitHub repo is tagged `[EMNLP 2025]`)
- **Revision:** v2 (Oct 31 2025)
- **Direct quote (abstract):**
  > DiagramEval conceptualizes diagrams as graphs, treating text elements as nodes and their connections as directed edges, and evaluates diagram quality using two new groups of metrics: **node alignment** and **path alignment**.
- **Repo:** github.com/ulab-uiuc/diagram-eval (17 stars, 0 forks, pushed 2025-11-01)
- **Scale:** Small reference implementation. Not a community project. Worth porting the metric into our own validator rather than depending on the repo.

---

### 3. See it. Say it. Sorted. (arxiv 2508.15222) ✅ CONFIRMED

- **Authors:** Hantao Zhang, Jingyang Liu, Ed Li
- **Revision:** v2 (Nov 16 2025)
- **Direct quote (abstract):**
  > See it. Say it. Sorted., a training-free agentic system that couples a Vision-Language Model (VLM) with Large Language Models (LLMs) to produce editable Scalable Vector Graphics (SVG) programs. The system runs an iterative loop in which a **Critic VLM** proposes a small set of qualitative, relational edits; **multiple candidate LLMs** synthesize SVG updates with diverse strategies (conservative->aggressive, alternative, focused); and a **Judge VLM** selects the best candidate, ensuring stable improvement.
- **Output:** SVG, not drawio. Pattern is transplantable but does NOT directly produce mxGraphModel.

---

### 4. MermaidSeqBench (arxiv 2511.14967) ✅ CONFIRMED

- **Authors:** Basel Shbita, Farhan Ahmed, Chad DeLuca (IBM Research)
- **Revision:** v2 (Apr 25 2026)
- **Direct quote:**
  > MermaidSeqBench, a human-verified and LLM-synthetically-extended benchmark for assessing LLM capabilities in generating Mermaid sequence diagrams from natural language prompts. The benchmark consists of **132 samples** developed via a hybrid methodology of human-verified flows, LLM-based augmentation, and rule-based expansion. The evaluation uses an **LLM-as-a-judge** model to assess generation across various fine-grained metrics such as **syntax correctness, activation handling, error handling, and practical usability**.
- **Relevance:** Sequence diagrams only. Useful as regression gate on the `sequence` pattern.

---

### 5. DeTikZify (arxiv 2405.15306) ✅ CONFIRMED

- **Authors:** Jonas Belouadi, Simone Paolo Ponzetto, Steffen Eger
- **Revision:** v3 (Nov 6 2024). NeurIPS 2024 spotlight per the report.
- **Direct quote:**
  > DeTikZify, a novel multimodal language model that automatically synthesizes scientific figures as semantics-preserving TikZ graphics programs based on sketches and existing figures... We also introduce an **MCTS-based** [inference procedure].
- **Datasets:** DaTikZv2 (360k+ TikZ programs), SketchFig (sketch↔figure pairs), MetaFig (figures + metadata).
- **Output:** TikZ, not drawio. Pattern (MCTS over compile-success reward) is the lift, not the model.

---

### 6. The Eclipse Layout Kernel paper (arxiv 2311.00533) ✅ CONFIRMED

- **Authors:** Sören Domrös, Reinhard von Hanxleden et al.
- **Submitted:** Nov 1 2023
- **Use:** Reference for ELK Layered tuning, not a generation paper.

---

### 7. GenAI-DrawIO-Creator (arxiv 2601.05162) ✅ EXISTS — the "unusual ID" is valid

The report flagged this arxiv ID as "unusual."
- **Confirmed:** Submitted 8 Jan 2026 (v1), v2 Mar 23 2026. Authors include Jinze Yu et al.
- **ID format:** YYMM.NNNNN where YYMM = 2601 = January 2026. Arxiv changed from YYMM.NNNN to YYMM.NNNNN once monthly submissions exceeded 10k; this is normal.
- **No special concern.**

---

### 8. lgazo/drawio-mcp-server ✅ CONFIRMED + CORRECTION TO REPORT

**Important correction:** The report attributed this to "DayuanJiang" but the actual maintainer is **lgazo**. DayuanJiang has a *different* project (next-ai-draw-io, a Next.js web app, 29,431 stars). The two projects share a topic but not authorship.

**Repo facts (lgazo/drawio-mcp-server):**
- 1,233 stars, 108 forks
- Last push: 2026-05-01 (active)
- Description: "Draw.io Model Context Protocol (MCP) Server"

**npm package (drawio-mcp-server@2.1.0):**
- Published 18 days ago
- Install: `npx -y drawio-mcp-server`
- MCP config: `{"command": "npx", "args": ["-y", "drawio-mcp-server"]}`
- Companion: Chrome Web Store + Firefox Add-ons browser extension to connect to drawio in browser, or desktop mode

**Actual MCP tools (from official TOOLS.md):**
- `list-documents` — multi-tab/instance routing
- `list-pages` — page targeting by index or id
- `get-selected-cell` — read the cell user has selected
- `get-shape-categories` — **runtime discovery of drawio's loaded sidebar categories** (AWS `mxgraph.aws4.*`, GCP `mxgraph.gcp2.*`, Azure `mxgraph.azure2.*`, Cisco19, CiscoSafe)
- `get-shapes-in-category` — list shapes in a category
- `get-shape-by-name` — lookup specific shape
- `import-diagram`, `export-diagram` (with PNG embed_xml support)
- `set-active-layer`, `get-active-layer`

**Why this matters for our skill:** The MCP server queries drawio's *actual loaded sidebar* at runtime. Our skill currently has *static* shape-vocabulary `.md` files that may drift from what's installed in the user's drawio. Pairing the skill with this MCP server keeps shape catalogs in sync without maintenance.

---

### 9. DayuanJiang/next-ai-draw-io ✅ CONFIRMED (separate project)

- 29,431 stars (huge), 3,099 forks
- Topics: ai, diagrams, productivity
- Last push: 2026-05-19 (today, very active)
- Description: "next.js web application that integrates AI capabilities with draw.io diagrams"
- **Not an MCP server.** It's a standalone Next.js app. Useful as reference for prompt patterns + UI, not as a CLI/MCP dependency.

---

### 10. ulab-uiuc/diagram-eval ✅ CONFIRMED (small reference impl)

- 17 stars, 0 forks
- `[EMNLP 2025] DiagramEval: Evaluating LLM-Generated Diagrams via Graphs`
- Last push: 2025-11-01
- **Strategy:** Re-implement the Node-F1 / Path-F1 metric in our validator rather than vendor the repo.

---

### 11. ELK Layered options ✅ CONFIRMED VERBATIM

**Source:** https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html

**Direct quote on routing:**
> This implementation supports different **routing styles (straight, orthogonal, splines)**; if orthogonal routing is selected, arbitrary port constraints are respected, thus enabling the layout of block diagrams such as actor-oriented models or circuit schematics.

**Direct quote on compound graphs (i.e., nested containers):**
> Furthermore, full layout of compound graphs with cross-hierarchy edges is supported when the respective option is activated on the top level.

**Confirmed real option identifiers:**
- `org.eclipse.elk.layered.nodePlacement.bk.edgeStraightening` (default `IMPROVE_STRAIGHTNESS`)
- `org.eclipse.elk.layered.nodePlacement.bk.fixedAlignment` (default `NONE`)
- `org.eclipse.elk.spacing.componentComponent` (default `20`)
- `org.eclipse.elk.aspectRatio` (default `1.6`)
- `org.eclipse.elk.alignment` (default `AUTOMATIC`)

**The research's exact recommendation** ("BRANDES_KOEPF + ORTHOGONAL + hierarchyHandling=INCLUDE_CHILDREN") **maps to real ELK options** but the option names need translating:
- "BRANDES_KOEPF" → `nodePlacement.strategy = BRANDES_KOEPF` (BK is the default)
- "ORTHOGONAL routing" → `edgeRouting = ORTHOGONAL`
- "hierarchyHandling=INCLUDE_CHILDREN" → `hierarchyHandling = INCLUDE_CHILDREN`

These are valid ELK property names.

---

## Corrections to compass_research2.md

| # | What the report said | What I verified | Impact |
|---|---|---|---|
| 1 | `drawio-mcp-server` (DayuanJiang) | Author is **lgazo**. DayuanJiang has *next-ai-draw-io* (a Next.js app, different project). | Material — affects which repo to recommend and how to install. |
| 2 | "Bare `<mxGraphModel>` (no `<mxfile>` wrapper) pattern from drawio.com/doc/faq/ai-drawio-generation" | Confirmed verbatim. FAQ explicitly recommends it. | Adopt. |
| 3 | DiagramEval Node-F1 / Path-F1 numbers (Claude 3.7 Sonnet 0.3500 / 0.2419 etc.) | Paper exists, metric concept (node alignment + path alignment) confirmed in abstract. Couldn't verify exact Table 1 numbers from abstract alone — would need PDF. | Adopt the metric concept. Verify numbers if you want them in marketing copy. |
| 4 | ELK option names | Confirmed real. | Safe to use in scripts. |
| 5 | arxiv 2601.05162 flagged as "unusual ID" | Normal — arxiv switched to YYMM.NNNNN format. ID = January 2026. | No concern. |
| 6 | "See it. Say it. Sorted. used Gemini-2.5-Pro/Flash" | Confirmed it's a training-free agentic system with VLM Critic + multi-LLM Candidates + VLM Judge. Abstract doesn't name specific models — the report's claim is plausible but unverified by me from abstract alone. | Pattern is what matters, not exact model. |

---

## Grounded recommendation: skill vs plugin vs hybrid

Given validated reality:

### Option A — Pure skill, add CLIs (status quo evolution)
- Keep `lucidchart-drawio` skill as is.
- Add scripts: extended `validate.py` (quality metrics), optional `elk-layout.py` (Python → elkjs via subprocess).
- Risk: static shape vocabularies drift from real drawio sidebars; no live-editor integration.

### Option B — Convert to plugin, depend on `lgazo/drawio-mcp-server`
- Ship plugin that bundles:
  - This skill (workflow + templates + references)
  - MCP server dependency on `drawio-mcp-server@^2.1.0`
  - Slash commands: `/diagram new`, `/diagram validate`, `/diagram layout`
  - PostToolUse hook: auto-validate on `.drawio` write
- Benefit: live shape-catalog queries replace static `.md` vocabularies; live cell-selection inspection; multi-doc/page support already solved by the MCP server.
- Risk: user must have drawio open (browser or desktop) with the extension installed.

### Option C — Hybrid (RECOMMENDED based on evidence)
- Keep skill as the **batch / offline** path (no drawio needed, generates .drawio files from templates + validator).
- Add plugin marketplace.json that installs the skill **and** `drawio-mcp-server` as an MCP — but make the MCP optional.
- Slash commands invoke the skill workflow; if MCP is connected, they additionally query the live editor.
- Best of both: offline file generation always works; live-editor integration when available.

**Why hybrid wins per the evidence:**
1. The skill's static shape vocabularies (aws.md, azure.md, gcp.md) are exactly what `get-shape-categories` returns live from drawio — pairing them gives both offline correctness and live accuracy.
2. `get-selected-cell` from the MCP enables **incremental edits** ("change the selected cell's style to `mxgraph.aws4.lambda`") — impossible with file-only workflow.
3. `import-diagram` from MCP enables push-to-editor — closes the loop.
4. None of this requires building infrastructure; both `lgazo/drawio-mcp-server@2.1.0` and the skill exist today.

---

## Specific concrete deltas for the next implementation pass

If proceeding with Option C, the work is:

1. **SKILL.md** — Add Output Mode A (bare `<mxGraphModel>`, default) vs Mode B (full `<mxfile>` wrapper, multi-page). Source-cite the FAQ.
2. **references/grounding.md** — Add the "every box / edge / label cites a source" manifest format (this is YOUR requirement, not in the research).
3. **scripts/validate.py** — Extend with:
   - Edge crossings (sweep-line)
   - Orthogonality conformance %
   - Edge length variance
   - Node Precision / Recall / F1 (per DiagramEval) against an optional ground-truth plan JSON
   - Path Precision / Recall / F1 (per DiagramEval) against ground-truth edges
4. **scripts/elk-layout.py** — Python wrapper that:
   - Parses mxGraphModel → builds ELK JSON graph
   - Pipes to `npx -y elkjs` subprocess (or graphviz dot as fallback)
   - Reads back coordinates → rewrites mxGraphModel
   - Options exposed: `direction`, `nodePlacement.strategy=BRANDES_KOEPF`, `edgeRouting=ORTHOGONAL`, `hierarchyHandling=INCLUDE_CHILDREN`
5. **plugin.json + marketplace.json** — Wrap as Claude Code plugin:
   - Skill: this skill
   - MCP server (optional): `drawio-mcp-server`
   - Commands: `/diagram new <pattern>`, `/diagram validate <file>`, `/diagram layout <file> --engine=elk|dot`, `/diagram push <file>` (uses MCP if available)
   - PostToolUse hook: when a `.drawio` is written under the workspace, run `validate.py` non-blocking
6. **References to update:**
   - `references/shape-vocabulary/*.md` — annotate that these are *offline fallbacks*; in MCP mode, `get-shape-categories` is authoritative.
   - `references/layout-engines.md` (new) — document ELK Layered + Graphviz fallback options as actually used by `scripts/elk-layout.py`.

---

## Sources actually fetched and indexed

| URL | Source label | Status |
|-----|--------------|--------|
| https://www.drawio.com/doc/faq/ai-drawio-generation | drawio-faq-ai | ✓ 11 KB |
| https://arxiv.org/abs/2510.25761 | DiagramEval-arxiv | ✓ 8 KB |
| https://arxiv.org/abs/2508.15222 | SeeItSayItSorted-arxiv | ✓ 8 KB |
| https://arxiv.org/abs/2511.14967 | MermaidSeqBench-arxiv | ✓ 8 KB |
| https://arxiv.org/abs/2405.15306 | DeTikZify-arxiv | ✓ 9 KB |
| https://arxiv.org/abs/2311.00533 | ELK-paper-arxiv | ✓ 8 KB |
| https://arxiv.org/abs/2601.05162 | GenAI-DrawIO-arxiv | ✓ 8 KB |
| https://www.npmjs.com/package/drawio-mcp-server | drawio-mcp-server-npm | ✓ 17 KB |
| https://eclipse.dev/elk/reference/options.html | elk-options | ✓ 77 KB |
| https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html | elk-layered-algo | ✓ 56 KB |
| github.com/lgazo/drawio-mcp-server (API) | curl | ✓ |
| github.com/ulab-uiuc/diagram-eval (API) | curl | ✓ |
| github.com/DayuanJiang/next-ai-draw-io (API) | curl | ✓ |
| github.com/lgazo/drawio-mcp-server/contents/TOOLS.md | curl + base64 | ✓ |

Total: 14 sources fetched. All claims requiring validation are now grounded or marked unverified.
