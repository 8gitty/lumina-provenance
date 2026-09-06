import os
import cv2
from deepface import DeepFace

def get_face_embedding(image_path: str):
    """
    Detects a face in the given image and generates a facial embedding.
    Returns the embedding (list of floats) and metadata.
    """
    try:
        results = DeepFace.represent(img_path=image_path, model_name="VGG-Face", enforce_detection=True)
        if len(results) > 0:
            face_data = results[0]
            embedding = face_data['embedding']
            facial_area = face_data['facial_area']
            return {
                "success": True,
                "embedding": embedding,
                "facial_area": facial_area,
                "message": "Face detected and embedding generated successfully."
            }
        else:
            return {
                "success": False,
                "message": "No faces found in the image."
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
