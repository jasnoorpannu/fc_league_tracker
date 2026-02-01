"""
FC League Tracker - Main Pipeline

Processes all screenshots, extracts member data via OCR,
deduplicates by name, and exports to CSV.
"""

import glob
import os
import pandas as pd
from ocr.extract_rows import extract_rows
from ocr.parse_text import parse_row


def main():
    print("=" * 60)
    print("FC League Tracker - Processing Screenshots")
    print("=" * 60)
    
    # Find all screenshots
    screenshot_files = sorted(glob.glob("screenshots/*.png"))
    
    if not screenshot_files:
        print("\nERROR: No screenshots found in screenshots/ folder.")
        print("Run 'python capture/adb_capture.py' first.")
        return
    
    print(f"\nFound {len(screenshot_files)} screenshots")
    print("-" * 60)
    
    # Dictionary for deduplication by name
    members = {}
    total_rows = 0
    parsed_rows = 0
    
    for img_path in screenshot_files:
        print(f"Processing {os.path.basename(img_path)}...", end=" ")
        
        rows = extract_rows(img_path)
        total_rows += len(rows)
        
        file_parsed = 0
        for row in rows:
            parsed = parse_row(row)
            if parsed:
                # Dedupe by name - later entries overwrite earlier
                # (handles partial visibility at screen edges)
                members[parsed["name"]] = parsed
                parsed_rows += 1
                file_parsed += 1
        
        print(f"{len(rows)} rows, {file_parsed} parsed")
    
    print("-" * 60)
    print(f"\nTotal rows detected: {total_rows}")
    print(f"Successfully parsed: {parsed_rows}")
    print(f"Unique members: {len(members)}")
    
    if not members:
        print("\nERROR: No members extracted. Check:")
        print("  1. Run 'python -m ocr.test_one' to debug OCR")
        print("  2. Review debug_rows/ images")
        print("  3. Adjust ROI ratios in extract_rows.py")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Create DataFrame and sort by activity (highest first)
    df = pd.DataFrame(members.values())
    df = df.sort_values("activity", ascending=False)
    df = df.reset_index(drop=True)
    
    # Add rank column
    df.insert(0, "rank", range(1, len(df) + 1))
    
    # Export to CSV
    output_path = "output/league_members.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"✓ Saved {len(df)} members to {output_path}")
    print(f"{'=' * 60}")
    
    # Show top 10
    print("\nTop 10 by Activity:")
    print("-" * 40)
    for _, row in df.head(10).iterrows():
        print(f"  {row['rank']:2d}. {row['name']:<20} OVR:{row['ovr']:3d}  Activity:{row['activity']}")


if __name__ == "__main__":
    main()
