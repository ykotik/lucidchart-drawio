"""
Visual regression tests.

Compares reference.png against a committed baseline.png using pixelmatch.
"""

from pathlib import Path
from helpers.cv_checks import check_visual_regression


def test_visual_regression(png_path, baseline_png_path, thresholds):
    """Diagram must visually match the committed baseline image."""
    if not baseline_png_path.exists():
        # If no baseline, skip or pass (we allow establishing baseline via command line)
        import shutil
        shutil.copy2(png_path, baseline_png_path)
        return

    max_diff = thresholds.get("regression", {}).get("max_pixel_diff_pct", 5.0)
    passed, diff_pct, diff_img = check_visual_regression(png_path, baseline_png_path, max_diff)

    if not passed:
        # Write diff image for debugging/artifacts
        diff_out = png_path.parent / f"diff_{png_path.name}"
        import cv2
        if diff_img is not None:
            cv2.imwrite(str(diff_out), diff_img)
        assert passed, (
            f"Visual regression failed: {diff_pct:.2f}% pixel difference (max allowed: {max_diff}%).\n"
            f"Diff image written to: {diff_out}"
        )
