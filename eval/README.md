# F7: Eval Harness

Regression suite for the lucidchart-drawio skill. Runs the validator (with all feature flags on) against a fixed set of reference diagrams + ground-truth plans, and tracks Node-F1 / Path-F1 / Q4xx quality metrics over time.

**Feature flag:** `eval_harness` — `on` / `off` (default `off`).

## Layout

```
eval/
├── README.md                      — this file
├── run.py                         — harness runner
├── baseline.json                  — committed expected scores per case (updates by hand after review)
├── cases/
│   ├── c4-context-commerce/
│   │   ├── prompt.md              — the natural-language request
│   │   ├── expected.plan.json     — ground-truth plan
│   │   └── reference.drawio       — known-good output (regenerable)
│   ├── pipeline-streaming/
│   │   ├── prompt.md
│   │   ├── expected.plan.json
│   │   └── reference.drawio
│   └── swimlanes-trust-zones/
│       ├── prompt.md
│       ├── expected.plan.json
│       └── reference.drawio
└── results/
    └── 2026-05-19_001.json        — per-run output (timestamped, gitignored)
```

Three cases ship in v2.1 — `c4-context-commerce`, `pipeline-streaming`, `swimlanes-trust-zones`. Add more as confidence grows.

## Usage

```bash
# Run all cases
python3 eval/run.py

# Run a single case
python3 eval/run.py --case c4-context-commerce

# Compare against committed baseline
python3 eval/run.py --against-baseline

# Update the baseline (after manual review confirms regressions are intentional)
python3 eval/run.py --update-baseline
```

Exit codes:
- `0` — all cases meet baseline
- `1` — at least one case regressed
- `2` — harness itself failed

## What's measured

Per case:

| Metric | Source |
|---|---|
| Errors (E0xx) | validator.py |
| Warnings (W1xx, Q4xx, G5xx, D6xx) | validator.py |
| Node F1 | F4 DiagramEval |
| Path F1 | F4 DiagramEval |
| Edge crossings | F2 Q401 |
| Orthogonality % | F2 Q402 |
| Area utilization % | F2 Q404 |
| Grounding coverage | F3 G503 |

The harness writes a timestamped `results/<date>_<seq>.json` and (when run with `--against-baseline`) prints a delta table against `baseline.json`.

## When to run

- Before any merge that touches `SKILL.md`, `references/`, `templates/`, or `scripts/`
- After upgrading the underlying Claude model
- Manually before client deliverable batches

## Caveats

- `reference.drawio` files are committed snapshots, not regenerated on each run. The harness only re-validates them. To exercise the *generation* path, you'd need to call the skill end-to-end (out of scope for v2.1).
- The harness uses the same validator the skill ships with; it cannot detect bugs in the validator itself. Cross-check by spot-running cases through draw.io desktop.
- Baseline F1 thresholds (Node ≥ 0.70, Path ≥ 0.60) come from the EMNLP 2025 paper's findings on simpler structured diagrams. Calibrate per your own set after 10+ runs.
