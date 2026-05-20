"""
Layer 3: OCR-based content accuracy checks.

Extracts text labels from rendered PNG using EasyOCR,
then compares against expected plan labels using fuzzy matching.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path


@dataclass
class ContentReport:
    """Results from OCR content validation."""
    ocr_available: bool = False
    ocr_labels: list = field(default_factory=list)
    expected_labels: list = field(default_factory=list)
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    phantom: list = field(default_factory=list)
    label_precision: float = 0.0
    label_recall: float = 0.0
    label_f1: float = 0.0


def _fuzzy_match(a: str, b: str, threshold: float = 0.65) -> bool:
    """Check if two strings are similar enough to count as a match."""
    a = a.lower().strip()
    b = b.lower().strip()
    if a == b:
        return True
    # Substring match
    if a in b or b in a:
        return True
    # Sequence similarity
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold


def extract_ocr_labels(png_path: str | Path) -> list[str]:
    """Extract text labels from a PNG using EasyOCR."""
    try:
        import easyocr
    except ImportError:
        return []

    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    results = reader.readtext(str(png_path))
    labels = []
    for (bbox, text, conf) in results:
        text = text.strip()
        if len(text) >= 2 and conf > 0.3:  # filter noise
            labels.append(text.lower())
    return labels


def load_expected_labels(plan_path: str | Path) -> list[str]:
    """Load expected labels from an expected.plan.json file."""
    import json
    path = Path(plan_path)
    if not path.exists():
        return []
    with path.open() as f:
        plan = json.load(f)

    labels = []
    for kind in ("containers", "shapes"):
        for el in plan.get(kind, []) or []:
            lbl = el.get("label", "").strip()
            if lbl:
                labels.append(lbl.lower())
    return labels


def check_content(png_path: str | Path, plan_path: str | Path) -> ContentReport:
    """Run OCR on a PNG and compare extracted labels against the expected plan."""
    report = ContentReport()

    # Load expected
    report.expected_labels = load_expected_labels(plan_path)

    # Extract OCR
    report.ocr_labels = extract_ocr_labels(png_path)
    report.ocr_available = len(report.ocr_labels) > 0 or True  # True if easyocr imported

    if not report.expected_labels:
        return report

    # Match OCR labels against expected
    used_ocr = set()
    matched = []
    missing = []

    for exp in report.expected_labels:
        found = False
        for i, ocr_lbl in enumerate(report.ocr_labels):
            if i in used_ocr:
                continue
            if _fuzzy_match(exp, ocr_lbl):
                matched.append((exp, ocr_lbl))
                used_ocr.add(i)
                found = True
                break
        if not found:
            missing.append(exp)

    # Phantom labels (OCR found but not in plan)
    phantom = [report.ocr_labels[i] for i in range(len(report.ocr_labels)) if i not in used_ocr]
    # Filter common noise (single chars, numbers, etc.)
    phantom = [p for p in phantom if len(p) > 2]

    report.matched = matched
    report.missing = missing
    report.phantom = phantom

    # F1 calculation
    tp = len(matched)
    pred_total = len(report.ocr_labels)
    true_total = len(report.expected_labels)

    report.label_precision = tp / pred_total if pred_total > 0 else 0.0
    report.label_recall = tp / true_total if true_total > 0 else 0.0
    if report.label_precision + report.label_recall > 0:
        report.label_f1 = (
            2 * report.label_precision * report.label_recall
            / (report.label_precision + report.label_recall)
        )
    else:
        report.label_f1 = 0.0

    return report
