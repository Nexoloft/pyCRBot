"""
Image detection and template matching utilities
"""

import cv2
import os
from config import REF_IMAGES, CONFIDENCE_THRESHOLD


class ImageDetector:
    """Handles image detection and template matching"""
    
    def __init__(self, instance_name):
        self.instance_name = instance_name
    
    def find_template(self, template_name, screenshot=None, confidence=CONFIDENCE_THRESHOLD):
        """Find a template image within a screenshot"""
        if screenshot is None:
            print(f"[{self.instance_name}] No screenshot provided for template matching")
            return None, None
        
        # Load template image
        template_path = REF_IMAGES[template_name]
        if not os.path.exists(template_path):
            print(f"[{self.instance_name}] Template image not found: {template_path}")
            return None, None
            
        template = cv2.imread(template_path)
        if template is None:
            print(f"[{self.instance_name}] Failed to load template: {template_path}")
            return None, None
        
        # Perform template matching
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check if match is above confidence threshold
        if max_val >= confidence:
            # Calculate center of matched area
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y), max_val
        else:
            return None, max_val
    
    def check_pixel_color(self, screenshot, x, y, expected_color=(255, 255, 255), tolerance=30):
        """Check if pixel at (x, y) matches expected color within tolerance"""
        if screenshot is None:
            return False
        
        # Get screenshot dimensions
        height, width = screenshot.shape[:2]
        
        # Check if coordinates are within bounds
        if y >= height or x >= width:
            print(f"[{self.instance_name}] Pixel coordinates ({x}, {y}) out of bounds for screenshot size ({width}x{height})")
            return False
        
        # Get pixel color (BGR format in OpenCV)
        pixel_bgr = screenshot[y, x]
        pixel_rgb = (int(pixel_bgr[2]), int(pixel_bgr[1]), int(pixel_bgr[0]))  # Convert BGR to RGB as integers
        
        # Check if pixel is within tolerance of expected color
        for i in range(3):
            diff = abs(pixel_rgb[i] - expected_color[i])
            if diff > tolerance:
                return False
        
        return True
    
    def pixel_matches_color(self, pixel, expected_color, tolerance=25):
        """Check if a pixel matches an expected color within tolerance"""
        try:
            # Convert BGR to RGB for comparison
            pixel_rgb = [int(pixel[2]), int(pixel[1]), int(pixel[0])]
            for i in range(3):
                if abs(pixel_rgb[i] - expected_color[i]) > tolerance:
                    return False
            return True
        except (IndexError, TypeError):
            return False
    
    def pixel_matches_color_rgb(self, pixel_rgb, expected_color, tolerance=25):
        """Check if a pixel (in RGB format) matches an expected color within tolerance"""
        try:
            for i in range(3):
                if abs(pixel_rgb[i] - expected_color[i]) > tolerance:
                    return False
            return True
        except (IndexError, TypeError):
            return False
    
    def all_pixels_match(self, pixels, colors, tolerance=25):
        """Helper method to check if all pixels match expected colors within tolerance"""
        if len(pixels) != len(colors):
            return False
            
        for pixel, expected_color in zip(pixels, colors):
            if not self.pixel_matches_color(pixel, expected_color, tolerance):
                return False
        return True
    
    def debug_current_screen(self, screenshot, find_template_func):
        """Debug method to check what templates are currently visible"""
        print(f"[{self.instance_name}] DEBUG: Checking current screen for templates...")
        
        # Check all our key templates
        templates_to_check = ["play_again", "ok_button", "battle_button", "in_battle", "confirm"]
        
        for template_name in templates_to_check:
            position, confidence = find_template_func(template_name, screenshot)
            if position:
                print(f"[{self.instance_name}] DEBUG: Found {template_name} at {position} (confidence: {confidence:.2f})")
            else:
                if confidence is not None:
                    print(f"[{self.instance_name}] DEBUG: {template_name} not found (best confidence: {confidence:.2f})")
                else:
                    print(f"[{self.instance_name}] DEBUG: {template_name} not found (no confidence)")
