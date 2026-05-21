# drawio-architect

## Project Overview

This repository is the source for the **`drawio-architect`** Claude skill (v2.1). The skill generates clean draw.io / mxGraph XML (`.drawio` files) that can be imported seamlessly into Lucidchart, draw.io desktop, and any other mxGraph-aware tool.

## Core Features

- **15 Layout Patterns**: Supports a wide variety of standard layout templates including:
  - `hub-radial`, `scope-columns`, `swimlanes`, `pipeline`, `tenant-namespace`
  - `c4-context/container/component`, `erd-crowfoot`, `uml-class`
  - `sequence`, `flowchart-dag`, `bpmn-process`, `tree-hierarchy`, `grid-matrix`
- **Container-Relative Coordinates**: Ensures elements inside containers use local coordinates relative to the container's top-left, rather than absolute canvas coordinates.
- **Feature Flags**: Customizable settings for auto-layout, edge-routing, text metrics, and grounding manifests.
- **Style Dictionary Enforcement**: Uses a strict palette and approved shape vocabularies (AWS, Azure, GCP, UML/ERD/BPMN).

## Repository Layout

- `skill/` - The core skill orchestrator (`SKILL.md`), references, scripts, and the 15 template skeletons.
- `docs/` - Research and documentation on the LLM-to-diagram generation landscape.
- `tests/` - Comprehensive multi-layered testing suite (structure, content, regression, visual).

## Usage & Scripts

To run the validation or processing scripts, activate your virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate

# Validate a generated diagram
python3 scripts/validate.py path/to/diagram.drawio
python3 scripts/validate.py path/to/diagram.drawio --mode strict

# Perform auto-layout or post-processing
python3 scripts/elk-layout.py path/to/diagram.drawio --engine neato
python3 scripts/fit-fonts.py path/to/diagram.drawio --mode auto
node scripts/text-metrics.js diagram.plan.json --out diagram.annotated.plan.json
```

## Testing Suite

This repository uses `pytest` alongside various image processing libraries (`opencv-python-headless`, `easyocr`, `Pillow`, `pixelmatch`) to comprehensively test diagram outputs across 4 distinct layers.

### Test Layers

1. **Layer 1: XML Structure (`test_xml_structure.py`)** - Validates well-formed XML, correct parent/child ID associations, and basic edge geometry constraints.
2. **Layer 2: Content Verification (`test_content.py`)** - Uses OCR heuristics to ensure node labels and text elements are present and rendered correctly.
3. **Layer 3: Regression Testing (`test_regression.py`)** - Performs pixel-diff regression comparisons of the generated diagram against a known `baseline.png`.
4. **Layer 4: Visual Quality (`test_visual.py`)** - Uses specific visual heuristics to verify design quality metrics (edge crossings, orthogonality).

### Running the Tests

Before running the tests, install the required testing dependencies:

```bash
source .venv/bin/activate
pip install -r tests/requirements.txt
```

You can execute the test suite via pytest:

```bash
# Run all test layers
pytest tests/

# Run only Layer 1 (fastest, does not require image processing dependencies)
pytest tests/test_xml_structure.py

# Refresh baseline.png images for visual regression tests
pytest tests/ --update-baselines
```

### Adding a New Test Case

1. Create a new directory for the test case in `tests/cases/<name>/`.
2. Add a `thresholds.json` and an `expected.plan.json` which define the acceptable error boundaries and test parameters.
3. Generate your initial `reference.drawio` file.
4. Export a `reference.png` via the draw.io CLI or UI.
5. Run `pytest tests/ --update-baselines` to generate and commit the initial `baseline.png` for future regression runs.
