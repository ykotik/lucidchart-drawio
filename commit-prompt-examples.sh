#!/usr/bin/env bash
#
# F9: 5 canonical prompt examples included in the skill.
#
# Run from Mac terminal:
#   cd "/Users/Yuriy_Kotik/Documents/Claude/Projects/Lucid Diagrams/lucidchart-drawio"
#   bash commit-prompt-examples.sh

set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .git/index.lock || -f .git/HEAD.lock ]]; then
  rm -f .git/index.lock .git/HEAD.lock
fi
git -c maintenance.auto=false config gc.auto 0 2>/dev/null || true

git add SKILL.md references/prompt-examples.md

git commit -m "F9: 5 canonical prompt examples in references/prompt-examples.md

Each example exercises a different feature combination of the skill:

1. C4 Container — payments platform
   showcases: plan-then-emit, grounding manifest, two-layer edges,
   critic-judge auto-fire at >15 shapes

2. LR streaming pipeline — clickstream analytics
   showcases: auto_layout=elk (>20 vertices), Q401 crossings,
   font_fit=grow after ELK enlarges cells

3. BPMN swimlanes — purchase requisition approval
   showcases: container-relative coords, cross-lane parent=<pool-id>,
   pattern-skip for auto_layout (positional semantics)

4. ERD crow's-foot — multi-tenant SaaS schema
   showcases: table compartments, PK/FK fontStyle, crow's-foot
   cardinality, source-cited columns

5. Multi-tenant Kafka — tenant-namespace pattern
   showcases: 3-level container nesting, distinct-color sub-containers,
   LCA edge parents for cross-tenant edges, font_fit on long topic names

Each prompt includes:
- explicit pattern name
- source citations in cite: format (so F3 grounding passes)
- specific output path
- feature-flag hints where relevant

Also added anti-examples table (what NOT to write) + workflow guidance.

SKILL.md updates:
- New 'Prompt examples' section right after Scripts
- New 'Examples & guides' subsection in Reference files
- Scripts section now lists all 3 scripts (validate, elk-layout, fit-fonts)"

echo
echo "After: git push origin main"
