# lucidchart-drawio

A Claude skill for generating Lucidchart-importable architecture diagrams as draw.io XML.

## Install

Drag `lucidchart-drawio.skill` into Claude's plugin panel, or run `/install` in Claude Code.

To rebuild the `.skill` file from source:

```bash
cd /path/to/skill-creator
python3 -m scripts.package_skill /path/to/lucidchart-drawio ./dist
```

## Contents

```
SKILL.md                        — skill trigger + 5-step workflow + critical XML rules
references/
  xml-schema.md                 — mxGraph XML attribute reference (mxCell, geometry, containers, edges)
  style-dictionary.md           — color palettes, scope/component/edge styles, legend XML
  gestalt-rules.md              — 10 design rules (flow, spacing, connectors, typography, density)
  layout-patterns.md            — coordinate guides + skeleton structure for 5 layout patterns
templates/
  hub-radial.drawio             — hub at center, N satellite spokes
  scope-columns.drawio          — dual-scope columns: green (internal) + black (vendor/external)
  swimlanes.drawio              — horizontal trust/cadence/tier bands
  pipeline.drawio               — LR streaming pipeline: sources → processing → consumers
  tenant-namespace.drawio       — multi-tenant Kafka/Flink namespace containers
```

## Layout patterns

| Pattern | Use case |
|---|---|
| hub-radial | Central system (Okta, Workato) with satellite connections |
| scope-columns | CIAM-style dual boundary: org-internal vs vendor SaaS |
| swimlanes | Trust zones, integration cadence bands, network tiers |
| pipeline | Kafka/Flink streaming, ETL, middleware data flow (LR) |
| tenant-namespace | Multi-tenant deployments with nested Kafka/Postgres containers |

## Scope style convention

| Border | Meaning |
|---|---|
| Green dashed `#2E7D32` | Internal org boundary (owned/managed systems) |
| Black dashed `#424242` | Vendor SaaS + external orgs |
| Red fill `#FFEBEE` | Auth gap / remediation needed |
