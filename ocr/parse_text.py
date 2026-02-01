"""
Parse OCR text from member rows.

Extracts: name, OVR, activity from each row's OCR output.
Uses specialized preprocessing for FC Mobile's game font.
"""

import re
import cv2
import pytesseract
from ocr.preprocess import preprocess_for_names, preprocess_for_numbers


def parse_row(img):
    """
    Parse a row image and extract member data.
    
    Uses region-based approach with specialized preprocessing.
    
    Args:
        img: Raw BGR image of a single row.
        
    Returns:
        Dictionary with 'name', 'ovr', 'activity' or None if parsing fails.
    """
    h, w = img.shape[:2]
    
    # Split into regions based on FC Mobile UI layout
    # Name is in the left portion (after avatar area)
    name_region = img[:, int(w * 0.05):int(w * 0.35)]
    # OVR is just after name
    ovr_region = img[:, int(w * 0.02):int(w * 0.20)]
    # Activity number is on the right side
    activity_region = img[:, int(w * 0.70):]
    
    # Preprocess each region with specialized settings
    name_proc = preprocess_for_names(name_region)
    ovr_proc = preprocess_for_numbers(ovr_region)
    activity_proc = preprocess_for_numbers(activity_region)
    
    # OCR configs
    # PSM 7 = single line, PSM 8 = single word
    config_word = '--psm 8 --oem 3'
    config_line = '--psm 7 --oem 3'
    config_digits = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'
    
    # Extract name
    name = None
    name_text = pytesseract.image_to_string(name_proc, config=config_line)
    name_text = name_text.strip().replace('\n', ' ')
    
    # Clean up common OCR errors
    name_text = name_text.replace('|', 'l').replace('0', 'O')
    
    # Find username pattern
    name_matches = re.findall(r'\b([A-Za-z][A-Za-z0-9_]{1,})\b', name_text)
    noise_words = ['OVR', 'ovr', 'Activity', 'MEMBERS', 'TEAM', 'Title', 'Division']
    for match in name_matches:
        if match not in noise_words and len(match) >= 2:
            name = match
            break
    
    # Extract OVR (look for 3-digit number 100-150)
    ovr = None
    ovr_text = pytesseract.image_to_string(ovr_proc, config=config_line)
    ovr_text = ovr_text.strip()
    
    # Look for OVR pattern
    ovr_match = re.search(r'OVR\s*(\d{2,3})', ovr_text, re.IGNORECASE)
    if ovr_match:
        val = int(ovr_match.group(1))
        if 100 <= val <= 150:
            ovr = val
    else:
        # Just find any 3-digit number in range
        nums = re.findall(r'\b(\d{3})\b', ovr_text)
        for n in nums:
            val = int(n)
            if 100 <= val <= 150:
                ovr = val
                break
    
    # Extract activity (3-5 digit number)
    activity = None
    activity_text = pytesseract.image_to_string(activity_proc, config=config_line)
    activity_text = activity_text.strip()
    
    # Find activity numbers
    activity_nums = re.findall(r'\b(\d{3,5})\b', activity_text)
    if activity_nums:
        # Take largest number
        activity = max(int(n) for n in activity_nums)
    
    # If we couldn't get activity, try full row
    if not activity:
        full_proc = preprocess_for_numbers(img)
        full_text = pytesseract.image_to_string(full_proc, config=config_line)
        nums = re.findall(r'\b(\d{4,5})\b', full_text)
        if nums:
            activity = max(int(n) for n in nums)
    
    # Return data if we have a name
    if name:
        return {
            'name': name,
            'ovr': ovr if ovr else 0,
            'activity': activity if activity else 0
        }
    
    return None


def parse_row_debug(img):
    """
    Debug version that returns raw OCR text from all regions.
    """
    h, w = img.shape[:2]
    
    name_region = img[:, int(w * 0.05):int(w * 0.35)]
    activity_region = img[:, int(w * 0.70):]
    
    name_proc = preprocess_for_names(name_region)
    activity_proc = preprocess_for_numbers(activity_region)
    
    config = '--psm 7 --oem 3'
    
    name_text = pytesseract.image_to_string(name_proc, config=config).strip()
    activity_text = pytesseract.image_to_string(activity_proc, config=config).strip()
    
    return f"NAME: {name_text} | ACTIVITY: {activity_text}"
