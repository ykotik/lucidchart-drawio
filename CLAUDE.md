# CLAUDE.md — drawio-architect skill repo

## Project overview

This repo is the source for the **`drawio-architect`** Claude skill (v2.1). The skill generates clean draw.io / mxGraph XML (`.drawio` files) that import into Lucidchart, draw.io desktop, and any mxGraph-aware tool.

## Repo layout

```
skill/
  SKILL.md              — main skill orchestrator (workflow, checklist, 15-pattern selector)
  README.md             — install & feature summary
  references/           — reference docs read on demand during diagram generation
    container-coords.md
    edge-routing.md
    plan-format.md
    style-dictionary.md
    gestalt-rules.md
    layout-patterns.md
    validator.md
    font-fit.md
    edge-routing.md
    prompt-examples.md
    layout-engines.md
    critic-judge-loop.md
    xml-schema.md
    shape-vocabulary/
      aws.md  azure.md  gcp.md  uml-erd-bpmn.md
  templates/            — 15 starter .drawio skeletons (one per layout pattern)
  scripts/
    validate.py         — pre-flight validator (E/W/Q/G/D error codes)
    elk-layout.py       — ELK / Graphviz auto-layout + neato overlap removal
    fit-fonts.py        — adaptive fontSize post-processor
    text-metrics.js     — label overflow measurement (zero native deps)
tests/
  conftest.py           — pytest fixtures; discovers cases/ subdirectories
  test_xml_structure.py — Layer 1: well-formed XML, IDs, parents, edge geometry
  test_content.py       — Layer 2: OCR-based label presence checks
  test_regression.py    — Layer 3: pixel-diff regression vs baseline.png
  test_visual.py        — Layer 4: visual quality heuristics
  requirements.txt      — pytest, opencv-headless, easyocr, Pillow, pixelmatch
  cases/<name>/         — each case: reference.drawio, reference.png, baseline.png, thresholds.json, expected.plan.json
docs/
  compass_research2.md                — deep-research report on the LLM→diagram landscape
  research-validation-findings.md     — fact-check of the research report (verified URLs, corrections)
```

## Core workflow (plan-then-emit)

Always follow this order when generating a diagram:

1. **PLAN** — JSON layout plan (containers, shapes, edges with parent IDs + grid cells)
2. **TEXT METRICS** — run `scripts/text-metrics.js` to annotate min dims; adjust plan
3. **EMIT XML** — read matching template, fill from plan
4. **SELF-CHECK** — pre-flight checklist (13 items in SKILL.md)
5. **WRITE** `.drawio` file with the Write tool
6. **VALIDATE** — `python3 scripts/validate.py <file>.drawio`
7. **OVERLAP REMOVAL** (dense/complex) — `python3 scripts/elk-layout.py <file>.drawio --engine neato`

**Never inline XML in chat. Always write a `.drawio` file.**

## Running scripts

```bash
# activate venv first
source .venv/bin/activate

python3 scripts/validate.py path/to/diagram.drawio
python3 scripts/validate.py path/to/diagram.drawio --mode strict
python3 scripts/elk-layout.py path/to/diagram.drawio --engine neato
python3 scripts/elk-layout.py path/to/diagram.drawio --engine auto
python3 scripts/fit-fonts.py path/to/diagram.drawio --mode auto
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
```

## Running tests

```bash
source .venv/bin/activate
pip install -r tests/requirements.txt

pytest tests/                          # all layers
pytest tests/test_xml_structure.py     # Layer 1 only (fast, no image deps)
pytest tests/ --update-baselines       # refresh baseline.png files
```

Test cases live in `tests/cases/<name>/`. A case needs at minimum a `thresholds.json`. The `reference.drawio` and `reference.png` are generated; `baseline.png` is committed.

To add a new test case: create `tests/cases/<name>/thresholds.json` and `expected.plan.json`, generate `reference.drawio`, export `reference.png` via draw.io CLI, then run `--update-baselines`.

## The #1 rule — container-relative coordinates

Children inside a container use coordinates **relative to the container's top-left**, not absolute canvas coordinates. Cross-lane edges must have `parent="<common-ancestor>"`. See `skill/references/container-coords.md`.

## Output format

- **Single-page diagrams** → bare `<mxGraphModel>` (no `<mxfile>` wrapper) per `output_mode: auto`
- **Multi-page diagrams** → full `<mxfile><diagram>...</diagram></mxfile>` wrapper
- Both formats are accepted by draw.io and Lucidchart.

## Feature flags (SKILL.md frontmatter)

| Flag | Default | Effect |
|---|---|---|
| `output_mode` | `auto` | bare / wrapped / auto |
| `quality_gate` | `on` | edge-crossings, orthogonality, length variance checks |
| `grounding_manifest` | `on` | every node/edge must have a `cite` field (G501 on violation) |
| `auto_layout` | `auto` | ELK when >20 vertices |
| `text_metrics` | `auto` | measure labels, warn on overflow |
| `font_fit` | `auto` | shrink fontSize on overflow |
| `edge_routing` | `auto` | obstacle-push waypoints when >15 edges (F7) |

Override per-diagram: add `<!-- lucid:feature=value -->` as first line of the source plan.

## Validator error codes

- **E0xx** — hard errors (fail by default)
- **W1xx** — warnings (fail in `--mode strict`)
- **Q4xx** — quality metrics (edge crossings, orthogonality %)
- **G5xx** — grounding manifest violations
- **D6xx** — DiagramEval F1 scores

## Style rules

Only use styles from the allowlist:
- `skill/references/style-dictionary.md` (general palette, scope containers, edge styles)
- `skill/references/shape-vocabulary/aws.md` / `azure.md` / `gcp.md` / `uml-erd-bpmn.md`

Never invent style fragments. If a new style is needed, add it to the vocabulary file first.

## Layout pattern quick-pick

| Pattern | When |
|---|---|
| `hub-radial` | central hub + N satellites |
| `scope-columns` | internal vs vendor boundary (CIAM-style) |
| `swimlanes` | trust zones / cadence bands |
| `pipeline` | LR data flow / streaming / ETL |
| `tenant-namespace` | multi-tenant nested containers |
| `c4-context/container/component` | C4 L1/L2/L3 |
| `erd-crowfoot` | database schema |
| `uml-class` | domain model / class diagram |
| `sequence` | request flow, call ordering |
| `flowchart-dag` | process with decisions |
| `bpmn-process` | business process (gateways, events) |
| `tree-hierarchy` | org chart / taxonomy |
| `grid-matrix` | 2D capability/classification map |

If intent is unclear, ask one question — do not guess.

## Key design decisions

- **Two-layer edge rendering**: edges in a layer *before* the icon layer so connectors render behind shapes (see `skill/references/edge-routing.md`)
- **Grounding manifest**: every diagram element must cite its source (file:line, doc:section, `user-stated`, or `assumption:...`). No hallucinated boxes.
- **Overlap removal via neato**: deterministic Graphviz constraint-solving replaced the earlier Critic-Judge LLM loop for dense diagrams
- **Bare `<mxGraphModel>`** is the recommended AI generation format per the official draw.io FAQ (confirmed in `docs/research-validation-findings.md`)
