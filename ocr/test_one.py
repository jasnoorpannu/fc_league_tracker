"""
Debug script to test OCR on a single screenshot.

Saves row images to debug_rows/ and prints raw OCR text
for calibration and troubleshooting.
"""

import cv2
import os
from ocr.extract_rows import extract_rows
from ocr.parse_text import parse_row, parse_row_debug

# Output directory for debug images
DEBUG_DIR = "debug_rows"
os.makedirs(DEBUG_DIR, exist_ok=True)

# Test image
IMG_PATH = "screenshots/ss_00.png"


def main():
    print("=" * 60)
    print("OCR Debug - Testing Single Screenshot")
    print("=" * 60)
    
    if not os.path.exists(IMG_PATH):
        print(f"\nERROR: {IMG_PATH} not found.")
        print("Run 'python capture/adb_capture.py' first to capture screenshots.")
        return
    
    print(f"\nProcessing: {IMG_PATH}")
    
    # Extract rows
    rows = extract_rows(IMG_PATH)
    print(f"\nDetected {len(rows)} visual rows\n")
    
    if len(rows) == 0:
        print("No rows detected. Check:")
        print("  1. Screenshot file exists and is valid")
        print("  2. ROI ratios in extract_rows.py match your game UI")
        return
    
    print("-" * 60)
    
    for i, row in enumerate(rows):
        # Save row image for visual inspection
        out_path = f"{DEBUG_DIR}/row_{i:02d}.png"
        cv2.imwrite(out_path, row)
        
        # Get raw OCR text
        raw_text = parse_row_debug(row)
        
        # Try parsing
        parsed = parse_row(row)
        
        print(f"ROW {i:2d} | {out_path}")
        print(f"   Raw: {raw_text[:80]}{'...' if len(raw_text) > 80 else ''}")
        
        if parsed:
            print(f"   ✓ Parsed: {parsed}")
        else:
            print(f"   ✗ Could not parse")
        
        print()
    
    print("-" * 60)
    print(f"\nRow images saved to {DEBUG_DIR}/")
    print("Review these images to verify cropping is correct.")


if __name__ == "__main__":
    main()
