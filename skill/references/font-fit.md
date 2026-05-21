# F8: Adaptive font sizing (font_fit)

A lightweight post-processor that rescues labels overflowing their cells. Runs after the diagram is emitted (and after `auto_layout` if enabled) but before the validator. Works with all `auto_layout` modes — no ELK dependency.

**Feature flag:** `font_fit: off | auto | grow` (default `auto`).

| Value | Behavior |
|---|---|
| `off` | Never touch `fontSize`. Legacy v2.0 parity. |
| `auto` (default) | Shrink fonts when text overflows. Preserves designer intent. |
| `grow` | Shrink and grow. In non-elk modes, prefers expanding cells before fonts. |

## Layout modes (`--layout-mode`)

Separate from `--mode`, this flag tells fit-fonts what the upstream layout optimizer did. It governs whether the **cell-expansion pre-pass** runs before font shrinking.

| `--layout-mode` | Behavior |
|---|---|
| `elk` | ELK ran first — cells already optimally sized. Shrink fonts only. **Back-compat default when no marker found.** |
| `off` | No layout optimizer ran. Prefer expanding cells (up to `--max-grow-ratio`) before shrinking fonts. |
| `neato` | Same as `off` — neato does overlap-removal, not size optimization. |
| `graphviz` | Same as `off`. |
| `auto` (default) | Infer from a `data-layout-engine` attribute written by `elk-layout.py`. Falls back to `elk` if no marker found (back-compat). |

### Cell-expansion pre-pass (modes: off, neato, graphviz)

When the layout optimizer did not run (or only ran overlap removal), LLM-emitted cell sizes may be too small for the label text. Rather than immediately shrinking the font, fit-fonts first tries to grow the cell:

1. Compute `required_w` / `required_h` from the char-table heuristic (or from `--metrics` if provided).
2. If `required / current ≤ --max-grow-ratio` (default 1.5), expand the cell's `mxGeometry`.
3. If ratio > max, fall back to font shrinking as usual.

**Worked example — `--layout-mode off`:**
```
Cell "API Gateway"  w=80, h=40, fontSize=12
required_w ≈ 94, required_h ≈ 30
ratio_w = 94/80 = 1.175  ≤ 1.5  → expand w to 94
No font change needed.
```

**Worked example — cell too small even for expansion:**
```
Cell "Long Label That Won't Fit"  w=40, h=24, fontSize=12
required_w ≈ 130
ratio_w = 130/40 = 3.25  > 1.5  → skip expansion, shrink font instead
font: 12 → 8 (min floor)
```

**Worked example — `--layout-mode elk` (back-compat):**
```
Cell "Okta SSO"  w=120, h=60, fontSize=12 (ELK already set this)
text_fits() → True → no change
```

## Algorithm

Pure stdlib Python, no PIL / no glyph metrics / no browser. Per vertex cell:

1. Parse current `fontSize` from style (default 12 if missing)
2. Strip HTML from `value`; split on `<br/>`, `<br>`, `\n` → logical lines
3. Compute available text area:
   ```
   available_w = width  − spacingLeft − spacingRight
   available_h = height − startSize    − spacingTop − spacingBottom
   ```
   `startSize` is the swimlane header offset (0 for non-containers).
4. Compute text dimensions at current size using approximation:
   ```
   char_w (Latin) = fontSize × 0.55     (sans-serif avg)
   char_w (CJK)   = fontSize × 1.0      (square cell, ~1 em)
   char_w (emoji) = fontSize × 1.2
   line_h         = fontSize × 1.2
   ```
5. With `whiteSpace=wrap`, simulate word-wrap: `visual_lines = ceil(text_px_w / available_w)`. Without wrap, each logical line must fit on one row.
6. **Pre-pass** (non-elk modes): try to expand the cell — see Layout modes above.
7. **Shrink** stepwise (e.g. 12 → 11 → 10 → 9 → 8) until text fits OR `--min` reached.
8. **Grow** (only in `mode=grow`): step up while text still fits with 25% headroom in both axes.

### CJK and emoji handling

The char-width heuristic mirrors the codepoint ranges in `text-metrics.js`:

| Script | Codepoint range | Width factor |
|---|---|---|
| Hiragana / Katakana | U+3040–U+30FF | 1.0 × fontSize |
| CJK Unified + Extension A | U+3400–U+9FFF | 1.0 × fontSize |
| Hangul | U+AC00–U+D7AF | 1.0 × fontSize |
| Fullwidth Forms | U+FF00–U+FFEF | 1.0 × fontSize |
| Misc Symbols / Dingbats | U+2600–U+27BF | 1.2 × fontSize |
| Emoji (Misc Symbols, Pictographs) | U+1F300–U+1F9FF | 1.2 × fontSize |

For highest accuracy with CJK/emoji labels, pass `--metrics` (see below) to use precomputed widths from `text-metrics.js`.

## `--metrics` interop with text-metrics.js

`text-metrics.js` annotates every plan shape with a `text_safe` block containing `min_width` and `min_height`. When you pass `--metrics path/to/annotated.plan.json` to fit-fonts, the pre-pass reads these precomputed values instead of re-computing from heuristic:

```bash
# Step 1: annotate the plan
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json

# Step 2: emit .drawio (uses annotated plan)

# Step 3: run fit-fonts with metrics
python3 scripts/fit-fonts.py diagram.drawio \
  --layout-mode off \
  --metrics diagram.annotated.plan.json \
  --max-grow-ratio 1.5
```

The lookup key is the shape's `id` field (matches mxCell `id` attribute in the `.drawio` file). Shapes not found in the metrics map fall back to the char-table heuristic.

The annotated plan emits `text_safe.min_w` and `text_safe.min_h` as convenience aliases (same values as `min_width` / `min_height`).

## What gets skipped

| Cell type | Reason |
|---|---|
| `style="text;..."` cells | Titles, legend chrome — sized intentionally |
| `edgeLabel=1` cells | drawio repositions these dynamically; static sizing conflicts |
| Cells with empty `value` | Nothing to fit |
| Cells with `width=0` or `height=0` | Edge geometry placeholders |
| Cells with `geometry relative="1"` and no w/h | Floating edge labels |

## Bounds

| Argument | Default | Why |
|---|---|---|
| `--min` | 8 | drawio renders smaller text but it's unreadable on print |
| `--max` | 18 | Above this would break visual hierarchy against titles (font 14) |
| `--max-grow-ratio` | 1.5 | Prevents ballooning cells that are grossly undersized — fall back to font shrink |

Override per-run: `python3 scripts/fit-fonts.py file.drawio --min 9 --max 20 --max-grow-ratio 2.0`.

## Pipeline order

The skill's full pipeline reads:

```
1. Skill emits .drawio with rough fontSize from gestalt-rules.md
2. (optional) scripts/elk-layout.py auto-layout    → changes cell w/h
3. scripts/fit-fonts.py                            → expands cells and/or shrinks fontSize
4. scripts/validate.py                             → Q405 catches anything still overflowing
```

`fit-fonts` works correctly regardless of whether step 2 ran. Pass `--layout-mode` to communicate the upstream state:
- After ELK: `--layout-mode elk` (or omit — auto-infer)
- No layout run: `--layout-mode off`
- After neato overlap-removal only: `--layout-mode neato`

## CLI usage

```bash
# Most common: shrink-only, in-place (back-compat)
python3 scripts/fit-fonts.py path/to/diagram.drawio

# Non-elk pipeline: expand cells first, then shrink fonts
python3 scripts/fit-fonts.py path/to/diagram.drawio --layout-mode off

# With precomputed metrics from text-metrics.js
python3 scripts/fit-fonts.py path/to/diagram.drawio \
  --layout-mode off \
  --metrics path/to/annotated.plan.json

# Allow cell + font growth (after ELK enlarged some shapes)
python3 scripts/fit-fonts.py path/to/diagram.drawio --mode grow

# Cap cell expansion ratio
python3 scripts/fit-fonts.py path/to/diagram.drawio --layout-mode off --max-grow-ratio 2.0

# Custom font bounds
python3 scripts/fit-fonts.py path/to/diagram.drawio --min 9 --max 20

# Dry-run (preview, don't write)
python3 scripts/fit-fonts.py path/to/diagram.drawio --dry-run

# Output to a new file
python3 scripts/fit-fonts.py in.drawio out.drawio

# Disable via feature flag (matches SKILL.md `font_fit: off`)
python3 scripts/fit-fonts.py path/to/diagram.drawio --features font_fit=off
```

## Known limitations (intentional)

- **Sans-serif assumption.** Char-width ratio (0.55) is calibrated for Helvetica/Arial/Inter. Serif fonts run ~5% wider; would underestimate overflow.
- **CJK heuristic.** CJK chars use 1.0× fontSize; the heuristic is correct for square-cell scripts but loses accuracy for mixed Latin+CJK. Use `--metrics` for mixed-script diagrams.
- **No font-family parsing.** All cells assumed to be the same family. If you mix fonts intentionally, override `--mode off` per diagram.
- **No semantic-zoom.** Static .drawio output; the script can't hide sub-labels at low zoom (that's a renderer concern).

## When to switch off

| Scenario | Recommended `font_fit` |
|---|---|
| Most architecture diagrams | `auto` (default) |
| Pixel-perfect designer-tuned output | `off` |
| After `auto_layout=elk` enlarged your boxes | `grow` |
| No layout run, need cells to expand | `auto --layout-mode off` |
| CJK / RTL labels, no metrics file | `off` or `auto --metrics annotated.plan.json` |
| Sequence diagrams (lifelines have wide whitespace) | `auto` is fine, won't enlarge |
| Grid-matrix (intentionally tight cells) | `off` (cells are deliberately small) |

## Cost / accuracy comparison

| Approach | Per-diagram time | Deps | Accuracy |
|---|---|---|---|
| **This (char-width estimate)** | <50 ms | stdlib | ~85% Latin, ~80% CJK |
| With `--metrics` (text-metrics.js) | <50 ms | Node.js (already required) | ~92% |
| PIL + truetype metrics | ~200 ms | Pillow + font files | ~98% |
| Headless browser DOM measure | 2–5 s | Playwright + Chromium | 100% |

The ~15% inaccuracy manifests as either (a) shrinking one step too aggressively or (b) failing to shrink when it should (very rare; caught by validator `Q405`). Both fail-safe — never produces unreadable output.
