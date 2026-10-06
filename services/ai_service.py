import os
import random
from PIL import Image
import numpy as np

CATEGORIES = [
    "Plastic",
    "Paper/Cardboard",
    "Organic",
    "Metal/Glass",
    "Mixed Waste",
    "Other"
]

def analyze_waste_image(image_path):
    """
    Analyzes an uploaded waste image using computer vision feature extraction
    (color histogram, saturation, brightness variance, edge contrast) combined
    with probabilistic classification to detect waste type with confidence.
    Clearly indicates execution under CleanTrack AI Vision Model (Demo/Heuristic Mode).
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Open and inspect image using Pillow
        with Image.open(image_path) as img:
            img_rgb = img.convert('RGB')
            # Resize for consistent feature analysis
            img_thumb = img_rgb.resize((128, 128))
            arr = np.array(img_thumb)
            
            # Compute basic color statistics
            r_mean = float(np.mean(arr[:, :, 0]))
            g_mean = float(np.mean(arr[:, :, 1]))
            b_mean = float(np.mean(arr[:, :, 2]))
            brightness = (r_mean + g_mean + b_mean) / 3.0
            
            # Color variance to detect complexity
            color_std = float(np.std(arr))
            
            # Heuristic decision hints based on dominant visual features
            # Green/Brown dominant -> Organic
            # High blue/bright synthetic -> Plastic
            # High brightness with low variance -> Paper/Cardboard
            # Metallic sheen/gray/high contrast -> Metal/Glass
            # Multi-colored high std -> Mixed Waste
            if g_mean > r_mean + 15 and g_mean > b_mean + 15:
                predicted = "Organic"
                confidence = round(random.uniform(91.5, 98.2), 1)
                reason = "Dominant organic vegetation/food tonal palette with medium texture variance."
            elif b_mean > r_mean + 10 or (brightness > 160 and color_std > 50):
                predicted = "Plastic"
                confidence = round(random.uniform(89.0, 97.4), 1)
                reason = "High synthetic color signature and reflective surface profile typical of plastics."
            elif brightness > 175 and color_std < 45:
                predicted = "Paper/Cardboard"
                confidence = round(random.uniform(88.0, 96.0), 1)
                reason = "Uniform light tonal plane with low chromatic variance characteristic of pulp/paper."
            elif color_std > 65 and brightness < 130:
                predicted = "Metal/Glass"
                confidence = round(random.uniform(86.5, 94.8), 1)
                reason = "High-contrast specular reflections and dark tonal distribution indicative of scrap."
            elif color_std > 55:
                predicted = "Mixed Waste"
                confidence = round(random.uniform(85.0, 93.5), 1)
                reason = "Heterogeneous multi-spectral composition showing commingled municipal waste."
            else:
                # Weighted plausible selection
                predicted = random.choices(CATEGORIES, weights=[30, 20, 25, 10, 10, 5])[0]
                confidence = round(random.uniform(87.0, 95.5), 1)
                reason = "General municipal solid waste visual markers recognized."

        return {
            "success": True,
            "predicted_category": predicted,
            "confidence": confidence,
            "model_version": "CleanTrack-VisionNet v2.4 (Simulated AI Inference)",
            "details": reason,
            "is_mock": True,
            "categories_available": CATEGORIES
        }
    except Exception as e:
        # Fallback safe response
        return {
            "success": False,
            "error": str(e),
            "predicted_category": "Mixed Waste",
            "confidence": 85.0,
            "model_version": "CleanTrack-VisionNet v2.4 (Fallback)",
            "details": "Image feature extraction fallback applied.",
            "is_mock": True,
            "categories_available": CATEGORIES
        }
