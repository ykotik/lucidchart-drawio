#!/usr/bin/env python3
"""
F7: drawio-architect eval harness.

Runs the validator against every case in eval/cases/, captures metrics,
optionally compares against the committed baseline.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
CASES_DIR = HERE / "cases"
RESULTS_DIR = HERE / "results"
BASELINE = HERE / "baseline.json"


def run_case(case_dir):
    """Run the validator on one case, return metrics dict."""
    drawio = case_dir / "reference.drawio"
    plan = case_dir / "expected.plan.json"
    if not drawio.exists():
        return {"error": f"missing reference.drawio in {case_dir.name}"}

    cmd = [
        sys.executable,
        str(SKILL_ROOT / "scripts" / "validate.py"),
        str(drawio),
        "--features",
        "quality_gate=on,grounding_manifest=on,diagram_eval=on",
        "--mode",
        "loose",  # we capture warnings as data, not failures
    ]
    if plan.exists():
        cmd.extend(["--plan", str(plan)])

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = proc.stdout

    metrics = {
        "case": case_dir.name,
        "exit": proc.returncode,
        "errors": 0,
        "warnings": 0,
        "node_f1": None,
        "path_f1": None,
        "edge_crossings": None,
        "orthogonality_pct": None,
        "area_util_pct": None,
        "grounding": None,
    }

    m = re.search(r"Summary: (\d+) errors, (\d+) warnings", out)
    if m:
        metrics["errors"] = int(m.group(1))
        metrics["warnings"] = int(m.group(2))

    m = re.search(r"D601:.*F1=([\d.]+)", out)
    if m:
        metrics["node_f1"] = float(m.group(1))
    m = re.search(r"D602:.*F1=([\d.]+)", out)
    if m:
        metrics["path_f1"] = float(m.group(1))
    m = re.search(r"Q401: Edge crossings.*: (\d+)", out)
    if m:
        metrics["edge_crossings"] = int(m.group(1))
    m = re.search(r"Q402: Orthogonality.*= (\d+)%", out)
    if m:
        metrics["orthogonality_pct"] = int(m.group(1))
    m = re.search(r"Q404: Area utilization: ([\d.]+)%", out)
    if m:
        metrics["area_util_pct"] = float(m.group(1))
    m = re.search(r"G503: Grounding: (\d+)/(\d+) cited", out)
    if m:
        cited, total = int(m.group(1)), int(m.group(2))
        metrics["grounding"] = f"{cited}/{total}"
    return metrics


def load_baseline():
    if BASELINE.exists():
        with BASELINE.open() as f:
            return json.load(f)
    return {}


def compare(actual, baseline):
    """Return list of regressions: (case, metric, baseline_value, actual_value)."""
    regs = []
    for case_name, base in baseline.items():
        cur = next((c for c in actual if c["case"] == case_name), None)
        if not cur:
            regs.append((case_name, "<missing>", "", ""))
            continue
        for k in ("errors",):
            if cur.get(k, 0) > base.get(k, 0):
                regs.append((case_name, k, base.get(k), cur.get(k)))
        for k in ("node_f1", "path_f1"):
            bv = base.get(k)
            cv = cur.get(k)
            if bv is not None and cv is not None and cv < bv - 0.05:
                regs.append((case_name, k, bv, cv))
        for k in ("edge_crossings",):
            bv = base.get(k)
            cv = cur.get(k)
            if bv is not None and cv is not None and cv > bv + 2:
                regs.append((case_name, k, bv, cv))
    return regs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="Run only this case (directory name)")
    ap.add_argument("--against-baseline", action="store_true",
                    help="Compare results against baseline.json, exit 1 on regression")
    ap.add_argument("--update-baseline", action="store_true",
                    help="Overwrite baseline.json with the current run's metrics")
    args = ap.parse_args()

    if not CASES_DIR.exists():
        print(f"No cases directory at {CASES_DIR}", file=sys.stderr)
        sys.exit(2)

    case_dirs = sorted(d for d in CASES_DIR.iterdir() if d.is_dir())
    if args.case:
        case_dirs = [d for d in case_dirs if d.name == args.case]
        if not case_dirs:
            print(f"No case '{args.case}'", file=sys.stderr)
            sys.exit(2)

    results = [run_case(d) for d in case_dirs]

    def fmt(v, spec=""):
        if v is None:
            return "-"
        if spec:
            return format(v, spec)
        return str(v)

    # Print table
    print(f"{'case':32} {'err':>4} {'warn':>5} {'NodeF1':>7} {'PathF1':>7} {'cross':>6} {'ortho%':>7} {'area%':>6} {'grd':>6}")
    for r in results:
        node_f1 = fmt(r["node_f1"], ".3f")
        path_f1 = fmt(r["path_f1"], ".3f")
        cross = fmt(r["edge_crossings"])
        ortho = fmt(r["orthogonality_pct"])
        area = fmt(r["area_util_pct"], ".1f")
        grd = r["grounding"] or "-"
        print(
            f"{r['case']:32} "
            f"{r['errors']:>4} "
            f"{r['warnings']:>5} "
            f"{node_f1:>7} "
            f"{path_f1:>7} "
            f"{cross:>6} "
            f"{ortho:>7} "
            f"{area:>6} "
            f"{grd:>6}"
        )

    # Persist results
    RESULTS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = RESULTS_DIR / f"{ts}.json"
    with out_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")

    if args.update_baseline:
        baseline = {r["case"]: r for r in results}
        with BASELINE.open("w") as f:
            json.dump(baseline, f, indent=2)
        print(f"Updated {BASELINE}")
        sys.exit(0)

    if args.against_baseline:
        baseline = load_baseline()
        if not baseline:
            print("\nNo baseline.json — run with --update-baseline first", file=sys.stderr)
            sys.exit(2)
        regs = compare(results, baseline)
        if regs:
            print("\nREGRESSIONS:")
            for case, metric, bv, cv in regs:
                print(f"  {case}: {metric} baseline={bv} actual={cv}")
            sys.exit(1)
        print("\nNo regressions vs baseline.")
        sys.exit(0)


if __name__ == "__main__":
    main()
