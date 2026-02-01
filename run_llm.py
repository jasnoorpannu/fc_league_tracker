"""
FC League Tracker - LLM Pipeline

Processes all screenshots using Groq's Llama 4 Maverick,
deduplicates by name (with fuzzy matching), and exports to CSV.
"""

import glob
import os
import time
import re
import pandas as pd
from llm.llm_extract import extract_members


def normalize_name(name: str) -> str:
    """Normalize name for comparison by removing punctuation and lowercasing."""
    # Remove trailing dots, underscores, dashes
    name = re.sub(r'[._\-]+$', '', name)
    # Remove all non-alphanumeric except underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    return name.lower()


def fuzzy_match(name1: str, name2: str) -> bool:
    """Check if two names are similar enough to be the same person."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    # Exact match after normalization
    if n1 == n2:
        return True
    
    # One is prefix of the other (at least 4 chars)
    if len(n1) >= 4 and len(n2) >= 4:
        if n1.startswith(n2) or n2.startswith(n1):
            return True
    
    # Levenshtein distance <= 2 for names >= 5 chars
    if len(n1) >= 5 and len(n2) >= 5:
        if levenshtein(n1, n2) <= 2:
            return True
    
    return False


def levenshtein(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    
    return prev_row[-1]


def find_matching_member(name: str, members: dict) -> str | None:
    """Find an existing member key that matches the given name."""
    for existing_name in members:
        if fuzzy_match(name, existing_name):
            return existing_name
    return None


def main():
    print("=" * 60)
    print("FC League Tracker - LLM Extraction (Llama 4 Maverick)")
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
    total_extracted = 0
    duplicates_merged = 0
    
    for i, img_path in enumerate(screenshot_files):
        print(f"[{i+1}/{len(screenshot_files)}] Processing {os.path.basename(img_path)}...", end=" ")
        
        extracted = extract_members(img_path)
        total_extracted += len(extracted)
        
        for m in extracted:
            name = m.get("name", "").strip()
            activity = m.get("activity", 0)
            
            if not name or len(name) < 2:
                continue
            
            # Skip UI elements that might be misread as names
            skip_names = ["Division Rivals", "Activity", "Title", "MEMBERS", "OVR"]
            if any(skip.lower() in name.lower() for skip in skip_names):
                continue
            
            # Check for fuzzy match with existing member
            match_key = find_matching_member(name, members)
            
            if match_key:
                # Merge: keep the one with same activity (dedupe across screenshots)
                # or keep the one with longer/cleaner name
                existing = members[match_key]
                if existing.get("activity") == activity:
                    # Same activity = same person, keep longer name
                    if len(name) > len(match_key):
                        members[name] = m
                        del members[match_key]
                    duplicates_merged += 1
                elif activity > existing.get("activity", 0):
                    # Higher activity, update
                    members[match_key] = m
            else:
                # New member
                members[name] = m
        
        print(f"found {len(extracted)} members")
        
        # Rate limiting for Groq API
        if i < len(screenshot_files) - 1:
            time.sleep(0.5)
    
    print("-" * 60)
    print(f"\nTotal extracted: {total_extracted}")
    print(f"Duplicates merged: {duplicates_merged}")
    print(f"Unique members: {len(members)}")
    
    if not members:
        print("\nERROR: No members extracted. Check API key and network.")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Create DataFrame and sort by activity (highest first)
    df = pd.DataFrame(members.values())
    
    # Ensure columns exist
    for col in ["name", "ovr", "activity"]:
        if col not in df.columns:
            df[col] = 0
    
    df = df.sort_values("activity", ascending=False)
    df = df.reset_index(drop=True)
    
    # Add rank column
    df.insert(0, "rank", range(1, len(df) + 1))
    
    # Export to CSV
    output_path = "output/league_members_llm.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"✓ Saved {len(df)} members to {output_path}")
    print(f"{'=' * 60}")
    
    # Show top 10
    print("\nTop 10 by Activity:")
    print("-" * 50)
    for _, row in df.head(10).iterrows():
        print(f"  {row['rank']:2d}. {row['name']:<20} OVR:{row['ovr']:3}  Activity:{row['activity']}")


if __name__ == "__main__":
    main()
