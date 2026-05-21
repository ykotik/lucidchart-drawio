# drawio-architect

## Project Overview

This repository is the source for the **`drawio-architect`** Claude skill (v2.1). The skill generates clean draw.io / mxGraph XML (`.drawio` files) that can be imported seamlessly into Lucidchart, draw.io desktop, and any other mxGraph-aware tool.

## Core Features

- **Plan-then-emit workflow**: Generates a JSON layout plan before emitting XML to ensure structural integrity.
- **Container-Relative Coordinates**: Ensures elements inside containers use local coordinates relative to the container's top-left, rather than absolute canvas coordinates (eliminating common swimlane bugs).
- **Two-layer edge rendering**: Connectors are drawn behind icons for cleaner visuals.
- **Style Dictionary Enforcement**: Uses a strict palette and approved shape vocabularies (AWS, Azure, GCP, UML/ERD/BPMN) to prevent hallucinatory styles.
- **Pre-flight Validator**: Included scripts (`validate.py`) catch duplicate IDs, orphan parents, missing edge geometry, and overlaps before final output.
- **Deterministic Overlap Removal**: Uses Graphviz `neato` constraint-solving for clean, automatic layouts.

## Installation

To install the skill in Claude:

1. Locate the `.skill` or `.zip` package (e.g., `skill.zip`) in the repository.
2. Drag and drop the package into Claude's plugin panel, or run `/install` in Claude Code.

To rebuild the `.skill` file from source:
```bash
cd /path/to/skill-creator
python3 -m scripts.package_skill /path/to/drawio-architect ./dist
```

## Samples & Layout Patterns

The skill comes pre-loaded with 15 layout template samples, ensuring consistent architecture diagrams across various use cases:

1. **hub-radial**: Central system (Okta, Workato) with satellite connections.
2. **scope-columns**: CIAM-style dual boundary (internal vs. vendor SaaS).
3. **swimlanes**: Trust zones, integration cadence bands, network tiers.
4. **pipeline**: Kafka/Flink streaming, ETL, middleware data flow (LR).
5. **tenant-namespace**: Multi-tenant deployments with nested containers.
6. **c4-context**: C4 L1 — Person/System/External boundaries.
7. **c4-container**: C4 L2 — Containers inside a system.
8. **c4-component**: C4 L3 — Components inside a container.
9. **erd-crowfoot**: Entity-relationship with crow's-foot cardinality.
10. **uml-class**: UML class diagram (3-compartment boxes, inheritance).
11. **sequence**: UML sequence — lifelines + messages.
12. **tree-hierarchy**: Org chart, decision tree, taxonomy.
13. **flowchart-dag**: Flowchart with decision diamonds, start/end.
14. **bpmn-process**: BPMN (pools, lanes, gateways, events, tasks).
15. **grid-matrix**: 2D classification / capability matrix.

## Usage & Scripts

To run the validation or processing scripts locally, activate your virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate

# Validate a generated diagram
python3 scripts/validate.py path/to/diagram.drawio
python3 scripts/validate.py path/to/diagram.drawio --mode strict

# Perform auto-layout or post-processing
python3 scripts/elk-layout.py path/to/diagram.drawio --engine neato
python3 scripts/fit-fonts.py path/to/diagram.drawio --mode auto
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
```
