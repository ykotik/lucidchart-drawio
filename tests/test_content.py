"""
Layer 3 Tests: OCR-based content accuracy validation.

These tests use EasyOCR to extract text from the rendered PNG
and check it against expected labels in expected.plan.json.
"""

import pytest

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from helpers.ocr_checks import check_content


@pytest.mark.skipif(not OCR_AVAILABLE, reason="easyocr not installed")
class TestContent:
    """Content accuracy checks via OCR — Layer 3."""

    def test_ocr_label_recall(self, png_path, expected_plan_path, thresholds):
        """Rendered diagram text must contain the expected labels (Recall)."""
        report = check_content(png_path, expected_plan_path)
        min_recall = thresholds.get("content", {}).get("min_label_recall", 0.70)
        assert report.label_recall >= min_recall, (
            f"OCR Label Recall of {report.label_recall:.2f} is below threshold {min_recall}.\n"
            f"Matched: {len(report.matched)}\n"
            f"Missing: {report.missing[:10]}"
        )

    def test_no_excessive_phantom_labels(self, png_path, expected_plan_path, thresholds):
        """The diagram must not contain too much unrecognized text (phantom labels)."""
        report = check_content(png_path, expected_plan_path)
        max_phantom = thresholds.get("content", {}).get("max_phantom_labels", 5)
        assert len(report.phantom) <= max_phantom, (
            f"Found {len(report.phantom)} unrecognized OCR labels (max allowed: {max_phantom}):\n"
            f"{report.phantom[:10]}"
        )
