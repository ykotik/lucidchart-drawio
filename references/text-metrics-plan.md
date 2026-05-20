# Text Metrics & Label Safety — Implementation Plan

> Feature name: **text_metrics**
> Script: `scripts/text-metrics.js`
> Status: **NOT IMPLEMENTED** — this document is the design spec before coding begins.

---

## Problem statement

The LLM guesses how much text fits inside a node or swimlane header. It does not know the rendered pixel width of the string. The result:

- Long labels overflow the node box visually.
- Short labels that span multiple words get hard-wrapped at a position the LLM invented.
- `startSize=N` swimlane headers are sized by gut feel — a five-word title may clip.
- Tooltip-style sub-labels (`<br/>Description text`) are never checked against container width.

The fix is an **intermediate measurement pass** that runs *after the LLM emits the plan JSON but before it converts the plan to XML*. The script reads every label from the plan, measures it with a headless canvas (the same font metrics as draw.io), and returns the minimum safe node dimensions back to the LLM.

---

## Why d3-textwrap is not the right library here

d3-textwrap is an SVG text-wrapping post-processor — it rewrites existing `<text>` SVG elements to break them across `<tspan>` lines after the fact. draw.io does not expose raw SVG `<text>` nodes for external patching; its XML model uses `mxCell.value` (an HTML-ish label string) and `mxGeometry` (a pixel box). The correct integration point is **pre-flight canvas measurement**, not SVG post-processing.

The insight from the d3-textwrap technique that *is* reusable: treat the container box as a wrapping constraint, apply a greedy line-breaking algorithm, and size the box to fit the resulting line count. We replicate this in Node.js using `canvas`/`@napi-rs/canvas` (headless).

---

## Architecture

```
Plan JSON  (shapes[].label, shapes[].width, shapes[].style)
      │
      ▼
scripts/text-metrics.js   ← NEW
      │  reads each label, measures with headless canvas
      │  returns per-id: { min_width, min_height, line_count, wrapped_lines }
      ▼
Annotated plan JSON  (each shape gains a "text_safe" key)
      │
      ▼
LLM emit XML step  ← reads "text_safe.min_width / min_height"
                      and applies them as node geometry lower bounds
      │
      ▼
validate.py  ← NEW check W106: node smaller than text_safe dims
```

The script is a Node.js CLI (matching the existing `elk-layout.py` which already requires Node.js / npx). It uses `canvas` or `@napi-rs/canvas` for headless text measurement — the same font stack draw.io uses (Arial/Helvetica 11px by default).

---

## Script interface

```bash
# Measure all labels in a plan JSON; print annotated plan to stdout
node scripts/text-metrics.js path/to/diagram.plan.json

# Or read plan from stdin, write to stdout  
cat diagram.plan.json | node scripts/text-metrics.js

# Write annotated plan to a new file
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
```

### Input schema (subset of plan JSON)

```json
{
  "shapes": [
    {
      "id": "erp",
      "label": "<b>SAP S/4HANA</b><br/><span style=\"font-size:10px;\">[ERP Core]</span><br/>Financial ledger, HR, Procurement",
      "style": "rounded=1;whiteSpace=wrap;html=1;fontSize=11;",
      "width": 160,
      "height": 64
    }
  ],
  "containers": [
    {
      "id": "zone_a",
      "label": "Internal Systems",
      "style": "swimlane;startSize=26;fontSize=12;fontStyle=1;",
      "width": 480,
      "height": 400
    }
  ]
}
```

### Output — annotated plan

Same JSON with a `text_safe` key added to each shape/container:

```json
{
  "id": "erp",
  "label": "...",
  "width": 160,
  "height": 64,
  "text_safe": {
    "min_width": 192,
    "min_height": 88,
    "line_count": 3,
    "overflow": true,
    "wrapped_lines": [
      "SAP S/4HANA",
      "[ERP Core]",
      "Financial ledger, HR, Procurement"
    ]
  }
}
```

`overflow: true` means the current declared `width`/`height` is smaller than `min_width`/`min_height`.

---

## Algorithm inside text-metrics.js

### 1. Font stack

draw.io renders labels with `Arial, Helvetica, sans-serif` at `fontSize` from the cell's style (default 11px). The script extracts `fontSize` from the style string using the same `style_kv` logic as elk-layout.py, and passes it to the canvas context:

```js
ctx.font = `${bold ? 'bold ' : ''}${size}px Arial, Helvetica, sans-serif`;
```

### 2. Label parsing

draw.io `value` strings are HTML-ish. The script strips HTML tags before measuring plain text width, and splits on `<br/>` / `<br>` to get logical lines. For `<b>` and `fontStyle=1`, it switches the canvas font to bold.

### 3. Width measurement (greedy word-wrap)

Given a **target width** (the declared `width` minus horizontal padding = `width - 2 * PADDING_H`):

```
PADDING_H = 8   # draw.io default horizontal label margin
PADDING_V = 4   # vertical

for each logical HTML line:
  run Knuth-Plass-inspired greedy wrap:
    word by word: measure cumulative width
    if cumulative > target_width: break line, start new
  record line_count, max_line_width
```

**Min width** = `max_line_width + 2 * PADDING_H` (single-line bound — the narrowest box that avoids wrapping).

**Min height** = `line_count * line_height + 2 * PADDING_V` where `line_height = fontSize * 1.4`.

### 4. Swimlane header special case

For cells with `swimlane` in style, the label lives in the header band (`startSize=N`). Measurement uses `startSize` as the height constraint and the container `width` as the width constraint. If the label doesn't fit in `startSize` height, the script recommends a larger `startSize`.

```json
"text_safe": {
  "min_startSize": 36,
  "overflow": true
}
```

### 5. Multi-line HTML labels (C4 style)

C4 labels use: `<b>Name</b><br/><span style="font-size:10px;">[Type]</span><br/><br/>Description`

The script handles nested font-size in `<span style="font-size:Npx;">` by switching font size mid-parse. Each `<span>` block is measured independently, then the total height sums them.

---

## Integration with SKILL.md workflow

### New feature flag

Add to SKILL.md frontmatter:

```yaml
text_metrics: auto   # off | on | auto — auto = on when plan has any label > 20 chars
```

### Workflow step 7.5 (between plan validation and XML emit)

```
Step 7.5  TEXT METRICS (when text_metrics != off)
  → node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
  → For any shape where text_safe.overflow == true:
      - Increase width to text_safe.min_width
      - Increase height to text_safe.min_height
      - If swimlane: increase startSize to text_safe.min_startSize
  → Re-validate plan grid collisions (nodes may have grown)
```

The LLM reads the annotated plan before emitting XML and applies the `min_width` / `min_height` as hard lower bounds on each shape's `mxGeometry`.

### New validator check W106

In `validate.py`, after XML is emitted, if `diagram.annotated.plan.json` exists:

```
W106  Node '{id}' width={w} < text_safe.min_width={mw} — label will overflow
W107  Node '{id}' height={h} < text_safe.min_height={mh} — label will be clipped
W108  Container '{id}' startSize={s} < text_safe.min_startSize={ms} — header clips label
```

These are warnings (not errors) because overflow may be intentional (e.g., a dense grid where wrapping is acceptable). Promote to errors in `--mode strict`.

---

## Implementation checklist

### Phase 1 — Core script (scripts/text-metrics.js)

- [ ] `npm init -y` + `npm install canvas` (or `@napi-rs/canvas` for M1/M2 compatibility)
  - Check: `node -e "require('canvas')"` succeeds
  - Note: `canvas` requires `libcairo`. On macOS: `brew install pkg-config cairo pango libpng libjpeg giflib librsvg`. On Ubuntu: `apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev`.
  - Fallback: if native canvas unavailable, use **character-width estimation** (see below).

- [ ] Parse CLI args: `--out <path>`, `--padding-h N`, `--padding-v N`, `--line-height-factor N`

- [ ] `parseStyle(styleStr)` → `{fontSize, fontStyle, isBold, isItalic}` — mirrors elk-layout.py's `style_kv`

- [ ] `stripHtml(label)` → plain text (strip tags, decode entities `&amp;` etc.)

- [ ] `splitLines(label)` → array of `{text, fontSize, bold}` — splits on `<br/>`, handles `<b>`, `<span style="font-size:Npx;">`

- [ ] `measureWrapped(lines, targetWidth, ctx)` → `{lineCount, maxLineWidth, totalHeight}`

- [ ] `analyzeShape(shape)` → `text_safe` object (calls above, handles swimlane header case)

- [ ] `annotate(planJson)` → annotated plan JSON (processes shapes + containers)

- [ ] CLI entry point: read plan file or stdin, annotate, write stdout or `--out` file

- [ ] Exit code: 0 always (reporter, not blocker); `--strict` exits 1 if any overflow found

### Phase 2 — Fallback: character-width estimation (no native canvas)

When `canvas` install fails (e.g., CI without libcairo), fall back to a character-width lookup table derived from Arial metrics:

```js
// Average char widths for Arial 11px (measured empirically)
const CHAR_WIDTHS_ARIAL_11 = {
  ' ': 3.0, 'i': 3.4, 'l': 3.4, 'f': 3.8, 'r': 4.0, 't': 4.0,
  'm': 8.5, 'w': 8.0, 'W': 9.5, 'M': 9.0,
  // ... full ASCII table
  default: 6.5  // average fallback
};
```

Scale by `fontSize / 11` and `bold ? 1.1 : 1.0`. Less accurate than canvas (~10% error) but zero native deps. Auto-detected: if `require('canvas')` throws, switch to table mode and add `"method": "char-table"` to each `text_safe` output.

### Phase 3 — SKILL.md integration

- [ ] Add `text_metrics: auto` flag to `features:` block in SKILL.md
- [ ] Add to Feature flags table in SKILL.md (row: `text_metrics`, values `off/on/auto`, default `auto`, description)
- [ ] Update Workflow section: add Step 7.5 with `node scripts/text-metrics.js` invocation
- [ ] Update Pre-flight checklist: add check #13 "All labels fit declared geometry (text_metrics run clean)"

### Phase 4 — validate.py W106/W107/W108

- [ ] In `validate_model()`, after XML checks, look for `<filename>.annotated.plan.json` sibling
- [ ] Load annotated plan; for each shape/container, compare `mxGeometry width/height` to `text_safe.min_width / min_height`
- [ ] Emit W106 / W107 (shape overflow) and W108 (swimlane header overflow)
- [ ] In strict mode: promote these to errors

### Phase 5 — references/text-metrics.md

- [ ] Document the algorithm, fallback, all flags, example output
- [ ] Add to "Reference files" section in SKILL.md

### Phase 6 — eval case

- [ ] Add `eval/cases/text-overflow/` with a prompt that generates a diagram with long multi-word labels
- [ ] `expected.plan.json` includes `text_safe` annotations
- [ ] `eval/run.py` checks that emitted diagram has node dimensions ≥ `min_width/min_height`

---

## Practical node size recommendations to encode in SKILL.md

These are derived from the measurement algorithm for common label patterns at 11px Arial:

| Label type | Typical measured width | Recommended min width |
|---|---|---|
| Short name (≤ 12 chars, single word) | 72–88px | 120px (grid-aligned) |
| Medium name (13–25 chars) | 90–160px | 160px |
| Long name (26–40 chars) | 161–240px | 240px |
| C4 three-line (name + type + description) | 160–200px | 200px, height ≥ 80px |
| Swimlane header (20 chars) | 130px | startSize=26 (single-line), 36 for two-line |
| Edge label (short phrase) | 60–100px | no node sizing needed; check edge spacing |

These ranges assume `whiteSpace=wrap;html=1` (draw.io auto-wraps). The script confirms actual values; these are LLM planning heuristics to apply *before* running the script.

---

## Files to create / modify

| Path | Action | Notes |
|---|---|---|
| `scripts/text-metrics.js` | CREATE | Core measurement script |
| `scripts/package.json` | CREATE | `{"dependencies": {"canvas": "^2.11"}}` |
| `references/text-metrics.md` | CREATE | Algorithm doc (this plan, condensed) |
| `lucidchart-drawio/SKILL.md` | MODIFY | Add `text_metrics` flag, Step 7.5, checklist item #13 |
| `scripts/validate.py` | MODIFY | Add W106/W107/W108 checks |
| `eval/cases/text-overflow/` | CREATE | Regression case |

---

## Dependency risks

| Risk | Mitigation |
|---|---|
| `canvas` needs libcairo (native build) | Phase 2 char-table fallback; document brew/apt commands |
| Node.js not installed | Skill already requires Node.js for ELK — same gate |
| draw.io font rendering ≠ canvas rendering | 5–10% width error acceptable; add 10% safety margin in `min_width` calculation |
| HTML label complexity (nested spans, bold mix) | Parse conservatively: take the widest measured line as the constraint |
| LLM ignores `text_safe` in annotated plan | validate.py W106 catches it post-emit; add explicit instruction in SKILL.md Step 7.5 |

---

## Decision: why not use Dagre for this?

Dagre does node sizing before layout — it's a *layout* engine that incorporates text size. But:
1. We already use ELK for layout (better output quality, nested container support).
2. Dagre is in maintenance mode (archived repo).
3. We only need the **measurement** half of what Dagre does, not a second layout pass.

The text-metrics script gives us the measurement half, ELK gives us layout. Combining them achieves Dagre's "integrated labeling" goal without switching layout engines.
