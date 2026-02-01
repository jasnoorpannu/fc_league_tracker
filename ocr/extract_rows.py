"""
Row Extraction Module.

Uses ratio-based cropping and contour detection to find text rows
dynamically, regardless of screen resolution or scroll position.
"""

import cv2
import numpy as np
from .preprocess import preprocess


# Ratio-based ROI for member list area (percentage of screen)
# Based on actual FC Mobile UI layout:
# - Member list panel is on the RIGHT side of landscape screen
# - Names/OVR/Activity are in a vertical list
ROI_X_START = 0.45   # Right panel starts ~45% from left
ROI_X_END = 0.98     # Extends almost to right edge
ROI_Y_START = 0.18   # Below header bar
ROI_Y_END = 0.88     # Above bottom navigation

# Minimum row dimensions (in preprocessed image which is 2x upscaled)
MIN_ROW_HEIGHT = 40   # Lower threshold to catch smaller rows
MIN_ROW_WIDTH = 200   # Minimum width to be a member row


def extract_rows(image_path):
    """
    Extract individual member rows from a screenshot.
    
    Uses contour detection to find text rows dynamically,
    handling variable scroll positions automatically.
    
    Returns:
        List of preprocessed row images, sorted top-to-bottom.
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Warning: Could not read {image_path}")
        return []
    
    h, w = img.shape[:2]
    
    # Ratio-based crop to member list area
    x1 = int(w * ROI_X_START)
    x2 = int(w * ROI_X_END)
    y1 = int(h * ROI_Y_START)
    y2 = int(h * ROI_Y_END)
    
    roi = img[y1:y2, x1:x2]
    
    # Preprocess for OCR
    proc = preprocess(roi)
    
    # Try a different approach: use horizontal projection to find row boundaries
    # This is more reliable for list-style UIs
    rows = extract_rows_by_projection(proc, roi)
    
    if rows:
        return rows
    
    # Fallback to contour method if projection fails
    return extract_rows_by_contours(proc)


def extract_rows_by_projection(proc, original_roi):
    """
    Extract rows using horizontal projection profile.
    Better for detecting evenly-spaced list items.
    """
    # Calculate horizontal projection (sum of white pixels per row)
    projection = np.sum(proc, axis=1)
    
    # Normalize
    projection = projection / np.max(projection) if np.max(projection) > 0 else projection
    
    # Find row boundaries where projection drops (gaps between rows)
    threshold = 0.1
    in_row = False
    row_start = 0
    rows = []
    
    for i, val in enumerate(projection):
        if val > threshold and not in_row:
            # Starting a new row
            in_row = True
            row_start = i
        elif val <= threshold and in_row:
            # Ending current row
            in_row = False
            row_height = i - row_start
            
            if row_height > MIN_ROW_HEIGHT:
                row_img = proc[row_start:i, :]
                rows.append((row_start, row_img))
    
    # Handle last row if still in_row
    if in_row and len(proc) - row_start > MIN_ROW_HEIGHT:
        rows.append((row_start, proc[row_start:, :]))
    
    return [r[1] for r in rows]


def extract_rows_by_contours(proc):
    """
    Fallback method using contour detection.
    """
    # Create horizontal dilation kernel
    kernel_width = proc.shape[1] // 3
    kernel_height = 5
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, 
        (kernel_width, kernel_height)
    )
    
    # Dilate to connect text within rows
    dilated = cv2.dilate(proc, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(
        dilated, 
        cv2.RETR_EXTERNAL, 
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    rows = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        
        if ch > MIN_ROW_HEIGHT and cw > MIN_ROW_WIDTH:
            row = proc[y:y+ch, x:x+cw]
            rows.append((y, row))
    
    # Sort top-to-bottom
    rows.sort(key=lambda r: r[0])
    
    return [row[1] for row in rows]
