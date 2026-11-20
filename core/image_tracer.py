import cv2
import numpy as np


def _signed_area(points):
    """Calculates signed area to determine contour winding direction."""
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += (x1 * y2) - (x2 * y1)
    return area / 2.0


def trace_image_to_contours(
    image_path,
    units_per_em=1000,
    baseline_ratio=0.20,
    simplify_epsilon=1.2,
    use_canvas_scale=True,
):
    """
    Converts a character image into TrueType-ready contours.
    
    :param baseline_ratio: Where the baseline sits from the bottom of the image (0.20 = 20% up).
    :param use_canvas_scale: If True, scales relative to full image height (preserves proportions).
                             If False, stretches glyph bounding box to fit ascender height.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return [], 300, 0

    img_h, img_w = img.shape

    # Ensure white ink on black background
    if np.mean(img) > 127:
        _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    else:
        _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

    # Extract contours with 2-level hierarchy (outer vs inner holes)
    contours, hierarchy = cv2.findContours(
        thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours or hierarchy is None:
        return [], 300, 0

    hierarchy = hierarchy[0]
    all_pts = np.vstack(contours)
    x_min, y_min, bbox_w, bbox_h = cv2.boundingRect(all_pts)

    if use_canvas_scale:
        scale = units_per_em / float(img_h)
        baseline_px_from_top = img_h * (1.0 - baseline_ratio)
    else:
        target_h = units_per_em * 0.75
        scale = target_h / float(max(bbox_h, 1))
        baseline_px_from_top = y_min + bbox_h

    normalized_contours = []

    for idx, cnt in enumerate(contours):
        # Smooth out pixel staircases
        approx = cv2.approxPolyDP(cnt, epsilon=simplify_epsilon, closed=True)
        if len(approx) < 3:
            continue

        # hierarchy[idx][3] == -1 means outer contour; >= 0 means inner hole
        is_hole = hierarchy[idx][3] != -1

        pts = []
        for point in approx:
            px, py = point[0]
            # Shift X so left-most ink starts at x = 0
            nx = int(round((px - x_min) * scale))
            # Flip Y and align relative to baseline
            ny = int(round((baseline_px_from_top - py) * scale))
            pts.append((nx, ny))

        # Remove consecutive duplicate points caused by integer rounding
        dedup_pts = [pts[0]]
        for p in pts[1:]:
            if p != dedup_pts[-1]:
                dedup_pts.append(p)
        if len(dedup_pts) > 2 and dedup_pts[0] == dedup_pts[-1]:
            dedup_pts.pop()

        if len(dedup_pts) < 3:
            continue

        # TrueType winding rule: outer contours should be clockwise (negative area in Y-up),
        # inner holes should be counter-clockwise (positive area in Y-up).
        area = _signed_area(dedup_pts)
        if not is_hole and area > 0:
            dedup_pts.reverse()
        elif is_hole and area < 0:
            dedup_pts.reverse()

        normalized_contours.append(dedup_pts)

    lsb = 40  # Left side bearing
    rsb = 60  # Right side bearing
    glyph_width = int(round(bbox_w * scale))
    advance_width = glyph_width + lsb + rsb

    # Shift contours right by LSB so glyph sits cleanly inside its advance box
    shifted_contours = [
        [(x + lsb, y) for (x, y) in contour] for contour in normalized_contours
    ]

    return shifted_contours, advance_width, lsb