import base64

import cv2
import numpy as np
def enhance_shading_contrast(image_base64):
    # 1. Decode the base64 string into raw bytes
    image_bytes = base64.b64decode(image_base64)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # 2. SHADOW REMOVAL: Create a map of the uneven lighting
    # A heavy Gaussian blur erases the text/pencil, leaving only the shadow gradients
    bg = cv2.GaussianBlur(img, (61, 61), 0)
    
    # Divide the original image by the shadow map to flatten the lighting to pure white
    flat_img = cv2.divide(img, bg, scale=255)
    
    # 3. Apply a milder CLAHE to pop the pencil marks safely
    # Lowered clipLimit from 3.0 to 2.0 to prevent noise amplification
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced_img = clahe.apply(flat_img)
    
    # 4. Convert back to base64 string for the LLM
    _, buffer = cv2.imencode('.jpg', enhanced_img)
    return base64.b64encode(buffer).decode('utf-8')

def prepare_solver_payload(interpreted: dict) -> dict:
    return {
        "instructions_en": interpreted.get("instructions_en", []),
        "instructions_ms": interpreted.get("instructions_ms", []),
        "introductory_instructions_ms": interpreted.get("introductory_instructions_ms", ""),
        "topic": interpreted.get("topic", ""),
        "subtopic": interpreted.get("subtopic", ""),
        "diagram_type": interpreted.get("diagram_type", ""),
        "subparts_present": interpreted.get("subparts_present", []),
        "solve_only_subpart": interpreted.get("solve_only_subpart", ""),
        "previous_subpart_answers": interpreted.get("previous_subpart_answers", {}),
        "subpart_classification": interpreted.get("subpart_classification", {}),
        "allocated_marks": interpreted.get("allocated_marks", {}),
        "target": interpreted.get("target", ""),
        "variables": interpreted.get("variables", []),
        "given_values": interpreted.get("given_values", {}),
        "constraints": interpreted.get("constraints", {}),
        "table_data": interpreted.get("table_data", {}),
        "note": (
            "This extracted data is only a rough helper for question understanding "
            "and RAG retrieval. The attached image is the source of truth for solving. "
            "If solve_only_subpart is provided, solve only that subpart."
        )
    }