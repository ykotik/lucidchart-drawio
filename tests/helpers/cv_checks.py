"""
Layer 2: Computer Vision checks on rendered PNG diagrams.

Uses OpenCV to detect shape overlaps, blank diagrams, edge visibility,
and other visual quality issues in the exported PNG.
"""

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VisualReport:
    """Results from CV-based visual validation."""
    image_loaded: bool = False
    image_width: int = 0
    image_height: int = 0
    blank_pct: float = 100.0
    contour_count: int = 0
    bounding_boxes: list = field(default_factory=list)
    shape_overlaps: int = 0
    overlap_pairs: list = field(default_factory=list)
    edge_lines_detected: int = 0


def _require_cv2():
    if cv2 is None:
        raise ImportError("opencv-python-headless is required: pip install opencv-python-headless")


def analyze_png(path: str | Path) -> VisualReport:
    """Run CV analysis on a PNG diagram export."""
    _require_cv2()
    report = VisualReport()
    path = Path(path)

    img = cv2.imread(str(path))
    if img is None:
        return report
    report.image_loaded = True
    report.image_height, report.image_width = img.shape[:2]

    # --- Blank detection (histogram) ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    total_pixels = gray.shape[0] * gray.shape[1]
    # Pixels close to white (> 245) are considered "blank"
    white_pixels = int(np.sum(gray > 245))
    report.blank_pct = (white_pixels / total_pixels) * 100.0

    # --- Contour detection (shape counting) ---
    # Threshold to binary (invert so shapes are white on black)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    
    # Erode to wipe out thin connecting line segments (edges)
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    eroded = cv2.erode(thresh, erode_kernel, iterations=1)
    
    # Morphological close on the eroded image to merge text/icons back into shape blobs
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, close_kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter small contours (noise) — keep only those > 1% of image area
    min_area = total_pixels * 0.001
    significant = [c for c in contours if cv2.contourArea(c) > min_area]
    report.contour_count = len(significant)

    # --- Bounding boxes + overlap detection ---
    boxes = []
    for c in significant:
        x, y, w, h = cv2.boundingRect(c)
        boxes.append((x, y, w, h))
    report.bounding_boxes = boxes

    # Check pairwise IoU for overlap
    overlaps = 0
    overlap_pairs = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            iou = _bbox_iou(boxes[i], boxes[j])
            if iou > 0.15:  # significant overlap threshold
                overlaps += 1
                overlap_pairs.append((i, j, round(iou, 3)))
    report.shape_overlaps = overlaps
    report.overlap_pairs = overlap_pairs

    # --- Edge / line detection (Hough) ---
    edges_img = cv2.Canny(gray, 50, 150)
    # Dilate edges slightly to connect broken lines
    edge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges_dilated = cv2.dilate(edges_img, edge_kernel, iterations=1)
    lines = cv2.HoughLinesP(edges_dilated, 1, np.pi / 180, threshold=80,
                            minLineLength=40, maxLineGap=15)
    report.edge_lines_detected = len(lines) if lines is not None else 0

    return report


def _bbox_iou(box_a, box_b):
    """Compute Intersection over Union of two bounding boxes (x, y, w, h)."""
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b

    # Intersection
    ix1 = max(ax, bx)
    iy1 = max(ay, by)
    ix2 = min(ax + aw, bx + bw)
    iy2 = min(ay + ah, by + bh)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = aw * ah
    area_b = bw * bh
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def check_visual_regression(current_png: str | Path, baseline_png: str | Path,
                            max_diff_pct: float = 5.0) -> tuple[bool, float, np.ndarray | None]:
    """Compare current PNG against a baseline using pixelmatch.

    Returns (passed, diff_pct, diff_image_or_None).
    """
    try:
        from PIL import Image
        from pixelmatch import pixelmatch
        from pixelmatch.contrib.PIL import pixelmatch as pil_pixelmatch
    except ImportError:
        # Fallback to basic numpy diff if pixelmatch unavailable
        _require_cv2()
        img_a = cv2.imread(str(current_png))
        img_b = cv2.imread(str(baseline_png))
        if img_a is None or img_b is None:
            return False, 100.0, None
        # Resize if needed
        if img_a.shape != img_b.shape:
            img_b = cv2.resize(img_b, (img_a.shape[1], img_a.shape[0]))
        diff = cv2.absdiff(img_a, img_b)
        diff_pixels = int(np.sum(diff > 30))
        total = img_a.shape[0] * img_a.shape[1] * 3
        pct = (diff_pixels / total) * 100.0
        return pct <= max_diff_pct, pct, diff

    # Use pixelmatch (preferred)
    img_a = Image.open(str(current_png)).convert("RGBA")
    img_b = Image.open(str(baseline_png)).convert("RGBA")

    # Resize baseline to match current if dimensions differ
    if img_a.size != img_b.size:
        img_b = img_b.resize(img_a.size, Image.LANCZOS)

    diff_img = Image.new("RGBA", img_a.size)
    num_diff = pil_pixelmatch(img_a, img_b, diff_img, threshold=0.1, includeAA=True)
    total = img_a.size[0] * img_a.size[1]
    pct = (num_diff / total) * 100.0

    return pct <= max_diff_pct, round(pct, 2), np.array(diff_img)
