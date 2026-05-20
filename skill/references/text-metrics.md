# Text Metrics (F8)

Controlled by the `text_metrics` feature flag in SKILL.md frontmatter: `off` / `auto`. **Default: `auto`**.

The LLM cannot know the pixel width of a rendered string. `scripts/text-metrics.js` measures every label in the plan JSON using a character-width lookup table (Arial metrics at the declared `fontSize`) and annotates each element with a `text_safe` block. The LLM reads this before emitting XML and applies the safe dimensions as geometry lower bounds.

---

## When to run

- **Always** when any label exceeds ~20 characters
- **Always** for multi-line C4-style labels (`<b>Name</b><br/>[Type]<br/>Description`)
- **Always** for swimlane containers (header `startSize` must fit the title)
- Skip only for purely decorative text cells (`style=text;`)

---

## Usage

```bash
# Annotate plan JSON → stdout
node scripts/text-metrics.js diagram.plan.json

# Write annotated plan to file (recommended — validate.py auto-detects it)
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json

# Fail with exit 1 if any label overflows (CI gate)
node scripts/text-metrics.js diagram.plan.json --strict

# Use canvas for pixel-accurate measurement (requires libcairo)
node scripts/text-metrics.js diagram.plan.json --canvas
```

Default output path expected by `validate.py`: `<diagram-name>.annotated.plan.json` (sibling of the `.drawio` file).

---

## Output — text_safe block

Each `shapes[]` and `containers[]` element in the annotated plan gains:

```json
"text_safe": {
  "min_width":    192,      // narrowest box — fits longest word without wrapping
  "min_height":    88,      // height for all lines at declared width
  "line_count":     3,
  "overflow":    true,      // declared dims < safe dims
  "method":  "char-table",  // or "canvas"
  "wrapped_lines": [
    "SAP S/4HANA",
    "[ERP Core]",
    "Financial ledger, HR, Procurement"
  ]
}
```

For swimlane containers only:

```json
"text_safe": {
  "min_startSize": 36,      // header band height needed to fit title
  "overflow": true,
  ...
}
```

---

## How to apply in the plan step (Step 1.5)

After running the script, for every element where `text_safe.overflow == true`:

```
width  = max(plan_width,  text_safe.min_width)
height = max(plan_height, text_safe.min_height)
```

For swimlane containers:

```
startSize = max(declared_startSize, text_safe.min_startSize)
```

Then re-check grid collisions — grown nodes may overlap neighbours. Shift neighbours outward on the grid (24px increments) as needed before emitting XML.

---

## Measurement algorithm

### Font stack

`Arial, Helvetica, sans-serif` at `fontSize` px (parsed from cell style, default 11). Bold (`fontStyle=1`) widens each character by ×1.08.

### Character width table

Pre-measured per-character widths for Arial at 11px are embedded in the script (`ARIAL_11_WIDTHS`). Width at other sizes = `table_width × (fontSize / 11)`.

Accuracy: ±8% vs browser canvas. Add a 10% margin to `min_width` for safety — the script does this automatically (see `SAFETY_MARGIN` constant, default 1.0 — increase to 1.1 in tight layouts).

### HTML label parsing

The script handles:
- `<b>` / `<strong>` → bold weight
- `<span style="font-size:Npx;">` → per-run font size
- `<br/>` / `<br>` → hard line break
- HTML entities: `&amp;` `&lt;` `&gt;` `&quot;` `&#xa;`
- All other tags stripped (ignored)

### Greedy word-wrap

Given `target_width = declared_width - 2 × PADDING_H` (PADDING_H = 8px):

1. Split each HTML line into word tokens
2. Accumulate words left-to-right; measure each with char table
3. When adding the next word would exceed `target_width`, flush the current line and start a new one
4. First word on a new line is always placed even if it alone exceeds `target_width` (avoids infinite loops on long compound words)

`min_height = line_count × (fontSize × 1.4) + 2 × PADDING_V` (PADDING_V = 4px)

`min_width` = result of the same algorithm with `target_width = Infinity` (no wrapping) — gives the width that fits everything on one line.

---

## Validator checks (W106 / W107 / W108)

`scripts/validate.py` auto-loads `<name>.annotated.plan.json` and emits:

| Code | Level | Condition |
|---|---|---|
| W106 | WARN | Node `width` < `text_safe.min_width` |
| W107 | WARN | Node `height` < `text_safe.min_height` |
| W108 | WARN | Swimlane `startSize` < `text_safe.min_startSize` |
| T801 | INFO | Summary: N elements checked, M overflows |

In `--mode strict`, W106/W107/W108 promote to errors (exit 1).

Pass explicit path: `python3 scripts/validate.py diagram.drawio --annotated-plan diagram.annotated.plan.json`

Disable check: `--features text_metrics=off`

---

## Quick sizing rules (LLM heuristics without running the script)

These apply before running text-metrics.js — use them for first-pass planning:

| Label pattern | Min width | Min height |
|---|---|---|
| Short name ≤ 12 chars | 120px | 48px |
| Medium name 13–25 chars | 160px | 48px |
| Long name 26–40 chars | 240px | 48px |
| Very long name > 40 chars | 280px | 48px |
| C4 three-line (name + type + desc) | 200px | 80px |
| Swimlane header single line | `startSize=26` | — |
| Swimlane header two-line title | `startSize=40` | — |
| Edge label short phrase | — | — (no node) |

These are conservative lower bounds. Text-metrics.js refines them to exact values.

---

## Canvas mode (opt-in)

Pass `--canvas` to use `node-canvas` for pixel-accurate measurement instead of the char table.

Requires system libraries: `brew install pkg-config cairo pango libpng libjpeg giflib librsvg` (macOS) or `apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev` (Ubuntu), then `npm install canvas` in the `scripts/` directory.

The script detects `require('canvas')` failure and silently falls back to char-table, printing `method: "char-table"` in each `text_safe` block. You can tell which mode was used from the `method` field.
