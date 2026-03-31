import cv2
import os
import json
from deepface import DeepFace

# Paths for our "Local Database"
REGISTRY_PATH = "data/face_registry"
USER_DB = "data/users.json"

if not os.path.exists(REGISTRY_PATH):
    os.makedirs(REGISTRY_PATH)

def register_user(name, age, habits, frame):
    """Saves a user's face and their dynamic habits."""
    user_id = name.lower().replace(" ", "_")
    img_path = os.path.join(REGISTRY_PATH, f"{user_id}.jpg")
    
    # 1. Save the "Golden Image" for future comparison
    cv2.imwrite(img_path, frame)
    
    # 2. Save user profile and dynamic habits
    user_data = {
        "name": name,
        "age": age,
        "habits": [{"text": h, "done": False} for h in habits],
        "id": user_id
    }
    
    try:
        with open(USER_DB, "r+") as f:
            db = json.load(f)
            db[user_id] = user_data
            f.seek(0); json.dump(db, f); f.truncate()
    except (FileNotFoundError, json.JSONDecodeError):
        with open(USER_DB, "w") as f:
            json.dump({user_id: user_data}, f)
            
    return user_id

def authenticate_face(frame):
    """Compares live frame against all registered faces."""
    if not os.listdir(REGISTRY_PATH):
        return None
    
    try:
        # DeepFace search finds the closest match in our local folder
        results = DeepFace.find(img_path=frame, db_path=REGISTRY_PATH, 
                               model_name="VGG-Face", enforce_detection=False)
        
        if len(results) > 0 and not results[0].empty:
            # Get the filename of the match (e.g., "data/face_registry/ayesha.jpg")
            match_path = results[0]['identity'][0]
            user_id = os.path.basename(match_path).split(".")[0]
            
            with open(USER_DB, "r") as f:
                db = json.load(f)
                return db.get(user_id)
    except Exception as e:
        print(f"Auth Error: {e}")
    return None