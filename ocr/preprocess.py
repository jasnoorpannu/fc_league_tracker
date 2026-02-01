"""
Preprocessing module for FC Mobile screenshots.

Uses multiple preprocessing strategies for game UI text.
"""

import cv2
import numpy as np


def preprocess(img):
    """
    Preprocess row image for OCR.
    
    FC Mobile uses white text on dark backgrounds with styling.
    We need to enhance contrast and clean up the text.
    """
    # Scale up for better OCR accuracy
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Increase contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Threshold to get white text
    # The text is white (high value), background is darker
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    
    # Minimal morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh


def preprocess_for_names(img):
    """
    Specialized preprocessing for name region (left side of row).
    Names are white text with potential shadows.
    """
    # Scale up significantly
    img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Apply CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Use adaptive thresholding for varying backgrounds
    thresh = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        21, -5
    )
    
    return thresh


def preprocess_for_numbers(img):
    """
    Specialized preprocessing for number regions (OVR, Activity).
    Numbers are typically clearer than stylized names.
    """
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Simple Otsu threshold works well for numbers
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh
