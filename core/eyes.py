import cv2
from deepface import DeepFace
import time

def get_snapshot_emotion():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "neutral", {"neutral": 100}

    start_time = time.time()
    ret = False
    frame = None
    
    # Warm up for max 1.5 seconds to find a clear frame
    while time.time() - start_time < 1.5:
        success, temp_frame = cap.read()
        if success:
            ret = True
            frame = temp_frame
            break
    
    cap.release() 
    cv2.destroyAllWindows()

    if not ret or frame is None:
        return "neutral", {"neutral": 100}

    try:
        # 🚀 detector_backend='opencv' is the fastest for demos
        # 🚀 silent=True prevents terminal spamming
        results = DeepFace.analyze(
            frame, 
            actions=['emotion'], 
            enforce_detection=False,
            detector_backend='opencv',
            silent=True
        )
        return results[0]['dominant_emotion'], results[0]['emotion']
    except:
        return "neutral", {"neutral": 100}