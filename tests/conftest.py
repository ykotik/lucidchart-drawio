"""
Pytest conftest.py — shared fixtures for the diagram test suite.

Discovers test cases from tests/cases/<name>/ directories and
provides fixtures for loading thresholds, plans, drawio files, and PNGs.
"""

import json
import pytest
from pathlib import Path
import ssl

# Bypass SSL certificate verification for downloading EasyOCR models
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass


CASES_DIR = Path(__file__).parent / "cases"


def discover_cases():
    """Find all test case directories that have a thresholds.json."""
    if not CASES_DIR.exists():
        return []
    cases = []
    for d in sorted(CASES_DIR.iterdir()):
        if d.is_dir() and (d / "thresholds.json").exists():
            cases.append(d.name)
    return cases


ALL_CASES = discover_cases()


@pytest.fixture(params=ALL_CASES)
def case_dir(request):
    """Parametrized fixture: yields a Path to each test case directory."""
    return CASES_DIR / request.param


@pytest.fixture
def thresholds(case_dir):
    """Load thresholds.json for the current case."""
    with (case_dir / "thresholds.json").open() as f:
        return json.load(f)


@pytest.fixture
def expected_plan_path(case_dir):
    """Path to the expected.plan.json for OCR content matching."""
    return case_dir / "expected.plan.json"


@pytest.fixture
def drawio_path(case_dir):
    """Path to the reference.drawio file."""
    p = case_dir / "reference.drawio"
    if not p.exists():
        pytest.skip(f"No reference.drawio in {case_dir.name} — generate it first")
    return p


@pytest.fixture
def png_path(case_dir):
    """Path to the reference.png (draw.io CLI export)."""
    p = case_dir / "reference.png"
    if not p.exists():
        pytest.skip(f"No reference.png in {case_dir.name} — export with: drawio -x -f png -o {p} {case_dir / 'reference.drawio'}")
    return p


@pytest.fixture
def baseline_png_path(case_dir):
    """Path to the committed baseline.png for visual regression."""
    return case_dir / "baseline.png"


def pytest_addoption(parser):
    parser.addoption(
        "--update-baselines", action="store_true", default=False,
        help="Copy current reference.png as baseline.png for all cases."
    )


def pytest_sessionfinish(session, exitstatus):
    """If --update-baselines was passed, copy all reference.png -> baseline.png."""
    if session.config.getoption("--update-baselines", default=False):
        import shutil
        for name in ALL_CASES:
            src = CASES_DIR / name / "reference.png"
            dst = CASES_DIR / name / "baseline.png"
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  Updated baseline: {dst}")
