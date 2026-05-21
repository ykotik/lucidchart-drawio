# fit-containers.md — Container Auto-Shrink Reference

## Purpose

`scripts/fit-containers.py` shrinks container cells (swimlanes, groups, nested boxes) to tightly wrap their children's bounding box plus padding. It eliminates wasted whitespace that the LLM or ELK may leave inside containers, improving diagram density and Q404 area-utilization scores.

## When to use

| Situation | Tool |
|---|---|
| Containers have excess empty space around children | `fit-containers.py` |
| Children overlap each other or spill outside container | `elk-layout.py --engine neato` |
| Font overflow inside fixed-size cells | `fit-fonts.py` |
| Both overlap removal AND tight containers | elk-layout first, then fit-containers |

## Algorithm

1. **Parse** — load all `mxCell` and `object/mxCell` elements from every `mxGraphModel` page.
2. **Identify containers** — cells with `vertex="1"` that have at least one child referencing them as `parent`.
3. **Sort bottom-up** — sort containers by depth (deepest first) so child containers shrink before their parents. This ensures parent shrink uses already-updated child dimensions.
4. **Compute children bbox** — for each container, gather all direct `vertex="1"` children, read their `mxGeometry` (x, y, width, height). Children use container-relative coordinates per the repo's #1 rule — no coordinate translation needed.
5. **Detect swimlane header** — parse the `style` string for `swimlane` or `table` key, read `startSize` (default 20). Check `horizontal` flag: `horizontal=1` (default) → top header; `horizontal=0` → left header. Reserve `startSize` on the header axis.
6. **Compute target size**:
   ```
   # horizontal header (default)
   target_w = (bbox.max_x - bbox.min_x) + padding * 2
   target_h = (bbox.max_y - bbox.min_y) + padding * 2 + startSize

   # vertical header (horizontal=0)
   target_w = (bbox.max_x - bbox.min_x) + padding * 2 + startSize
   target_h = (bbox.max_y - bbox.min_y) + padding * 2
   ```
7. **Apply floor** — clamp to `--min-container-size` (default 160×80).
8. **Shrink only** — if `target < current`, update `mxGeometry width/height`. Skip if `target >= current` (warn if `--also-grow` not set). Never move the container (x/y unchanged).

## Padding semantics

`--padding N` (default 24px) is applied uniformly on all four sides of the children bbox. The padding sits between the children's outermost edges and the container wall — not between the header and the first child.

Children that sit at `y=0` inside a swimlane already sit below the header; the header reservation is added on top of the padding.

## CLI reference

```
python3 skill/scripts/fit-containers.py diagram.drawio
python3 skill/scripts/fit-containers.py diagram.drawio --output out.drawio
python3 skill/scripts/fit-containers.py diagram.drawio --padding 32
python3 skill/scripts/fit-containers.py diagram.drawio --also-grow
python3 skill/scripts/fit-containers.py diagram.drawio --dry-run
python3 skill/scripts/fit-containers.py diagram.drawio --min-container-size 120,60
python3 skill/scripts/fit-containers.py diagram.drawio --exclude-pattern layer1,bg,*-header
python3 skill/scripts/fit-containers.py diagram.drawio --verbose
```

## Pipeline position

```
emit .drawio
→ elk-layout.py    (optional)
→ route-edges.py   (optional)
→ fit-fonts.py     (optional)
→ fit-containers.py   ← here
→ validate.py
```

## Validator interaction

After shrinking, Q404 (area utilization) typically improves as container area aligns with actual content. E-series overflow errors should not be introduced — children remain within the new bounds because target size was computed from their bbox.
