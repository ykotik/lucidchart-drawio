# LLM × draw.io / Lucidchart Architecture Diagrams — Expansion Report (May 2026)

## TL;DR
- **The biggest new lever for clean draw.io output is *layout-engine choice*, not model choice.** Switch your Claude/Cowork pipeline from "let the LLM place coordinates" to "let the LLM emit a logical graph + run a layout engine." For software architecture specifically, **TALA (Terrastruct)** and **ELK Layered with BRANDES_KOEPF + ORTHOGONAL routing** produce the fewest crossings and cleanest nested containers; both can be post-converted into draw.io XML.
- **There are now real benchmarks and metrics you can adopt as a quality gate**: MermaidSeqBench (NeurIPS 2025 workshop), DiagramEval (EMNLP 2025, node-F1/path-F1 over an SVG-parsed graph), DeTikZify's automatic metrics (cBLEU, TED, DSim, KID), plus classical aesthetic criteria (edge crossings, node overlap, area utilization). **DiagramEval is the most architecture-relevant** and the one to wire into CI first.
- **Commercial AI diagrammers (Lucid AI, Eraser DiagramGPT, Miro AI, Whimsical AI, FigJam AI, Mermaid Chart Pro) are *not* a replacement for your Claude + drawio + skill-pack workflow** because none of them export to native .drawio XML and most run their layout through Mermaid/dagre under the hood with limited container support. They are good for *first-draft on a client whiteboard*, then re-author in draw.io.

## Key Findings

1. **Practitioner-relevant research has consolidated around three paradigms**: (a) two-stage *plan-then-render* (DiagrammerGPT, AI2D-Caption); (b) *agentic critic–candidate–judge* loops over SVG/XML (See it. Say it. Sorted., DeTikZify with MCTS, GenAI-DrawIO-Creator); (c) *evaluation-as-graph* (DiagramEval) — the missing piece you can plug into your CI as a quality gate.
2. **ELK Layered is the most documented hierarchical engine** in the open-source world and the one you should reach for when draw.io's "Apply Layout → Vertical/Horizontal Flow" is not enough; its **BRANDES_KOEPF** node placer (default, a 62 KB implementation in the ELK source tree) is what produces the "straight long edges" look people want in C4 container diagrams. Edge-routing mode (ORTHOGONAL / POLYLINE / SPLINES) is the single biggest visual lever.
3. **TALA is the only widely-available layout engine designed for software-architecture diagrams** specifically (proprietary, ships with D2). It treats containers as first-class at every phase, handles non-hierarchical layouts symmetrically, and renders to SVG/PNG; getting from D2/TALA SVG into *editable* draw.io requires a manual import step.
4. **draw.io shipped a built-in AI integration in 2025-26** (Gemini, Claude Sonnet 4.5/Haiku 4.5, GPT-5.1, GPT-4.1) plus an official `drawio-mcp-server`. The official guidance is to emit a bare `<mxGraphModel>` fragment (no `<mxfile>` wrapper) — the single most important constraint pattern you can drop into your skill.
5. **There is no useful Lucidchart-native AI delta for an EPAM practitioner**: Lucid markets a proprietary "visual reasoning engine" but its public docs describe AI as "text-prompt → flowchart" with no exported model name, no .drawio export, and a Mermaid importer for technical users. Stick with draw.io as the system of record.

## Details

### 1. Research papers with shipped tools or reproducible techniques

| # | Paper / artifact | Venue, year | Link | Shipped artifact | Practitioner takeaway |
|---|---|---|---|---|---|
| 1 | **DiagrammerGPT** (Zala, Lin, Cho, Bansal) | COLM 2024 (arXiv 2310.12128) | arxiv.org/abs/2310.12128 | **AI2D-Caption** densely-annotated diagram dataset; planner-auditor prompt recipe | The "diagram plan → renderer" two-stage pattern is reproducible *without* their renderer. In your Claude Code workflow, force a JSON "plan" (nodes, groups, edges, intended direction) before any XML — alone reduces hallucinated arrows and floating shapes. |
| 2 | **See it. Say it. Sorted.** (H. Zhang, J. Liu, E. Li, Yale/Edinburgh) | arXiv 2508.15222 (v2 Nov 2025) | arxiv.org/abs/2508.15222 | Open-source repo (training-free agentic SVG loop: Critic VLM → multi-LLM candidates → Judge VLM). Reference implementation used Gemini-2.5-Pro as Critic/Judge VLM and Gemini-2.5-Flash for candidate LLMs. | The "Critic–Candidates–Judge" loop is directly transplantable into Claude Code. Per the paper: "On 10 sketches derived from flowcharts in published papers, our method more faithfully reconstructs layout and structure than two frontier closed-source image generation LLMs (GPT-5 and Gemini-2.5-Pro), accurately composing primitives (e.g., multi-headed arrows) without inserting unwanted text." Use Claude (or any VLM-capable model) for the Critic / Judge roles in your stack. |
| 3 | **DeTikZify / DeTikZifyv2-8b** (Belouadi, Ponzetto, Eger) | NeurIPS 2024 spotlight; v2 8b Dec 2024; TikZero adapters Mar 2025 | arxiv.org/abs/2405.15306 | **DaTikZv2** (360k+ human-authored TikZ programs), **SketchFig**, **MetaFig**; LLaMA-3.1+SigLIP model on HF; MCTS inference loop | Even though it targets TikZ, the **MCTS-based self-refinement with a compile-success reward** is the best-documented technique for "make the output actually parse and render." Adopt the idea: reward = "draw.io opens this file AND has zero overlapping shapes." |
| 4 | **MermaidSeqBench** (Shbita, Ahmed et al., IBM Research) | NeurIPS 2025 Workshop (arXiv 2511.14967, v2 Apr 2026) | arxiv.org/abs/2511.14967 | 132-sample human-verified NL→Mermaid sequence-diagram dataset; LLM-as-judge rubric (syntax correctness, activation handling, error handling, practical usability). Initial evaluations ran six models — Qwen 2.5 (0.5B/7B), Llama 3.1/3.2 (1B/8B), Granite 3.3 (2B/8B) — with multiple LLM judges. | First public benchmark you can run locally to grade *your* Claude/GPT pipelines on sequence diagrams. Use it as a regression gate when you swap the Sonnet 4.6 model under your skills. |
| 5 | **DiagramEval** (Liang & You, UIUC) | EMNLP 2025 main (arXiv 2510.25761; ACL Anthology 2025.emnlp-main.640) | arxiv.org/abs/2510.25761 ; github.com/ulab-uiuc/diagram-eval | Code + metric: parse generated SVG into a graph, compute **Node Precision/Recall/F1** and **Path Precision/Recall/F1** against ground truth | The most architecture-relevant metric in this list. Per Table 1 of the paper, on 361 CVPR 2025 paper diagrams: **Claude 3.7 Sonnet** Node-F1 0.3500 / Path-F1 0.2419 / CLIPScore-Text 0.6206; **Gemini 2.5 Pro** Node-F1 0.3341 / Path-F1 0.2261 / CLIPScore-Text 0.6090; **Llama 4 Maverick** Node-F1 0.3470 / Path-F1 0.2005 / CLIPScore-Text 0.6962. Claude had the highest **Node Recall (0.5087** vs Gemini 0.3741, Llama 0.3121) — it over-generates extra nodes. Adopt Node-F1 / Path-F1 as your primary CI quality gate. |
| 6 | **GenAI-DrawIO-Creator** (Jiang et al.) | arXiv 2601.05162 (preprint) | github.com/DayuanJiang/next-ai-draw-io | Next.js app + `drawio-mcp-server` npm package; supports Claude Sonnet 4.5, GPT-5.1, Gemini 3 Pro, GLM-4.7, DeepSeek V3.2/R1; image-to-drawio replication | The most direct follow-up to last year's AWS GenAI-DrawIO-Creator and the one to evaluate first. MCP server is `npx -y drawio-mcp-server` — drop-in for Claude Code. Authors explicitly state "the Claude series has been trained on draw.io diagrams with cloud architecture logos like AWS, Azure, GCP." |
| 7 | **Visualizing Thought: Conceptual Diagrams Enable Robust Planning in LMMs** | arXiv 2503.11790 (2025) | arxiv.org/abs/2503.11790 | Technique: depth-wise backtracking over diagrammatic intermediate states | Reproducible without code. Use diagrammatic representations as *intermediate reasoning state* rather than final output — improves layout correctness because the LLM "sees" what it produced. |
| 8 | **The Eclipse Layout Kernel** (Domrös, Schneider, Spönemann, von Hanxleden) | arXiv 2311.00533 (LIPIcs/JGAA companion) | arxiv.org/abs/2311.00533 | Reference architecture + benchmark of all ELK Layered processors | Not a generation paper, but *the* canonical reference for which ELK options to set. Read end-to-end before tuning ELK. |

**Notes on what's *not* yet published**: ChatDiagram has marketing copy but no peer-reviewed artifact; Eraser's DiagramGPT is a commercial product with no academic paper. EduIllustrate (arXiv 2604.05005) is K-12 education focused and has limited direct architecture-diagram applicability.

### 2. Layout algorithms and engines — deep dive

#### Sugiyama framework — the four phases, who implements what

| Phase | What it does | dagre | ELK Layered | OGDF | MSAGL | yFiles Hierarchic |
|---|---|---|---|---|---|---|
| 1. Cycle removal | Reverse a minimal set of edges to make graph acyclic | Greedy heuristic | GREEDY (default) or DFS (Gansner) | Multiple modules | DFS-based | Multiple, configurable |
| 2. Layer assignment | Assign each node to a "rank" | network-simplex / tight-tree / longest-path | LONGEST_PATH (default) / NETWORK_SIMPLEX / COFFMAN_GRAHAM / INTERACTIVE | LongestPathRanking / OptNodeRanking / CoffmanGrahamRanking | Modified Coffman–Graham | Configurable |
| 3. Crossing reduction | Order nodes within each layer | Barycenter heuristic + local transpositions | LAYER_SWEEP | Multiple | Sweep | Layered with multiple iterations |
| 4. Coordinate assignment | Assign concrete x/y | Brandes–Köpf | **BRANDES_KOEPF (default)** / LINEAR_SEGMENTS / NETWORK_SIMPLEX / SIMPLE | Multiple | Brandes algorithm | Proprietary, very polished |

**ELK Layered internals** (the engine you'll most often reach for from JS or Java):
- **Node placement strategies** (per the `NodePlacementStrategy.java` enum in `eclipse-elk/elk`):
  - `BRANDES_KOEPF` — default. Marks type-1 conflicts (short edges crossing long edges), builds aligned blocks in 4 directions (UP/DOWN × LEFT/RIGHT), selects most compact or most balanced layout. Best for hierarchical software diagrams with long pipelines.
  - `LINEAR_SEGMENTS` — Sander's "pendulum" method with deflection dampening. Use when BK produces too-wide layouts.
  - `NETWORK_SIMPLEX` — auxiliary-graph network simplex (Gansner et al.). More balanced placement, more centered nodes, slightly longer edges.
  - `SIMPLE` — explicitly marked "not for production use" in the ELK source.
  - `INTERACTIVE` — preserves user-specified positions.
- **Edge routing modes** (the single biggest visual lever for architecture diagrams):
  - `ORTHOGONAL` — produces draw.io-style right-angle edges; what you want for almost all architecture work.
  - `POLYLINE` — straight segments with bends only where necessary; cleaner for dense graphs.
  - `SPLINES` — smooth curves; aesthetic for flowcharts but rarely a fit for architecture.
- **Practitioner options to set** (`org.eclipse.elk.*`): `direction` (DOWN/RIGHT), `spacing.nodeNodeBetweenLayers`, `layered.nodePlacement.bk.fixedAlignment`, `layered.nodePlacement.bk.edgeStraightening` (trade diagram size for straight edges), `layered.mergeEdges`, `hierarchyHandling=INCLUDE_CHILDREN` (essential for nested containers / swimlanes).

**dagre internals** (what Mermaid, Excalidraw+, and many React Flow apps actually use):
- Implements the Sugiyama skeleton from Gansner et al. "A Technique for Drawing Directed Graphs" with Brandes–Köpf for coordinates.
- **Three rankers**: `network-simplex` (default, precise), `tight-tree` (reduce long edges), `longest-path` (fast DFS, but many long edges).
- **Known limitations** (verbatim from D2's docs and dagre's wiki):
  - "Layout algorithm is strictly hierarchical, even if underlying diagram is not hierarchical."
  - "Container child to another container (or another container child) is not natively supported by dagre."
  - Edge length variability is high (documented in the *Visualizing Evolving Trees* paper).
  - No native re-layout on graph mutation — you must re-run.
- **When to use anyway**: small flowcharts, sequence-of-steps. **When to avoid**: anything with nested containers, swimlanes, cloud-account boundaries.

**TALA (Terrastruct AutoLayout Approach)** — the only widely-available layout engine designed *specifically* for software-architecture diagrams:
- Closed-source, ships as a D2 plugin binary (`d2plugin-tala`); free to evaluate with a watermark, requires a paid Terrastruct license for clean output.
- Distinguishing properties (per Terrastruct's TALA docs and blog series):
  - **First-class containers** at every stage of layout (vs dagre/ELK where containers are bolted on).
  - **Orthogonal pathing** as default (matches what humans whiteboard).
  - **Clusters / trees / hierarchies auto-identified** as subsections, so you can mix hierarchical and non-hierarchical structures in one diagram.
  - **Symmetry-preferring** placement — important for mirrored multi-region cloud diagrams.
  - Layout is heuristic ("Optimal placements of nodes that minimizes distance and crossings is an NP-hard problem. TALA searches with heuristics to get an approximation"); pin a seed for reproducibility.
  - Per-section `direction` overrides (unique among D2 engines — dagre/ELK only support a global direction).
- **Compatibility caveat**: TALA renders SVG/PNG via D2. No clean SVG→draw.io XML round-trip; for Lucidchart compatibility you'd import the SVG as an image, not as editable shapes.

**OGDF (Open Graph Drawing Framework)** — C++ library with a recent Python wheel. When to choose over ELK:
- Planar drawing algorithms and the *planarization approach* (explicit crossing dummies) — useful when you genuinely need a planar-ish architecture diagram.
- Multilevel mixer for *very large* graphs (1000+ nodes) where ELK gets slow.
- More sophisticated cluster/compound-graph layouts.
- Downsides: C++ build, no first-class JS port, weaker tooling integration, slower iteration in a Claude Code loop.

**Graphviz engines** — use as one-line tools, not as part of a generation pipeline:

| Engine | What it's for | When to use for architecture |
|---|---|---|
| `dot` | DAGs/hierarchies, Sugiyama | C4 container / component diagrams, deployment trees |
| `neato` | Undirected spring-model (Kamada-Kawai) | Service-dependency graphs without hierarchy |
| `fdp` | Force-directed (Fruchterman-Reingold) | Same as neato for medium graphs |
| `sfdp` | Multi-scale force-directed | 500+ node service maps |
| `twopi` | Radial — concentric circles by distance | Hub-and-spoke topologies |
| `circo` | Circular — biconnected components on circles | Ring/cyclic topologies (HA clusters) |
| `osage` | Cluster-structure layout | Multi-tenant or multi-region groupings (competes with TALA for this niche) |
| `patchwork` | Squarified treemap | Cost/capacity diagrams; not real architecture |

**cytoscape.js layouts** (relevant if you ever embed a diagram in a portal/dashboard):
- `cose` — spring embedder, OK quality, tune-heavy.
- `cose-bilkent` — *Compound Spring Embedder* from Bilkent University with first-class **compound (nested) nodes** + non-uniform node sizes. Cite: Dogrusoz et al., *Information Sciences* 179, 2009.
- `fcose` — **fCoSE: A Fast Compound Graph Layout Algorithm with Constraint Support** (Balci & Dogrusoz, IEEE TVCG 28(12) pp. 4582–4593, 2022). ~2× faster than cose-bilkent and adds fixed-position / vertical-horizontal alignment / relative-placement constraints. **Best free option for nested containers in JS.**
- `elk`, `dagre`, `klay` — wrappers; same characteristics as upstream.

**yFiles** (commercial, enterprise diagramming SDK; Lucidchart-class quality, heavy license). Publicly documented algorithms (yWorks docs at docs.yworks.com/yfiles-html/dguide/automatic-layouts-main-chapter):
- HierarchicLayout (Sugiyama; flagship), OrganicLayout (force-directed), OrthogonalLayout, TreeLayout (multiple sub-placers), RadialTreeLayout (ex-Balloon), RadialLayout, CircularLayout, SeriesParallelLayout, CompactDiskLayout, RadialGroupLayout (ex-Cactus), EdgeRouter (orthogonal/octilinear/curved/bus), OrganicEdgeRouter, RemoveOverlaps.
- Not directly usable in a Claude Code loop, but worth knowing because many polished commercial diagramming UIs you meet at clients use yFiles under the hood.

**MSAGL (Microsoft Automatic Graph Layout)** — under-appreciated MIT-licensed library:
- Algorithms (per the .NET source and the MSAGL.js port `microsoft/msagljs`): **Sugiyama layered** with Brandes x-coords and modified Coffman–Graham scheduling, **MDS (Multi-Dimensional Scaling)**, **IPSepCola** (Incremental Procedure for Separation-Constraint Layout — best-in-class for constrained undirected layouts), **FastIncrementalLayout** for interactive updates, **LGL/GraphMaps** for large-graph zoomable visualization, orthogonal/rectilinear edge routing.
- Activity: lightly maintained as of 2024–2026. Main repo `microsoft/automatic-graph-layout` has slower cadence than ELK or yFiles; `microsoft/msagljs` describes itself as "currently under development."

### 3. Benchmarks, evals, and datasets

| Name | Scope / size | Where it lives | Practitioner adoption |
|---|---|---|---|
| **MermaidSeqBench** | 132 NL→Mermaid sequence-diagram pairs; LLM-as-judge over syntax correctness / activation handling / error handling / practical usability | arxiv.org/abs/2511.14967 ; IBM Research page | Initial evaluations across Qwen 2.5, Llama 3.1/3.2, Granite 3.3 with multiple LLM judges. Locally reproducible — point at your model's API. |
| **DiagramEval** | Metric, not a fixed dataset: parse SVG → graph (text = nodes, connections = directed edges) → Node Precision/Recall/F1 + Path Precision/Recall/F1 | arxiv.org/abs/2510.25761 ; github.com/ulab-uiuc/diagram-eval | Validated on 361 CVPR 2025 paper diagrams across Llama 4 Maverick / Gemini 2.5 Pro / Claude 3.7 Sonnet. Most worth porting to architecture diagrams. |
| **AI2D-Caption** | Densely-annotated diagram dataset on top of AI2D (built for DiagrammerGPT) | huggingface.co/papers/2310.12128 | Educational/science diagrams; less architecture-relevant but useful as a smoke test. |
| **DaTikZv2** | 360k+ human-authored TikZ graphics | HF dataset linked from DeTikZify repo | Largest open dataset of structured diagram code. Use for fine-tuning if you ever bring training in-house. |
| **SketchFig + MetaFig** | Sketch↔figure pairs, plus figure metadata | Linked from DeTikZify | Sketch-to-diagram reproducibility. |
| **Eraser DiagramGPT eval** | Internal, not public | eraser.io/diagramgpt | Not reproducible; reference point only. |
| **GenAI-DrawIO-Creator eval** | Simulated structural-fidelity check on draw.io XML | arxiv.org/html/2601.05162v1 | The only published eval focused on drawio XML. Re-implement their structural-fidelity check (valid mxGraphModel + all named nodes present + no orphan edges) as a unit test in your skill. |

**General LLM benchmarks that include diagram tasks**: As of May 2026, **LiveBench, BFCL, SWE-bench do not include diagram-generation tasks**. SWE-bench Verified has zero diagram tasks. Diagram-specific benchmarks (MermaidSeqBench, DiagramEval) remain the only meaningful signal.

**Classical aesthetic / layout-quality metrics** worth adopting as a CI gate (cheap, deterministic):
1. **Number of edge crossings** — canonical metric since the early '80s. Extract edges from mxGraphModel and run a sweep-line.
2. **Number of node overlaps** — count pairs (a, b) where bounding boxes intersect.
3. **Edge length variance** (Brandes–Köpf optimizes this; you want it low).
4. **Area utilization** — bounding-box area ÷ sum-of-node-area.
5. **Orthogonality conformance** — % of edges that are purely orthogonal.
6. **Container nesting consistency** — every node has `parent` consistent with its visual containment.
7. **Symmetry / angular resolution** — secondary.

You can implement gates 1–6 in ~150 lines of Python on top of the parsed mxGraphModel; they correlate well with "this diagram looks clean."

### 4. Active open-source projects, conferences, communities

**Conferences worth tracking (rank order for your use case):**
1. **Graph Drawing & Network Visualization (GD)** — annual since 1992. Proceedings now in LIPIcs (open access since 2024). GD 2024 in Vienna; GD 2024 LIPIcs vol. 320 (ISBN 978-3-95977-343-0). Track 2 papers are invited to JGAA / IEEE TVCG. Where new layout algorithms ship.
2. **NeurIPS / ICML / EMNLP / ACL / COLM** — DiagrammerGPT (COLM '24), DeTikZify (NeurIPS '24 spotlight), MermaidSeqBench (NeurIPS '25 workshop), DiagramEval (EMNLP '25 main) all appeared here.
3. **CHI / UIST** — diagram tooling and HCI evaluations (e.g., human-in-the-loop diagram editing). Lower hit rate but high signal when they hit.
4. **IEEE VIS / EuroVis / IEEE TVCG** — fCoSE was published in TVCG; classical layout-quality metric work continues here.
5. **Diagrams (International Conference on the Theory and Application of Diagrams)** — Diagrams 2024 Münster, Springer LNCS; mostly diagrammatic-reasoning theory, lower practitioner ROI.

**Active open-source repos with momentum** (May 2026):

| Repo | What it is | Status |
|---|---|---|
| `eclipse-elk/elk` | The reference layout kernel | Actively maintained; 2025 blog series on Layered internals at eclipse.dev/elk/blog/posts/2025 |
| `terrastruct/d2` and `terrastruct/TALA` | D2 lang + TALA layout | Very active; weekly-cadence releases |
| `dagrejs/dagre` | The Mermaid / React Flow default | Maintenance-mode but stable |
| `iVis-at-Bilkent/cytoscape.js-fcose` | Best free compound-graph layout | Active |
| `potamides/DeTikZify` | Sketch / figure → TikZ | v2 8b Dec 2024; TikZero adapters Mar 2025 |
| `DayuanJiang/next-ai-draw-io` + `drawio-mcp-server` npm | Direct AI-to-drawio with MCP | Most active drawio-MCP integration as of May 2026 |
| `ulab-uiuc/diagram-eval` | DiagramEval reference impl | New (EMNLP '25), needs adopters |
| `microsoft/vscode-mermAId` | Microsoft's experimental Copilot Chat → Mermaid extension | Experimental |
| `ogdf/ogdf` and `ogdf/ogdf-python` | OGDF + new Python wheel | Active |
| `jgraph/drawio` | Reference for mxGraph XML schema | Active; AI generation FAQ at drawio.com/doc/faq/ai-drawio-generation |

**Communities**:
- **Eraser Slack** — small but high signal.
- **Terrastruct Discord / GitHub Discussions** — primary venue for D2/TALA users.
- **r/drawio**, **r/PlantUML**, **r/diagrams** — low traffic but useful.
- **Mermaid Discord and GitHub Discussions** — highest-traffic diagram-as-code community.
- **C4 Model Slack** (`structurizr.com/help/slack`) — for Structurizr DSL practitioners.
- **GitHub `topic:diagram-as-code`** — best discovery surface for new tools.

### 5. Commercial tools — proprietary layout and AI features

| Tool | Underlying layout | AI model (disclosed) | .drawio export | Pricing tier (May 2026) | Practitioner verdict |
|---|---|---|---|---|---|
| **draw.io's own AI** | Native mxGraph; AI emits XML directly | User-configurable: Gemini 2.5/3 Pro, Claude Sonnet 4.5/Haiku 4.5/Sonnet 4.0/3.7, GPT-5.1/4.1/4o | **Yes — native** | Free (BYOK) | Cleanest choice for your workflow. Use the bare `<mxGraphModel>` fragment pattern from drawio.com/doc/faq/ai-drawio-generation. |
| **Lucidchart AI / Co-create / Smart Containers** | Proprietary "visual reasoning engine"; no public algorithm disclosure | Not disclosed | **No native drawio export**; can import Mermaid | Free (3 documents), **Individual $9/user/mo**, **Team $10/user/mo**, **Enterprise ~$12.17/user/mo** (custom-quoted; plan names verified May 2026 — Lucid does *not* use "Standard/Pro" naming) | Useful for client whiteboards. Smart Containers auto-group by a dataset column. Stick with draw.io for engineering work. |
| **Eraser DiagramGPT** | Eraser's own diagram-as-code (DAC) format | **OpenAI GPT-4** (officially stated on eraser.io: "DiagramGPT was created by the team at Eraser, leveraging OpenAI's models") | No, but can output PlantUML / Mermaid | Free tier; Starter, Business, Enterprise tiers with API access | Best UI for cloud-architecture diagrams; export Mermaid/PlantUML then convert. Good for fast PoCs. |
| **Miro AI** | Proprietary; standard Miro shapes & connectors | Mix of OpenAI + Anthropic (per Miro AI reference docs); not user-selectable | No (PNG/PDF/Miro file only); *imports* Lucidchart/Visio/.drawio | Free / Starter / Business / Enterprise; AI credits consumed per generation | Flowcharts / UML class / ER / sequence — good. Cloud architecture — weak. |
| **Whimsical AI** | Proprietary auto-layout | **Anthropic Claude** (officially named on whimsical.com/ai/ai-text-to-flowchart: "Turn a simple text prompt into a complex flowchart with Whimsical AI powered by Claude") | **No** (PNG/PDF/SVG/Markdown only; free plan watermarked) | Pro ~$12/editor/mo, Business ~$18, Enterprise ~$20 | Pleasant UI; thin diagram-type coverage. |
| **Excalidraw+ AI** ("Text to Diagram", "Wireframe to Code") | Generates Mermaid under the hood, then renders via Mermaid → Excalidraw shapes | Undisclosed default; supports **BYOK** (your OpenAI/Anthropic key) | **No** (PNG/SVG/.excalidraw JSON) | Excalidraw+ ~$6/editor/mo; 100 AI requests/day | Great for casual whiteboards; Mermaid intermediary means parse errors on parens-in-labels are a known recurring issue (GitHub issue #10562). |
| **Mermaid Chart Pro / Mermaid AI** | Mermaid.js (dagre + ELK) | Not officially named; Mermaid Chart GPT in OpenAI's GPT Store implies GPT-4-class for that surface | No native drawio export, but **draw.io natively imports Mermaid** — your effective bridge | Free / Pro (~$80/yr or ~$6.67/user/mo) / Premium (large teams, SSO) / Enterprise | The most useful "AI-first" tool for your draw.io workflow precisely because draw.io can ingest Mermaid. |
| **Microsoft Visio + Copilot** | Visio's built-in hierarchic/flowchart layouts; Data Visualizer add-in for Excel-to-flowchart | **No Copilot integration in Visio** (officially confirmed on Microsoft Q&A Nov 2025: "At this time, Microsoft has not announced any official plan, and this feature is not currently on the roadmap") | N/A | Visio Plan 1 ~$5/user/mo, Plan 2 ~$15; M365 Copilot $30 add-on | Avoid Copilot-in-Visio expectations for client PoCs in 2026. |
| **FigJam AI (Figma)** | FigJam connector auto-routing; no published algorithm | Undisclosed (Figma AI). Figma Make uses Anthropic Claude (separate product). | No | Free; Collab ~$3–5/mo; Full seat $15–90/mo. Pro AI credits 3,000/mo (don't roll over from March 18, 2026) | Can generate flowcharts, Gantt, org charts only. No UML/ER/C4/network/BPMN native. |
| **Notion AI** | None native; relies on Mermaid code blocks (since Dec 23 2021) | Mix of Claude + OpenAI GPT (not user-selectable) | No (Mermaid in code blocks → import to drawio) | Notion AI add-on ~$8–10/user/mo | Effectively "Notion as a Mermaid editor with an LLM in the sidebar." |
| **GitHub Copilot + Mermaid in PRs** | Mermaid.js (GitHub renders natively in Markdown / issues / PRs / wikis) | GPT-4o / GPT-5 / Claude 3.5/4 Sonnet / Gemini (user-selectable) | Mermaid text → drawio imports it | Copilot Individual ~$10, Business ~$19, Enterprise ~$39 /user/mo | Excellent for issue/PR-level diagrams. Known issue: Copilot inserts invalid characters in Mermaid output, requiring round-trip fixes. |
| **yFiles** (commercial SDK, used inside many enterprise tools) | Hierarchic, Organic, Orthogonal, Tree, Circular, Radial, RadialTree, SeriesParallel, CompactDisk, RadialGroup + OrganicEdgeRouter | N/A (library) | N/A | Per-developer commercial license | Worth knowing because polished commercial diagramming UIs you meet at clients often use yFiles under the hood. |

### 6. Tangible delta — what's NEW vs the previous report

**New papers to read (top 5, ranked):**
1. **DiagramEval (Liang & You, EMNLP 2025)** — adopt their graph-based metric as your CI quality gate (most direct ROI for an EPAM SA). arxiv.org/abs/2510.25761
2. **MermaidSeqBench (Shbita et al., NeurIPS 2025 workshop)** — first reproducible benchmark; run it against your skill stack. arxiv.org/abs/2511.14967
3. **See it. Say it. Sorted. (Zhang, Liu, Li, 2025)** — Critic-Candidates-Judge loop is directly portable into Claude Code. arxiv.org/abs/2508.15222
4. **DeTikZify v2 + TikZero (Belouadi et al., NeurIPS 2024 spotlight; updates 2024–2025)** — MCTS self-refinement against a compile-success reward is the canonical pattern. arxiv.org/abs/2405.15306
5. **The Eclipse Layout Kernel (Domrös et al., arXiv 2311.00533)** — definitive ELK reference; read before tuning options.

**New tools/projects to evaluate (top 5, ranked):**
1. **`drawio-mcp-server` + `next-ai-draw-io` (DayuanJiang)** — most active drawio-MCP integration; supports the same models you already use. `npx -y drawio-mcp-server --editor`. github.com/DayuanJiang/next-ai-draw-io
2. **TALA (Terrastruct)** — only software-architecture-specific layout engine available; first-class containers. Even if you don't adopt D2 long-term, *run the same diagram through TALA once* to see the gold-standard layout. github.com/terrastruct/TALA
3. **ELK Layered with `hierarchyHandling=INCLUDE_CHILDREN` + `BRANDES_KOEPF` + ORTHOGONAL** — default for production-quality nested-container layouts from JS or Java. eclipse.dev/elk
4. **cytoscape.js-fcose** — best free compound-graph layout with constraints (TVCG 2022). github.com/iVis-at-Bilkent/cytoscape.js-fcose
5. **DiagramEval reference implementation** — drop into CI. github.com/ulab-uiuc/diagram-eval

**New layout-quality metrics to adopt as a quality gate (in this order):**
1. **Node F1 + Path F1** (DiagramEval) — primary; the EMNLP 2025 paper shows these correlate substantially better with human judgment than CLIPScore.
2. **Number of edge crossings** on the parsed mxGraphModel — cheap, deterministic, catches Sugiyama failures.
3. **Number of node overlaps** — catches Claude's #1 failure mode.
4. **Container nesting consistency** — every shape's `parent` matches its visual containment.
5. **Orthogonality conformance** — % of edges that are purely right-angle.
6. **Edge length variance** — secondary; low values indicate a healthy layered layout.

**Conferences to track ongoing:** GD (LIPIcs proceedings, open access), NeurIPS / EMNLP / COLM for LLM-side, IEEE VIS / TVCG for layout-side, CHI for HCI-side. Skip Diagrams (theory-heavy, low practitioner ROI).

**Commercial tools worth testing for client-facing PoCs (vs always reaching for drawio + Claude):**
- **For a *first-impression* client whiteboard**: Eraser DiagramGPT (best UX for cloud architecture). Output Mermaid/PlantUML, then convert.
- **For *brainstorming with non-technical stakeholders*** (PMs, marketing): Miro AI or FigJam AI. Limited to flowchart-style outputs.
- **For *spec-heavy documentation*** that lives next to code: Mermaid Chart Pro + GitHub Copilot's Mermaid generation; round-trip through drawio's Mermaid import.
- **For *Lucidchart-required clients***: Lucidchart's "Generate with AI" feature → manual fix-up. Not worth abandoning draw.io as your source of truth.

**Specific next experiments Yuriy should run:**
1. **Plug DiagramEval into your skill's eval folder.** Generate 20 reference architecture diagrams with Claude Sonnet 4.6 + the JGraph skill, score Node F1 / Path F1, track on every skill change.
2. **Add a hard quality gate to the JGraph skill**: count edge crossings + node overlaps from the parsed mxGraphModel; if either > N, force a retry with a layout-correction prompt that quotes the offending node IDs back to the model.
3. **A/B test the Critic-Candidates-Judge loop from "See it. Say it. Sorted."** against your current single-pass generation. Use Claude as Critic, three Claude sub-agents as Candidates (conservative/aggressive/focused), and Claude with vision as Judge over a rendered PNG.
4. **Try the `drawio-mcp-server` from DayuanJiang** in Claude Code. Compare against the existing JGraph skill on the same five test prompts. Decide whether to switch.
5. **Run the same five diagrams through TALA** (free evaluation mode, ignore the watermark) and compare layout quality side-by-side with ELK and dagre. Even if you don't adopt TALA, the comparison will reveal which ELK options to tune.
6. **Adopt the bare `<mxGraphModel>` (no `<mxfile>` wrapper) pattern** from drawio.com/doc/faq/ai-drawio-generation in every skill — drawio auto-wraps it on open, and shorter prompts have measurably lower XML-syntax error rates.
7. **For C4-required engagements**, keep PlantUML C4 + Catalyst as the source of truth and use this expansion's layout-tuning advice only for the post-export draw.io pass.

## Recommendations

**Immediate (this sprint):**
- Add the bare-`<mxGraphModel>`-fragment instruction to your lucidchart-drawio, OpenAEC, and JGraph skills' system prompts.
- Install `drawio-mcp-server` in your Claude Code environment and run a side-by-side comparison with your existing skill on 5 representative prompts.
- Implement edge-crossings + node-overlaps + container-nesting-consistency as a ~150-line Python post-check that runs after every diagram generation.

**Within a month:**
- Stand up DiagramEval as a CI quality gate against a fixed evaluation set of 20 reference architectures.
- Adopt the Critic-Candidates-Judge loop for any diagram with >15 shapes.
- Evaluate TALA on three representative architectures; if Node F1 ≥ +5% over ELK on your set, add a D2/TALA generation path as a fallback for complex diagrams.

**Within a quarter:**
- Subscribe to GD 2026 (LIPIcs) and NeurIPS / EMNLP diagram-generation tracks.
- Decide whether the JGraph skill should optionally output Mermaid (for Lucidchart compatibility via Lucid's Mermaid import) in addition to .drawio XML.

**Benchmarks/thresholds that would change these recommendations:**
- If Node F1 on your eval set < 0.5 with Sonnet 4.6 → escalate to Opus 4.7 for diagram tasks (the EMNLP 2025 baseline numbers — Claude 3.7 Sonnet at Node-F1 0.3500 on research-paper diagrams — suggest you should expect ~0.50–0.60 on simpler architecture diagrams; anything lower is a real regression).
- If edge-crossings count > (|V|/2) on graphs with > 12 nodes → switch from inline LLM-coord generation to "LLM emits graph + ELK lays it out + serialize to mxGraphModel."
- If the JGraph skill cannot pass container-nesting-consistency on 95%+ of your eval set → add an explicit nesting-validation pass in the skill itself.

## Caveats

- The 2025/26 **GenAI-DrawIO-Creator** paper (arXiv 2601.05162) — the numeric arXiv ID is unusual and the paper is described as a preprint with simulated evaluations; treat structural-fidelity numbers as indicative, not benchmarked. The associated GitHub (`DayuanJiang/next-ai-draw-io`) is real and active.
- **MermaidSeqBench** covers *sequence diagrams only*, not architecture/container/component diagrams; useful as a regression gate for skill-pack changes but not directly representative of your typical workload. The specific judge models used in the evaluations are not confirmed from the snippets retrieved; consult the v2 paper appendix for exact judge configuration.
- **DiagramEval** was validated on research-paper figures (CVPR 2025), not architecture diagrams; the metric should transfer but the absolute thresholds (what counts as "good Node F1") will need recalibration on your own reference set. The numbers cited (Node-F1 0.35, Path-F1 0.24 for Claude 3.7 Sonnet) come from Table 1 of the EMNLP paper.
- **TALA is closed-source and requires a paid Terrastruct license** for non-watermarked output in commercial use; budget accordingly before standardizing.
- **Several AI-model attributions for commercial tools are not officially disclosed** (Mermaid Chart's AI chat, Excalidraw+ default model, Miro AI default, FigJam AI default). Where I have an explicit named source (Whimsical = Claude, Eraser = OpenAI's models) I've cited it; otherwise treat the model name as inferred. Notably, "See it. Say it. Sorted." actually used Gemini-2.5-Pro/Flash in its reference implementation, not Claude — Claude would be your *adaptation* of the pattern.
- **Lucidchart's current plan names are Free / Individual / Team / Enterprise** (verified May 2026 via independent pricing trackers); there is no "Standard" or "Pro" plan despite occasional secondhand sources using that terminology.
- The earlier report's coverage of Claude Opus 4.7 / Sonnet 4.6, the JGraph drawio-mcp skill, OpenAEC-Foundation skill, lucidchart-drawio skill, Structurizr DSL+MCP, PlantUML C4 + Catalyst, EasyC4, Mermaid limitations for C4, and D2 with dagre/ELK/TALA basics **remains valid**; this expansion deepens the layout / benchmark / commercial picture without superseding it.