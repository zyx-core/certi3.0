import re
from typing import List
from PIL import Image
import pytesseract
import cv2
import numpy as np

def clean_placeholder(name: str) -> str:
    corrections = {
        "nane": "name",
        # Add more common OCR mistakes here if needed
    }
    return corrections.get(name.lower(), name)

def extract_placeholders_from_text(text: str) -> List[str]:
    # Regex to match noisy placeholders in braces or parentheses
    matches = re.findall(r"[\(\{]+[^a-zA-Z0-9]*([a-zA-Z0-9_]+)[^a-zA-Z0-9]*[\)\}]+", text)
    cleaned = [clean_placeholder(m) for m in matches]
    return list(set(cleaned))  # Remove duplicates

def extract_placeholders_from_image(image_path: str) -> List[str]:
    # Load image in grayscale using OpenCV
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"❌ Error: Unable to load image from {image_path}")
        return []

    # Enhance contrast using histogram equalization
    img = cv2.equalizeHist(img)

    # Apply adaptive thresholding (binarization)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)

    # Morphological operations to reduce noise
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)

    # Convert back to PIL Image for pytesseract
    pil_img = Image.fromarray(img)

    # OCR with tesseract, psm 6 assumes uniform block of text
    text = pytesseract.image_to_string(pil_img, config='--psm 6')

    print("🔍 OCR Output:\n", text)

    return extract_placeholders_from_text(text)

if __name__ == "__main__":
    # Example usage:
    test_image_path = "certificate_template.png"
    placeholders = extract_placeholders_from_image(test_image_path)
    print("Extracted placeholders:", placeholders)
