# drawio-architect (v2.1)

A Claude skill for generating clean draw.io architecture diagrams (.drawio / mxGraph XML)
with strict layout discipline, clean edge routing, vendor icon vocabularies, and pre-flight
validation. Output opens natively in draw.io and imports cleanly into Lucidchart, the
Confluence drawio plugin, and any mxGraph-aware tool.

> Renamed from `drawio-architect` in v2.1 — the skill never touched Lucidchart APIs;
> output has always been standard mxGraph XML that all drawio-compatible editors accept.

## What's new in v2

- **Plan-then-emit workflow** — JSON layout plan before XML
- **Container-relative coordinate enforcement** — the #1 swimlane-bug fix
- **Two-layer edge rendering** — connectors drawn behind icons
- **10 new layout patterns** — C4 (context/container/component), ERD, UML class, sequence, tree, flowchart-DAG, BPMN, grid-matrix
- **Vendor shape vocabularies** — AWS / Azure / GCP / UML+ERD+BPMN
- **Pre-flight validator** — `python3 scripts/validate.py <file>` catches duplicate IDs, orphan parents, missing edge geometry, overlaps
- **Style allowlist** — model cannot invent style fragments
- **Deterministic Overlap Removal (v2.1.1)** — Replaces the LLM Critic-Judge loop with Graphviz `neato` constraint-solving (`scripts/elk-layout.py <file> --engine neato`)

## Install

Drag `drawio-architect.skill` into Claude's plugin panel, or run `/install` in Claude Code.

To rebuild the `.skill` file from source:

```bash
cd /path/to/skill-creator
python3 -m scripts.package_skill /path/to/drawio-architect ./dist
```

## Contents

```
SKILL.md                              — orchestrator, workflow, 15-pattern selector, pre-flight checklist
README.md                             — this file
references/
  xml-schema.md                       — mxGraph XML attribute reference (mxCell, geometry, containers, edges)
  style-dictionary.md                 — color palettes, scope/component/edge styles, legend XML
  gestalt-rules.md                    — 10 design rules (flow, spacing, connectors, typography, density)
  layout-patterns.md                  — coordinate guides + skeleton structure for all 15 patterns
  container-coords.md                 — THE #1 RULE: pool → lane → shape coord math
  edge-routing.md                     — two-layer rendering, orthogonal/curved, waypoints, label anchor
  plan-format.md                      — JSON layout plan schema for the plan-then-emit workflow
  validator.md                        — what scripts/validate.py checks and how to fix each violation
  shape-vocabulary/
    aws.md                            — AWS official icons (mxgraph.aws4.*)
    azure.md                          — Azure icons (mxgraph.azure2.*)
    gcp.md                            — GCP icons (mxgraph.gcp2.*)
    uml-erd-bpmn.md                   — class/ER/BPMN shapes and edge arrows
templates/
  hub-radial.drawio                   — hub at center, N satellite spokes
  scope-columns.drawio                — dual-scope columns: green (internal) + black (vendor/external)
  swimlanes.drawio                    — horizontal trust/cadence/tier bands
  pipeline.drawio                     — LR streaming pipeline: sources → processing → consumers
  tenant-namespace.drawio             — multi-tenant Kafka/Flink namespace containers
  c4-context.drawio                   — C4 L1: person/system/external systems
  c4-container.drawio                 — C4 L2: containers inside a system boundary
  c4-component.drawio                 — C4 L3: components inside a container
  erd-crowfoot.drawio                 — entity-relationship with crow's-foot cardinality
  uml-class.drawio                    — class diagram (3-compartment, inheritance, composition)
  sequence.drawio                     — sequence diagram with lifelines
  tree-hierarchy.drawio               — org/decision/taxonomy tree
  flowchart-dag.drawio                — process flowchart with decision diamonds
  bpmn-process.drawio                 — BPMN: pools, lanes, gateways, events, tasks
  grid-matrix.drawio                  — 2D classification matrix
scripts/
  validate.py                         — pre-flight validator (dup IDs, orphan parents, edges, overlaps)
```

## Layout patterns (15 total)

| # | Pattern | Use case |
|---|---|---|
| 1 | hub-radial | Central system (Okta, Workato) with satellite connections |
| 2 | scope-columns | CIAM-style dual boundary: org-internal vs vendor SaaS |
| 3 | swimlanes | Trust zones, integration cadence bands, network tiers |
| 4 | pipeline | Kafka/Flink streaming, ETL, middleware data flow (LR) |
| 5 | tenant-namespace | Multi-tenant deployments with nested Kafka/Postgres containers |
| 6 | c4-context | C4 L1 — Person/System/External boundaries |
| 7 | c4-container | C4 L2 — Containers inside a system |
| 8 | c4-component | C4 L3 — Components inside a container |
| 9 | erd-crowfoot | Entity-relationship with crow's-foot cardinality |
| 10 | uml-class | UML class diagram (3-compartment boxes, inheritance) |
| 11 | sequence | UML sequence — lifelines + messages |
| 12 | tree-hierarchy | Org chart, decision tree, taxonomy |
| 13 | flowchart-dag | Flowchart with decision diamonds, start/end |
| 14 | bpmn-process | BPMN: pools, lanes, gateways, events, tasks |
| 15 | grid-matrix | 2D classification / capability matrix |

## Vendor icon vocabularies

- **AWS** — 80+ icons across compute, storage, db, networking, security, integration, analytics, ML
- **Azure** — 60+ icons across the same categories
- **GCP** — 50+ icons across the same categories
- **UML / ERD / BPMN** — class compartments, crow's-foot edges, BPMN events/tasks/gateways

## Scope style convention

| Border | Meaning |
|---|---|
| Green dashed `#2E7D32` | Internal org boundary (owned/managed systems) |
| Black dashed `#424242` | Vendor SaaS + external orgs |
| Blue dashed `#1565C0` | Cloud zone (region/VPC) |
| Orange dashed `#E65100` | Regulated zone (GxP/PII/SOX) |
| Red fill `#FFEBEE` | Auth gap / remediation needed |

## Validation

```bash
python3 scripts/validate.py path/to/diagram.drawio              # standard mode
python3 scripts/validate.py path/to/diagram.drawio --mode strict # warnings also fail
python3 scripts/validate.py path/to/diagram.drawio --mode loose  # only errors fail
```

Catches: duplicate IDs, missing edge geometry, orphan parents, broken edge endpoints,
overlapping shapes, shapes overflowing containers, edges with wrong parent (not LCA),
XML comments in the model, missing `startSize` on swimlane containers.
