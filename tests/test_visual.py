"""
Layer 2 Tests: Visual / CV checks on rendered PNG exports.

These tests use OpenCV to analyze the PNG image exported from draw.io CLI.
They detect shape overlaps, blank diagrams, and edge visibility.
"""

import pytest

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from helpers.cv_checks import analyze_png


@pytest.mark.skipif(not CV2_AVAILABLE, reason="opencv-python-headless not installed")
class TestVisual:
    """Visual quality checks on rendered PNG — Layer 2."""

    def test_image_loads(self, png_path):
        """The exported PNG must be a valid, loadable image."""
        report = analyze_png(png_path)
        assert report.image_loaded, f"Could not load PNG: {png_path}"

    def test_not_blank(self, png_path, thresholds):
        """The diagram must not be blank (mostly white pixels)."""
        report = analyze_png(png_path)
        max_blank = thresholds.get("visual", {}).get("max_blank_pct", 95)
        assert report.blank_pct <= max_blank, (
            f"Diagram is {report.blank_pct:.1f}% blank (threshold: {max_blank}%)"
        )

    def test_minimum_contours(self, png_path, thresholds):
        """The rendered image must contain enough visual elements."""
        report = analyze_png(png_path)
        min_contours = thresholds.get("visual", {}).get("min_contour_count", 20)
        assert report.contour_count >= min_contours, (
            f"Only {report.contour_count} visual elements detected, need at least {min_contours}"
        )

    def test_no_shape_overlaps(self, png_path, thresholds):
        """Shapes must not significantly overlap each other."""
        report = analyze_png(png_path)
        max_overlaps = thresholds.get("visual", {}).get("max_shape_overlaps", 0)
        assert report.shape_overlaps <= max_overlaps, (
            f"Found {report.shape_overlaps} shape overlaps: {report.overlap_pairs[:5]}"
        )

    def test_edges_visible(self, png_path, thresholds):
        """Connector lines must be detectable in the rendered image."""
        report = analyze_png(png_path)
        min_lines = thresholds.get("visual", {}).get("min_edge_lines_detected", 8)
        assert report.edge_lines_detected >= min_lines, (
            f"Only {report.edge_lines_detected} line segments detected, need at least {min_lines}"
        )
