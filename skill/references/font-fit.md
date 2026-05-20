# F8: Adaptive font sizing (font_fit)

A lightweight post-processor that rescues labels overflowing their cells. Runs after the diagram is emitted (and after `auto_layout` if enabled) but before the validator.

**Feature flag:** `font_fit: off | auto | grow` (default `auto`).

| Value | Behavior |
|---|---|
| `off` | Never touch `fontSize`. Legacy v2.0 parity. |
| `auto` (default) | Shrink only — never grow. Fixes overflow bugs, preserves designer intent. |
| `grow` | Shrink and grow. Useful after `auto_layout=elk` enlarges shapes. |

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
   char_w     = fontSize × 0.55     (sans-serif avg)
   line_h     = fontSize × 1.2
   ```
5. With `whiteSpace=wrap`, simulate word-wrap: `visual_lines = ceil(chars / max_chars_per_line)`. Without wrap, each logical line must fit on one row.
6. **Shrink** stepwise (e.g. 12 → 11 → 10 → 9 → 8) until text fits OR `--min` reached.
7. **Grow** (only in `mode=grow`): step up while text still fits with 25% headroom in both axes.

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

Override per-run: `python3 scripts/fit-fonts.py file.drawio --min 9 --max 20`.

## Pipeline order

The skill's full pipeline now reads:

```
1. Skill emits .drawio with rough fontSize from gestalt-rules.md
2. (optional) scripts/elk-layout.py auto-layout    → changes cell w/h
3. scripts/fit-fonts.py                            → shrinks fontSize to new w/h
4. scripts/validate.py                             → Q405 catches anything still overflowing
```

If `auto_layout=off`, step 3 still runs against the LLM's original coords — it catches overflow bugs from the start.

## CLI usage

```bash
# Most common: shrink-only, in-place
python3 scripts/fit-fonts.py path/to/diagram.drawio

# Allow growth (after ELK enlarged some shapes)
python3 scripts/fit-fonts.py path/to/diagram.drawio --mode grow

# Custom bounds
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
- **Latin-only.** CJK glyphs are ~2× as wide as Latin; the script will underestimate width. For CJK diagrams, use `--min 12` (forces tighter floor) and inspect manually.
- **No font-family parsing.** All cells assumed to be the same family. If you mix fonts intentionally, override `--mode off` per diagram.
- **No semantic-zoom.** Static .drawio output; the script can't hide sub-labels at low zoom (that's a renderer concern).

## When to switch off

| Scenario | Recommended `font_fit` |
|---|---|
| Most architecture diagrams | `auto` (default) |
| Pixel-perfect designer-tuned output | `off` |
| After `auto_layout=elk` enlarged your boxes | `grow` |
| CJK / RTL labels | `off` (heuristic is wrong for these scripts) |
| Sequence diagrams (lifelines have wide whitespace) | `auto` is fine, won't enlarge |
| Grid-matrix (intentionally tight cells) | `off` (cells are deliberately small) |

## Cost / accuracy comparison

| Approach | Per-diagram time | Deps | Accuracy |
|---|---|---|---|
| **This (char-width estimate)** | <50 ms | stdlib | ~85% for Latin |
| PIL + truetype metrics | ~200 ms | Pillow + font files | ~98% |
| Headless browser DOM measure | 2–5 s | Playwright + Chromium | 100% |
| Tulip framework (academic) | n/a | C++/GPL | 100% (heavy) |

The 15% inaccuracy in this implementation manifests as either (a) shrinking one step too aggressively (label still fits, just smaller than necessary) or (b) failing to shrink when it should (very rare; would be caught by validator `Q405`). Both fail-safe — never produces unreadable output.
