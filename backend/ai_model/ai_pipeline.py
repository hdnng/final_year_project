import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from pathlib import Path
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# ===== PATH =====
AI_MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = AI_MODEL_DIR / "weights" / "behavior_model_v2.keras"
YOLO_PATH = AI_MODEL_DIR / "weights" / "yolov8n.pt"

print(f"--- Loading AI Models from: {AI_MODEL_DIR} ---")

cnn_model = load_model(str(MODEL_PATH)) if MODEL_PATH.exists() else None
yolo_model = YOLO(str(YOLO_PATH))

# ===== CONFIG =====
LABELS = ["Normal", "Sleeping"]
IMG_SIZE = 224

# ===== CACHE =====
last_box = None
last_detect_time = 0
last_label = "Normal"

def process_frame(frame, frame_count):
    global last_box, last_detect_time, last_label

    results_data = []   # 👈 thêm dòng này

    if cnn_model is None:
        return frame, results_data

    h, w = frame.shape[:2]
    small_frame = cv2.resize(frame, (640, 360))

    if time.time() - last_detect_time > 1:
        results = yolo_model(small_frame, verbose=False)[0]
        last_box = results.boxes
        last_detect_time = time.time()

    boxes = last_box
    if boxes is None:
        return frame, results_data

    scale_x = w / 640
    scale_y = h / 360

    for box in boxes:
        cls_id = int(box.cls[0].item())
        if cls_id != 0:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        x1 = int(x1 * scale_x)
        y1 = int(y1 * scale_y)
        x2 = int(x2 * scale_x)
        y2 = int(y2 * scale_y)

        person_crop = frame[max(0, y1):y2, max(0, x1):x2]
        if person_crop.size == 0:
            continue

        label = last_label
        confidence = 0.0

        if frame_count % 10 == 0:
            try:
                img = cv2.resize(person_crop, (IMG_SIZE, IMG_SIZE))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = np.expand_dims(img / 255.0, axis=0)

                preds = cnn_model(img, training=False)
                idx = np.argmax(preds[0])
                confidence = float(preds[0][idx])

                label = LABELS[idx]
                last_label = f"{label} ({confidence*100:.1f}%)"
            except:
                pass

        # 👇 lưu dữ liệu vào list
        results_data.append({
            "bbox": [x1, y1, x2, y2],
            "label": label,
            "confidence": confidence
        })

        color = (0, 255, 0) if "Normal" in label else (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, last_label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    return frame, results_data