"""
ADB Capture Module - Device-agnostic screenshot capture with auto-scrolling.

Automatically detects screen resolution and uses ratio-based swipe coordinates
to work across any Android device.
"""

import os
import subprocess
import time
import hashlib
import re

# =========================
# Configuration
# =========================

OUT_DIR = "screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

# Swipe ratios (percentage of screen dimensions)
# These work across any resolution
SWIPE_X_RATIO = 0.75      # Right side where member list is (in landscape)
SWIPE_Y_START_RATIO = 0.70  # 70% down from top
SWIPE_Y_END_RATIO = 0.55    # 55% down from top (scrolls only ~15% of height)

DURATION = 500  # milliseconds (slower swipe)
SCROLLS = 50    # max scrolls (will stop early if end detected)
DELAY = 1.5     # seconds between actions (more time for UI to settle)


# =========================
# Helpers
# =========================

def run(cmd, capture=False):
    """Run a shell command, optionally capturing output."""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if not capture:
        return None
    return result.stdout.strip()


def get_screen_size():
    """
    Detect screen resolution via ADB.
    Returns (width, height) tuple in LANDSCAPE orientation.
    """
    output = run("adb shell wm size", capture=True)
    # Output format: "Physical size: 2800x1200" or "Override size: ..."
    match = re.search(r"(\d+)x(\d+)", output)
    if not match:
        raise RuntimeError(f"Could not parse screen size from: {output}")
    
    w, h = int(match.group(1)), int(match.group(2))
    
    # FC Mobile runs in landscape - ensure width > height
    if h > w:
        print(f"Detected portrait mode ({w}x{h}), swapping to landscape...")
        w, h = h, w
    
    print(f"Screen size (landscape): {w}x{h}")
    return w, h


def screenshot(index):
    """Capture a screenshot and save to disk."""
    path = f"{OUT_DIR}/ss_{index:02d}.png"
    run(f"adb exec-out screencap -p > {path}")
    print(f"Captured {path}")
    return path


def swipe(width, height):
    """Perform a scroll swipe using ratio-based coordinates."""
    x = int(width * SWIPE_X_RATIO)
    y_start = int(height * SWIPE_Y_START_RATIO)
    y_end = int(height * SWIPE_Y_END_RATIO)
    
    cmd = f"adb shell input swipe {x} {y_start} {x} {y_end} {DURATION}"
    run(cmd)


def img_hash(path):
    """Calculate MD5 hash of image for duplicate detection."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# =========================
# Main
# =========================

def main():
    print("=" * 50)
    print("FC League Tracker - Screenshot Capture")
    print("=" * 50)
    
    print("\nChecking ADB connection...")
    devices_output = run("adb devices", capture=True)
    print(devices_output)
    
    if "device" not in devices_output or devices_output.count("\n") < 1:
        print("\nERROR: No device connected. Check USB debugging.")
        return
    
    # Detect screen size
    width, height = get_screen_size()
    
    # Save resolution for OCR module to use
    with open("screen_size.txt", "w") as f:
        f.write(f"{width}x{height}")
    
    input("\nOpen FC Mobile → League → Members, then press Enter...")
    
    print("\nStarting capture...\n")
    
    last_hash = None
    captured_count = 0
    
    for i in range(SCROLLS):
        path = screenshot(i)
        current_hash = img_hash(path)
        
        if current_hash == last_hash:
            print("\n✓ End of list detected. Stopping capture.")
            # Remove duplicate screenshot
            os.remove(path)
            break
        
        last_hash = current_hash
        captured_count += 1
        swipe(width, height)
        time.sleep(DELAY)
    
    print(f"\n{'=' * 50}")
    print(f"Capture complete! {captured_count} screenshots saved.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
