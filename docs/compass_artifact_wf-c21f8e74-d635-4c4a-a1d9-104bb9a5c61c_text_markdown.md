# Best LLMs and Claude Code Skills for Generating draw.io / Lucidchart Architecture Diagrams (May 2026)

## TL;DR

- **Best end-to-end workflow today:** Drive **Claude Opus 4.7** (or Sonnet 4.6 for cost) from Claude Code, layered with the **official jgraph `drawio` skill** (`/plugin marketplace add jgraph/drawio-mcp`) **plus your existing `lucidchart-drawio` skill** for layout patterns, **plus** the `drawio-impl-swimlanes` skill from the OpenAEC-Foundation pack for correct container-relative coordinates. This produces native `.drawio` mxGraph XML that opens directly in draw.io for editing.
- **Best intermediate format when grouping/auto-layout matters more than pixel control:** **Structurizr DSL** with the official Structurizr MCP server (`docker run structurizr/mcp`) → export to **PlantUML** → convert to `.drawio` via the **`localgod/catalyst`** library or the hosted **EasyC4 Diagram Creator** (`https://c4.wtx.pl`). Simon Brown's tooling enforces the C4 hierarchy and is explicitly designed for LLM generation. Mermaid C4 is **not** recommended — draw.io currently imports it as a flat image (jgraph/drawio issues #3870, #5377).
- **Avoid LLM-only raw XML coordinate math for large diagrams.** Across every skill we examined, the failure mode is identical: overlapping shapes, edges drawn over icons, wrong parent IDs in swimlanes. The fix is structural — use a skill that bakes in the *container-relative coordinate rules* (OpenAEC `drawio-impl-swimlanes`, OpenAEC `drawio-impl-generator` with Sugiyama auto-layout, or your own `lucidchart-drawio` skill with named patterns).

---

## Key Findings

1. **Claude Opus 4.7 is the strongest general model for diagram XML correctness in May 2026.** It posts 87.6% on SWE-bench Verified and 98.5% visual acuity (up from 54.5% on Opus 4.6), and Anthropic specifically calls out *"dense-screenshot computer use, complex diagram extraction, and pixel-perfect reference tasks"* as Opus 4.7 strengths. Sonnet 4.6 is the right default at ~1/5 the cost — it scores 79.6% on SWE-bench Verified, only 1.2 pts behind Opus 4.6. Per Anthropic's official launch post *"Introducing Claude Sonnet 4.6"* (February 17, 2026): *"Users even preferred Sonnet 4.6 to Opus 4.5, our frontier model from November, 59% of the time. They rated Sonnet 4.6 as significantly less prone to overengineering and 'laziness,' and meaningfully better at instruction following."*
2. **There is no public benchmark that specifically scores LLMs on draw.io XML generation.** The closest is **MermaidSeqBench** (arXiv:2511.14967v1, submitted November 18, 2025, by Basel Shbita, Farhan Ahmed, and Chad DeLuca of IBM Research San Jose, presented at the NeurIPS 2025 Workshop *"Evaluating the Evolving LLM Lifecycle: Benchmarks, Emergent Abilities, and Scaling"* — 132 samples for Mermaid *sequence* diagrams) and the **GenAI-DrawIO-Creator** paper (AWS Generative AI Innovation Center, arXiv 2601.05162v1) which built a Claude 3.7-based prototype with specialized prompts + XML post-processing. The arXiv paper explicitly observes that *"free-form text generation easily leads to syntax mistakes or hallucinated content that breaks the diagram"* — i.e., raw LLM coordinate output is the failure mode you want to avoid.
3. **The official jgraph `drawio-mcp` repo now ships three delivery mechanisms**: (a) MCP App Server (renders inline in MCP-Apps-aware chat hosts, hosted at `https://mcp.draw.io/mcp`), (b) `@drawio/mcp` npm tool server (opens in browser), and (c) **`skill-cli/`** — a Claude Code Skill that generates native `.drawio` files directly with no MCP setup. A canonical `shared/xml-reference.md` covers edge routing, containers, layers, tags, and dark mode, and is loaded by every delivery mechanism at startup.
4. **Structurizr does not export to draw.io natively.** Its CLI exports to PlantUML, C4-PlantUML, Mermaid, DOT, Ilograph, WebSequenceDiagrams, JSON, PNG/SVG — no `mxgraph`/`drawio` format. Simon Brown's recommended bridge is the third-party **EasyC4 Diagram Creator** (https://c4.wtx.pl) which converts PlantUML/Mermaid C4 → `.drawio` XML.
5. **Mermaid C4Context/C4Container imports into draw.io are currently broken.** jgraph/drawio issue #3870 reports *"Inserting a mermaid diagram with a C4Context doesn't result in a diagram… Workaround: Export mermaid to svg and then insert as image."* Issue #5377 confirms non-trivial Mermaid (including C4 examples) imports as a flat SVG/PNG, losing editability. Use PlantUML C4 → Catalyst/EasyC4 for editable round-trip.
6. **D2's TALA engine is the highest-quality auto-layout for software architecture** but is **paid-only and proprietary**. The free engines bundled with D2 are **dagre** (default, fast, Graphviz-DOT-based) and **ELK** (more mature, supports `width`/`height` on containers, hierarchical). D2 exports to SVG/PNG/PDF only — there is **no D2 → drawio exporter**, so D2 is a dead end if drawio editability is mandatory.
7. **The "container-relative coordinate" rule is the #1 source of swimlane bugs from LLMs.** The OpenAEC `drawio-impl-swimlanes` SKILL.md states this explicitly as *"the #1 swimlane mistake: using absolute coordinates for children instead of container-relative coordinates"* and is the most concrete piece of prompt engineering available to fix it.

---

## A) LLM Comparison for Diagram-as-Code / drawio XML Generation

### Capability matrix (May 2026)

| Model | XML correctness | Spatial coherence | Grouping/nesting | Long-output (large diagrams) | Cost | Recommendation |
|---|---|---|---|---|---|---|
| **Claude Opus 4.7** | Best | Best — 98.5% visual acuity, 128K max output | Best — handles deep container trees | 128K output, 200K context (1M beta) | $5 / $25 per Mtok | **Use for complex, multi-page diagrams and any time the diagram has >40 nodes or nested swimlanes** |
| **Claude Sonnet 4.6** | Very good | Very good | Very good | 200K context | $3 / $15 per Mtok | **Default workhorse** — Anthropic's own "build-by-default" model |
| **Claude Haiku 4.5** | Adequate for flowcharts | Weaker on dense layouts | OK for shallow nesting | Smaller | Cheap | Triage / fast iteration only |
| **GPT-5 / GPT-5.1** | Good; documented willingness to add unrequested validation logic | Good but more verbose | Good | Good | Comparable to Sonnet | Strong alternative. In *"Benchmarking GPT-5.1 vs Gemini 3.0 vs Opus 4.5 across 3 Coding Tasks"* (Darko, kilo.ai, November 26, 2025), GPT-5.1's analysis *"Included a Mermaid sequence diagram showing exactly how events propagate through the system"* and *"Referenced specific line numbers for every claim"* — useful for code-comprehension-driven diagrams |
| **Gemini 3 Pro** | Concise — same kilo.ai November 26, 2025 article notes: *"Claude Opus 4.5 was the fastest at 1 minute while producing the most complete implementation (936 lines with templates for all 7 notification events). Gemini 3.0 provided a concise, high-level summary (51 lines)."* | Reasonable for small diagrams | OK | Long context | Comparable | Use when you want short, abstract overviews; arXiv 2508.15222 (*"See it. Say it. Sorted."*) found *"our method more faithfully reconstructs layout and structure than two frontier closed-source image generation LLMs (GPT-5 and Gemini-2.5-Pro), accurately composing primitives (e.g., multi-headed arrows) without inserting unwanted text"* — i.e., without an agentic critic loop, both frontier models drift |
| **DeepSeek-V3 / DeepSeek-R1** | Mixed; community reports OK XML but weaker than Claude on deep nesting | Mid-tier | Mid-tier | Long context | Very cheap | Cost-driven option; less battle-tested for drawio specifically |
| **Qwen 3 / Qwen3-Coder** | Good for Mermaid/PlantUML; raw mxGraph XML mixed | Reasonable | Mid-tier | Long context | Cheap | Reasonable open-weights fallback |
| **GLM-4.7 (Zhipu)** | Limited public reporting on diagram tasks | — | — | — | Cheap | Insufficient public data; do not rely on for client work without your own eval |
| **Grok 4** | Limited public reporting | — | — | — | — | Insufficient public data |

**Spatial-reasoning caveat (well-documented).** arXiv 2508.15222 (the "See it. Say it. Sorted." paper, evaluated on 10 sketches from published-paper flowcharts) explicitly demonstrates that frontier closed-source image models (GPT-5 and Gemini-2.5-Pro) struggle to preserve structure unless wrapped in an agentic critic/judge loop. The AWS GenAI-DrawIO-Creator paper draws the same conclusion for Claude 3.7 producing draw.io XML: you need *"specialized techniques for prompting and XML post-processing"* — i.e., a skill, not just a model.

### Strength/weakness summary for the specific task

- **Best at raw mxGraph XML with absolute coordinates:** Claude Opus 4.7 + a skill that enforces container-relative coords (OpenAEC `drawio-impl-swimlanes`). Without the skill, every model — including Opus — produces overlapping shapes on dense diagrams (this is documented in dev.classmethod.jp's hands-on writeup of the official drawio skill: *"labels overlapping icons, connection lines drawn over icons, missing VPC and subnet boundaries"* until SKILL.md was augmented).
- **Best at Structurizr DSL:** Claude Sonnet 4.6 and Opus 4.7. Simon Brown himself reports good results with Claude on Structurizr DSL on LinkedIn, with the caveat that *"AI is non-deterministic. Ask an AI agent to generate a diagram from a codebase multiple times and you'll get a different answer each time"* — so use Structurizr's MCP `Validate Structurizr DSL` tool to gate output.
- **Best at PlantUML / C4-PlantUML:** Claude Sonnet 4.6. ChatGPT/GPT-5 has been observed to hallucinate outdated AWS-PlantUML imports (per Dejan Vukmirović on Medium, "Few good cases for using LLM as Software Architect part 2") — Claude requires fewer manual fixes.
- **Best at Mermaid:** All frontier models are competent; MermaidSeqBench shows wide variation by sub-metric (syntax correctness, activation handling, error handling, usability). Mermaid is your safest format for *sequence* and *flowchart* round-trips into drawio; do **not** use Mermaid C4 for drawio import.
- **Best at D2:** Lightly tested in public benchmarks. D2's grammar is small and Claude/GPT handle it well, but the layout quality comes from D2's engine (TALA/ELK/dagre), not the model.

---

## B) Claude Code Plugins, Skills, and Agents for Architecture Diagrams

### Tier 1 — Install these first

1. **jgraph/drawio-mcp `skill-cli/`** (the official draw.io skill for Claude Code) — `https://github.com/jgraph/drawio-mcp/tree/main/skill-cli`. Generates native `.drawio` directly, optional PNG/SVG/PDF export via draw.io desktop CLI (`--embed-diagram` keeps source editable). Loads canonical XML reference from `shared/xml-reference.md` at runtime. **No MCP setup required.** Best baseline.
2. **Your existing `lucidchart-drawio` skill** (the one already installed locally) with its hub-radial, scope-columns, swimlanes, LR data pipeline, and tenant-namespace patterns. This is rare and valuable — these are **named layout templates** that constrain the LLM's choices, which is exactly the structural fix needed for clean output.
3. **OpenAEC-Foundation Draw.io-Claude-Skill-Package** — `https://github.com/OpenAEC-Foundation/Draw.io-Claude-Skill-Package`. 22 deterministic skills + an MCP server (`pip install drawio-mcp`) with **Sugiyama (DAG), tree, grid, and flowchart auto-layout**, 310+ shape presets, themes, and crucially `drawio-impl-swimlanes` which enforces parent-child geometry rules. Complementary to your `lucidchart-drawio` skill.
4. **`@drawio/mcp` (npm)** or **`https://mcp.draw.io/mcp`** (hosted, no install) — when you want diagrams rendered inline in Claude Desktop / Cowork via MCP Apps. Useful for client demos.

### Tier 2 — Use selectively

- **`little-hands/claude-drawio-skill`** (`/plugin marketplace add little-hands/claude-drawio-skill` → `/plugin install draw-io@claude-drawio-skill`). Lightweight CRUD on `.drawio` files; good for simple flowcharts and ERDs. Less layout discipline than OpenAEC.
- **`Agents365-ai/drawio-skill`** — natural-language → `.drawio` with 6 presets (ERD, UML Class, Sequence, Architecture, ML/DL, Flowchart), self-check + auto-fix (2 rounds), iterative feedback (5 rounds), style presets capturable from a sample file or image. The self-check loop is the differentiator.
- **`ekusiadadus/draw-mcp`** — adds a **validator** (`draw-mcp-validate`) with strict/standard/loose modes, 153+ tests, and CI hooks. Use as a quality gate.
- **`sergio-farfan/OCI-draw.io-Architect`** — OCI-specific, 220 bundled OCI SVG icons, reads Terraform; relevant if you do Oracle Cloud PoCs.
- **`nirmal84/aws-arch-drawio-plugin`** — AWS-specific, reads CDK/Terraform/CloudFormation/SAM, AWS official icons; chains the `drawio-mcp` MCP and AWS Labs IaC MCPs.
- **`markus41/drawio-diagramming` plugin** (claudepluginhub) — bundles a "Diagram Architect" agent with generate→analyze→improve→finalize self-editing workflow; useful for unattended doc generation but heavier.
- **`jgtolentino/drawio-diagrams-enhanced`** — Curates 200+ icon libraries and PMP/BPMN/RACI templates. Good for project-management-flavored diagrams.

### Tier 3 — Adjacent skills you should know about

- **`obra/superpowers`** (`/plugin marketplace add obra/superpowers-marketplace`) — Jesse Vincent's framework. Not diagram-specific but the **brainstorming → plan → execute** workflow pairs well with diagram skills: have Superpowers' `brainstorming` skill draft the system narrative first, then hand off to the drawio skill.
- **`wshobson/agents`** — 153 skills / 137 agents. Includes a `c4-architecture` plugin with `c4-component` and `c4-code` agents, a `mermaid-expert` agent, and `architecture-decision-records` skill. Mermaid-first, not drawio-first.
- **`jeremylongshore/lucidchart-pack`** — 18 Lucidchart skills via `/plugin install lucidchart-pack@claude-code-plugins-plus`. Hits the Lucid REST API directly for programmatic diagram creation + data-linked visualizations. Use when your deliverable must end up in Lucidchart proper.
- **Claude Code skill for Excalidraw** — Excalidraw JSON files can be imported into drawio. Good for whiteboard-style sketches; weak for structured architecture.

### MCP servers worth running

| MCP server | Output | Best for |
|---|---|---|
| **`@drawio/mcp` (jgraph official)** | mxGraph XML / Mermaid / CSV → opens in draw.io editor | Default; supports inline rendering via MCP Apps |
| **`lgazo/drawio-mcp-server`** (Deno) | Live editor connection with AWS / GCP / Azure / Cisco19 / CiscoSafe icon search at runtime via `--editor` flag | Cloud-architecture diagrams with vendor icons |
| **`simonkurtz-MSFT/drawio-mcp-server`** | Generates draw.io XML directly, no browser needed | Server-side / CI generation |
| **`apetta/diagrams-mcp`** | Python `diagrams` library → PNG/PDF/JPG/DOT (15+ providers, 500+ nodes) | Quick AWS/Azure/GCP renders; not editable in drawio |
| **`structurizr/mcp`** (Docker: `structurizr/mcp`; hosted: `https://mcp.structurizr.com/mcp`) | DSL validate/parse/inspect + PlantUML/Mermaid/C4-PlantUML export | C4 workflow; chain into Catalyst or EasyC4 for drawio |

### What about Cursor / Cline / Roo Code / KiloClaw / Warp?

All of these support the **Agent Skills format** (SKILL.md with frontmatter). Every skill above except the ones that explicitly require Claude Code plugin marketplace syntax will work — `little-hands/claude-drawio-skill` documents Cursor symlink install, and `Agents365-ai/drawio-skill` is verified across Cursor / Copilot / OpenClaw / Codex / Hermes. The jgraph `skill-cli` is just a SKILL.md file and works in any host that respects Anthropic's Agent Skills spec.

---

## C) Intermediate Formats and Round-Trip Workflow

### Side-by-side comparison

| Format | Auto-layout engine | LLM friendliness | drawio editable round-trip | Best use case |
|---|---|---|---|---|
| **Raw mxGraph XML** | None (LLM places coords) | Hardest; needs skill to enforce coords | ✅ Native | Final-mile control, named templates (your `lucidchart-drawio`) |
| **Structurizr DSL** | Manual layout in DSL or server-rendered; auto-layout for PlantUML export | Excellent (designed for it per Simon Brown) | Via PlantUML → Catalyst/EasyC4 → drawio | C4 models, multi-view consistency, model-based AI workflows |
| **C4-PlantUML** | PlantUML/Graphviz; layout decided by PlantUML server | Very good; Claude beats GPT-5 on AWS-PlantUML imports | Via `localgod/catalyst` (Dagre) or EasyC4 (`https://c4.wtx.pl`) | C4 with editable drawio output |
| **Mermaid (non-C4)** | dagre (flowchart), plain layout (sequence) | Excellent | ✅ Native — drawio has built-in Mermaid import for flowchart, sequence, ER, gantt, mindmap | Flowcharts, sequences |
| **Mermaid C4** | dagre | Excellent text generation | ❌ Broken — drawio imports as flat image (issues #3870, #5377) | Avoid for drawio round-trip |
| **D2** | dagre / ELK / TALA (paid) | Excellent grammar | ❌ No drawio exporter | Final SVG/PNG only |
| **Excalidraw JSON** | None (rough hand-drawn aesthetic) | Good | drawio imports Excalidraw | Whiteboard-style sketches |

### Which intermediate produces the cleanest drawio result?

For the user's priority — clean layout, no overlaps, proper grouping, and Solution Architect client deliverables — the **ranking from cleanest to dirtiest after import**:

1. **PlantUML C4 → `catalyst` (Dagre) → drawio**, then human polish. Predictable, deterministic, edges routed by Dagre.
2. **Raw drawio XML from a skilled LLM** (Opus 4.7 + your `lucidchart-drawio` named layouts + OpenAEC swimlane skill). Highest visual quality ceiling, but only when the skill constrains structure.
3. **Mermaid (non-C4) → drawio native import**. Quick and editable for flowcharts/sequences; layouts can be plain.
4. **Structurizr DSL → PlantUML → drawio** for full C4 model consistency across multiple views.
5. **D2 → SVG → drawio (as image)**. Beautiful output but loses editability.
6. **Mermaid C4 → drawio**. Currently degrades to flat image; avoid.

### Auto-layout engines

- **dagre** — fast, hierarchical, used by Mermaid, D2 default, and Catalyst. Good for DAGs, weak when you need ports or fixed-position lanes.
- **ELK (Eclipse Layout Kernel / elkjs)** — *"more mature than dagre, better maintained"* per D2's own docs; supports layered, rectangle packing, tree, force/stress, radial; the only engine of these three that supports `width`/`height` constraints on containers in D2.
- **Graphviz (DOT, neato, circo, fdp, twopi)** — originated at AT&T Bell Labs with its first public release in 1991, making it ~35 years old as of 2026; output style is dated; integrated via ELK bridge and used by Python `diagrams` library / `diagrams-mcp`.
- **TALA** (Terrastruct, paid) — engineered specifically for software architecture; best aesthetics, but locks you in.

For drawio purposes, **Dagre via Catalyst is the practical winner** because it's what produces editable mxGraph XML.

---

## D) Prompt Patterns and Techniques

### Patterns that consistently improve output

1. **Enforce container-relative coordinates explicitly.** The single most impactful instruction, lifted verbatim from the OpenAEC swimlane SKILL: *"Pool (container=1, parent=\"1\") ← absolute coordinates; Lane A (container=1, parent=\"pool\") ← relative to pool; Shape 1 (parent=\"lane_a\") ← relative to Lane A."* Put this in your system prompt for any swimlane / nested-container diagram.
2. **Two-layer rendering for edges + icons.** From the official jgraph drawio skill: *"2-layer rendering (technique for drawing edges behind icons)"*. Tell the LLM to place all edges in a layer rendered *before* icons so connectors don't cross over icon glyphs.
3. **Plan-then-emit.** Have the model output a JSON layout plan (entities, parent IDs, grid cell assignments) *before* emitting XML. The arXiv DiagrammerGPT paper and AWS GenAI-DrawIO-Creator paper both rely on this: generate a *"diagram plan"* with bounding boxes, self-refine, then render. Your `lucidchart-drawio` skill's named patterns (hub-radial, scope-columns, etc.) act as the plan template.
4. **Self-check loop.** Agents365-ai's `drawio-skill` runs 2 self-check rounds and 5 feedback rounds — Anthropic's wshobson "Diagram Architect" follows a `generate → analyze → improve → finalize` cycle. For Opus 4.7 specifically, the new `xhigh` effort level (default in Claude Code) handles this without explicit prompting; for Sonnet, explicitly ask for it.
5. **Constrain shape vocabulary.** Provide an explicit allowlist of mxGraph style strings (`rounded=1;whiteSpace=wrap;html=1;`, `swimlane;startSize=30;container=1;collapsible=0;`, etc.). Skills like `OpenAEC drawio-impl-swimlanes` include this allowlist; without it the model invents style fragments.
6. **Validate before show.** Use `ekusiadadus/draw-mcp` validator (`draw-mcp-validate diagram.drawio --mode strict`) or Structurizr's MCP `Validate Structurizr DSL` tool to gate output. Validation catches `parent` mismatches, orphan edges, and dangerous HTML.
7. **For Structurizr DSL specifically**, hint the model. Simon Brown's own technique (LinkedIn): *"I gave Claude a Structurizr DSL file that modelled a software system down to the container level and said, '\<folder X\> represents \<container Y\>… add the component model in the DSL by parsing the source code'. Hints can take the form of saying, 'find all classes that have Spring's @Controller, @Service, and @Repository annotations' or even just adding some Structurizr element tags."*

The official Structurizr AI guidance (docs.structurizr.com/ai) states: *"LLMs excel at generating text — the Structurizr DSL is text-based, version controllable, and diff-friendly. Structurizr is model-based — you can create a collection of consistent views onto a single model… Structurizr was designed to support the C4 model — it understands the abstractions and diagram types that make up the C4 model. Structurizr can therefore enforce the hierarchy of abstractions (e.g. containers must be defined inside software systems) and enforce the rules of the diagram types (e.g. components can't be added to a container diagram)."*

### When to ask LLM to write XML directly vs. via DSL

| Situation | Direct mxGraph XML | Via DSL (Structurizr/PlantUML/Mermaid) |
|---|---|---|
| Diagram <20 nodes, simple flowchart | ✅ Fast | Overkill |
| Swimlanes / pools / nested containers | ✅ **With** swimlane skill enforcing parent rules | DSL doesn't always preserve lane fidelity through import |
| C4 model with multiple consistent views | ❌ Hard to keep models consistent | ✅ Structurizr DSL |
| Cloud-vendor diagrams (AWS/Azure/GCP) | ✅ With vendor-icon skill (`lgazo/drawio-mcp-server`, `nirmal84/aws-arch-drawio-plugin`) | DSL loses the official icons |
| Auto-layout from a complex graph | ❌ Coordinate math fails | ✅ Dagre/ELK via Catalyst |
| Reproducible PR-reviewable artifact | ❌ XML diffs are noisy | ✅ DSL diffs cleanly |

---

## E) Practical Recommendations

### Your end-to-end workflow (Solution Architect, Claude Code, drawio target)

**Default flow for client PoC diagrams:**

1. **Brainstorm narrative in Claude Code with Sonnet 4.6.** Use `obra/superpowers` `brainstorming` skill or just freeform conversation to nail down components, actors, and groupings *before* asking for any diagram.
2. **Generate the diagram with Opus 4.7** (switch to Opus when the prompt mentions "diagram" or has >5 nesting levels — match the routing pattern Anthropic and NxCode recommend).
3. **Let your skills stack route the work:**
   - Trigger your **`lucidchart-drawio`** skill by naming the pattern explicitly: *"Build this as a hub-radial diagram"* or *"Use the scope-columns layout"*. This is your strongest differentiator — most teams don't have named templates.
   - Layer on **OpenAEC `drawio-impl-swimlanes`** automatically when swimlanes/pools/lanes appear in the prompt.
   - Fall back to **jgraph `drawio` skill-cli** for generic architecture/ERD/sequence.
4. **Validate with `ekusiadadus/draw-mcp` validator** before showing the client (`draw-mcp-validate diagram.drawio --mode standard`).
5. **Open the `.drawio` in draw.io desktop**, polish styling/labels (the jgraph skill auto-opens it for you).
6. **For Lucidchart deliverables**, open the `.drawio` in Lucidchart via its built-in mxGraph import — quality is preserved for shapes and edges; complex styling sometimes needs touch-up.

**Fallback C4 flow when the client wants strict C4 (e.g., regulated industry, architecture-board reviews):**

1. Run the **Structurizr MCP server** in Docker: `docker pull structurizr/mcp` → `docker run -it --rm -p 3000:3000 -e PORT=3000 structurizr/mcp -dsl -plantuml -mermaid`. Or use the hosted endpoint `https://mcp.structurizr.com/mcp` via `npx mcp-remote`.
2. Have Claude generate Structurizr DSL.
3. Use the MCP server's `Validate Structurizr DSL` tool to gate output.
4. Export to PlantUML C4 (`Export view to C4-PlantUML`).
5. Convert to `.drawio` with **`localgod/catalyst`** (`npm install catalyst`, then `Catalyst.convert(pumlContent)`) or paste into **EasyC4** (`https://c4.wtx.pl`).
6. Open in draw.io to polish.

### Specific install commands

```bash
# Tier 1 — install once
/plugin marketplace add jgraph/drawio-mcp
/plugin install drawio@drawio-mcp   # or copy skill-cli/SKILL.md to ~/.claude/skills/drawio/

git clone https://github.com/OpenAEC-Foundation/Draw.io-Claude-Skill-Package
cp -r Draw.io-Claude-Skill-Package/skills/source/* ~/.claude/skills/
pip install drawio-mcp

# Tier 2 — install if you do AWS/OCI/Lucidchart work
/plugin add https://github.com/nirmal84/aws-arch-drawio-plugin
/plugin marketplace add sergio-farfan/OCI-draw.io-Architect
/plugin install lucidchart-pack@claude-code-plugins-plus   # via jeremylongshore

# Validator
pip install draw-mcp # or: /plugin marketplace add ekusiadadus/draw-mcp

# Structurizr MCP (Docker)
docker run -it --rm -p 3000:3000 -e PORT=3000 structurizr/mcp -dsl -plantuml -mermaid
# Then in Claude Desktop config:
# { "mcpServers": { "structurizr-mcp": { "command": "npx", "args": ["mcp-remote", "http://localhost:3000/mcp"] } } }

# PlantUML C4 → drawio (Node)
npm install catalyst
```

### Sample prompt template

```
You are generating a draw.io (.drawio) architecture diagram.

CONTEXT
- Diagram type: [container | swimlane | hub-radial | scope-columns | LR data pipeline | tenant-namespace]
- System: [name]
- Audience: [client exec | internal eng review | architecture board]
- Estimated nodes: [N]

CONSTRAINTS (non-negotiable)
1. Container-relative coordinates. Pool (parent="1") uses absolute coords; lanes inside use coords relative to the pool; shapes inside lanes use coords relative to the lane. Cross-lane edges have parent="<pool-id>".
2. No overlapping shapes. Reserve a 40px gutter on all sides of every shape; reserve a 30px gutter around every container header (startSize=30).
3. Edges in a layer rendered BEFORE icons (two-layer rendering).
4. Use only these mxGraph styles: [allowlist].
5. Output: a complete <mxfile><diagram><mxGraphModel>...</mxGraphModel></diagram></mxfile> document — no surrounding prose.

PROCESS
Step 1. Output a JSON plan: { containers: [...], shapes: [{id, parent, grid_row, grid_col, w, h}], edges: [{source, target}] }.
Step 2. Validate the plan: every shape's parent exists; no two shapes share grid cell; every edge endpoint is a valid id.
Step 3. Emit the final .drawio XML.
Step 4. Self-check: list any potential overlaps or missing parents and fix them in a second pass.
```

### Tradeoffs cheat sheet

- **Raw drawio XML from LLM** — Highest ceiling, lowest floor. Use **only** with a skill that enforces structure (`lucidchart-drawio`, OpenAEC swimlane). Best when you have a strong named template.
- **Structurizr/PlantUML → drawio** — Highest floor, lower ceiling. Layout is "good enough by default" via Dagre; you lose pixel-level control. Best for C4, multi-view consistency, and PR-reviewable diagrams-as-code.
- **Mermaid → drawio** — Easy and editable for flowcharts/sequences. Avoid Mermaid C4 → drawio (broken).
- **D2** — Beautiful renders, but **dead-end for editable drawio**. Use only when SVG/PNG is the actual deliverable.
- **Python `diagrams` library (via `apetta/diagrams-mcp`)** — Great for AWS/Azure/GCP PNGs with official icons; not editable in drawio.

---

## Caveats

- **No public benchmark scores LLMs on draw.io XML quality.** Recommendations above synthesize MermaidSeqBench (arXiv:2511.14967v1, sequence diagrams only), the AWS GenAI-DrawIO-Creator arXiv paper (Claude 3.7 prototype), the kilo.ai November 26, 2025 GPT-5.1 vs Gemini 3.0 vs Opus 4.5 coding comparison (which includes Mermaid output as one signal), arXiv 2508.15222 ("See it. Say it. Sorted" — sketch-to-diagram on 10 published-paper sketches for GPT-5 and Gemini-2.5-Pro), Anthropic's own model cards, and the documented behavior of the skills referenced. Run your own eval on your specific diagram patterns before standardizing.
- **Claude Opus 4.7's tokenizer (v2) may encode text 1.0–1.35x less efficiently than Opus 4.6.** Measure actual cost on your prompts before assuming the $5/$25 pricing parity translates 1:1.
- **The hosted `mcp.draw.io/mcp` endpoint requires an MCP host that supports MCP Apps** (Claude Desktop / Cowork do; many CLI hosts don't yet). In unsupported hosts, the tool still returns XML as text — usable, just not rendered inline.
- **Simon Brown's caveat applies to any diagram-from-codebase workflow:** *"AI is non-deterministic. Ask an AI agent to generate a diagram from a codebase multiple times and you'll get a different answer each time."* This is why a stable Structurizr DSL baseline + hints + validation beats one-shot generation.
- **Mermaid C4 → drawio is broken as of May 2026** (jgraph/drawio #3870, #5377). Track those issues if Mermaid C4 is on your roadmap.
- **D2's TALA engine is paid.** The free dagre and ELK engines are good; benchmarks comparing all three on the same diagram routinely show different layouts — none is universally "right."
- **Claude Mythos Preview** (April 2026, Project Glasswing) outperforms Opus 4.7 on benchmarks but is invitation-only for defensive-cybersecurity workflows. Not a practical option for solution-architect PoC work in May 2026.
- **Your existing `lucidchart-drawio` skill is unusual in a good way.** Most skills surveyed (jgraph, OpenAEC, Agents365-ai, little-hands, drawio-diagrams-enhanced) teach Claude *how* to write XML but don't impose *which* layout pattern to use. Named patterns (hub-radial, scope-columns, etc.) are the constraint that forces clean composition. Keep it. The recommendations above complement rather than replace it.