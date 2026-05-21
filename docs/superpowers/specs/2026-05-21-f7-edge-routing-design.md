# F7 edge_routing — Design Spec

**Date:** 2026-05-21  
**Status:** Approved for implementation  
**Branch:** feat/f7-edge-routing

---

## Problem

Edges in generated `.drawio` diagrams intersect unrelated shapes and graze shape
borders — the two most common visual quality defects, especially after ELK
relayout. The existing `auto_layout` (F4) repositions nodes but does not
guarantee edge paths are obstacle-free.

Target failure modes (in priority order):

1. Edge cuts through an unrelated shape (implies phantom connection)
2. Edge grazes a shape border within the clearance zone (looks connected)

---

## Solution

Two-layer approach:

**Layer 1 — LLM corridor planning (plan construction, Step 1.2)**  
A new reference doc (`references/routing-corridors.md`) teaches the LLM to
reserve horizontal/vertical routing bands (`corridors[]`) in the JSON plan and
add explicit `waypoints[]` to edges that would otherwise cross a shape. This
pre-empts most intersections before XML is emitted.

**Layer 2 — Obstacle-push script (post-ELK, Step 6.5)**  
`scripts/route-edges.py` runs after ELK relayout. It detects remaining
edge-shape AABB intersections and inserts waypoints via the shortest orthogonal
detour (above / below / left / right). Pure Python stdlib, zero LLM tokens.

---

## Feature flag

| Flag | Values | Default |
|---|---|---|
| `edge_routing` | `off` \| `script` \| `auto` | `auto` |

- `auto` — LLM corridor planning + script; activates when diagram has > 15 edges
- `script` — script only; zero extra LLM tokens; good for fast-draft + post-processing
- `off` — disabled entirely

Override per-diagram: `<!-- lucid:edge_routing=script -->`

---

## Pipeline position

```
Step 6   ELK auto-layout      (F4)
Step 6.5 route-edges.py       (F7)  ← NEW
Step 7   fit-fonts.py         (F6)
Step 8   re-validate          Q401 crossings should → 0
```

---

## Algorithm — obstacle-push (route-edges.py)

1. Parse all `mxCell` vertices; resolve absolute canvas coordinates by walking
   parent chains (container-relative → absolute).
2. For each edge with valid `source` and `target`:
   a. Compute centre-to-centre straight-line path p1 → p2.
   b. Collect all vertex AABBs expanded by `clearance` (default 20 px) that
      the segment intersects, excluding the source and target shapes.
   c. Sort blockers by Manhattan distance from p1 (process in path order).
   d. For each blocker, compute the shortest single-waypoint detour:
      try four bypass points (above / below / left / right of the AABB
      midpoint), pick the one with minimum Manhattan path length.
   e. Insert `<Array as="points">` waypoints into the edge's `mxGeometry`.
3. Log `W110` for any edge that is still blocked after detour insertion
   (indicates a diagram too dense for single-waypoint resolution — recommend
   `auto_layout=elk` with wider spacing).

**Clearance:** 20 px default. Override with `--clearance N`.  
**Threshold:** edges < 15 → no-op in `auto` mode. Override with `--threshold N`.

---

## LLM corridor planning — routing-corridors.md

The reference doc defines:

- `corridors[]` array added to plan JSON (alongside `shapes`, `edges`)
- Each corridor: `id`, `axis` (`h`|`v`), `y`+`height` or `x`+`width`,
  `between` label, `cite: "routing"`
- `edge.waypoints[]` — explicit waypoint array per edge (populated at plan time
  for known crossings; script may add more post-ELK)
- Sizing rules: 40 px minimum, 60 px for 2–3 parallel edges
- Pattern-specific guidance: pipeline (vertical corridors between stages),
  swimlanes (use existing inter-lane gap), C4 (horizontal corridors between
  tiers), hub-radial (skip — spokes radiate outward naturally)

---

## New and changed files

| File | Change |
|---|---|
| `skill/scripts/route-edges.py` | New — obstacle-push script |
| `skill/references/routing-corridors.md` | New — LLM corridor planning guide |
| `skill/SKILL.md` | Add F7 flag, Step 1.2, Step 6.5, reference entry, script entry |
| `skill/references/plan-format.md` | Add `corridors[]` and `waypoints[]` to optional fields table and schema example |
| `skill/scripts/validate.py` | Q401 warning now recommends route-edges.py |
| `CLAUDE.md` | Add edge_routing row to feature flags table |
| `docs/skill-feature-analysis.md` | Add F7 to catalogue, categorisation, cost table, and impact ranking |

---

## Token cost

| Mode | LLM Δ | Script time |
|---|---|---|
| `auto` | +2,000–2,500 tokens | < 500 ms |
| `script` | 0 | < 500 ms |

Sits between F3 grounding_manifest (+1,800) and F5 text_metrics (+3,000).

---

## Validation integration

- `Q401` (edge crossings) — after route-edges, expected count = 0. Warning now
  directs user to `scripts/route-edges.py` as primary fix.
- `W110` — emitted by route-edges.py stderr when a detour did not fully clear
  all blockers (diagram too dense for single-waypoint resolution).

---

## Known limitations

- Single-waypoint detour per blocker. Diagrams with 3+ collinear blockers on
  the same edge may produce sub-optimal zig-zag paths. Mitigation: `auto_layout=elk`
  with wider `spacing.nodeNode` resolves most cases before route-edges runs.
- Resolves centre-to-centre straight-line only — does not model ELK's actual
  routed path. May insert unnecessary waypoints on edges that ELK already routed
  cleanly. These are visually harmless (orthogonal routing absorbs extra waypoints).
- CJK / RTL label shapes: no special handling needed (geometry is geometry).

---

## Out of scope (v1)

- Multi-waypoint chaining for densely packed diagrams
- Reading ELK's actual routed path instead of straight-line proxy
- Corridor-aware waypoint placement (script uses geometric shortest-detour only)
- Style presets (separate feature)
