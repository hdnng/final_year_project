"""
AI inference pipeline — YOLO person detection + CNN behavior classification.
"""

import os
import time
from pathlib import Path

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from ultralytics import YOLO

from core.logger import get_logger

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

logger = get_logger(__name__)

# ── Model paths ─────────────────────────────────────────────
_AI_MODEL_DIR = Path(__file__).resolve().parent
_CNN_PATH = _AI_MODEL_DIR / "weights" / "behavior_model_final.keras"
_YOLO_PATH = _AI_MODEL_DIR / "weights" / "yolov8n.pt"

# ── Load models ─────────────────────────────────────────────
logger.info(f"Loading AI models from: {_AI_MODEL_DIR}")

_cnn_model = load_model(str(_CNN_PATH)) if _CNN_PATH.exists() else None
_yolo_model = YOLO(str(_YOLO_PATH))

if _cnn_model is None:
    logger.warning("CNN model not found — classification will be skipped")

# ── Constants ───────────────────────────────────────────────
LABELS = ["Normal", "Sleeping"]
IMG_SIZE = 224
_YOLO_INPUT_SIZE = (640, 360)
_DETECTION_COOLDOWN = 1.0  # seconds between YOLO runs
_CLASSIFY_EVERY_N = 10     # classify every Nth frame

# ── Cached state ────────────────────────────────────────────
_last_boxes = None
_last_detect_time = 0.0
_last_label = "Normal"


def process_frame(
    frame: np.ndarray,
    frame_count: int,
) -> tuple[np.ndarray, list[dict]]:
    """
    Process a single video frame through the detection + classification pipeline.

    Args:
        frame: BGR image from OpenCV.
        frame_count: Running frame counter (used to throttle classification).

    Returns:
        Tuple of (annotated_frame, list_of_detection_dicts).
        Each detection dict has keys: bbox, label, confidence.
    """
    global _last_boxes, _last_detect_time, _last_label

    results_data: list[dict] = []

    if _cnn_model is None:
        return frame, results_data

    h, w = frame.shape[:2]
    small_frame = cv2.resize(frame, _YOLO_INPUT_SIZE)

    # Run YOLO detection periodically
    if time.time() - _last_detect_time > _DETECTION_COOLDOWN:
        detections = _yolo_model(small_frame, verbose=False)[0]
        _last_boxes = detections.boxes
        _last_detect_time = time.time()

    if _last_boxes is None:
        return frame, results_data

    scale_x = w / _YOLO_INPUT_SIZE[0]
    scale_y = h / _YOLO_INPUT_SIZE[1]

    for box in _last_boxes:
        cls_id = int(box.cls[0].item())
        if cls_id != 0:  # person class only
            continue

        x1, y1, x2, y2 = _scale_bbox(box.xyxy[0], scale_x, scale_y)

        person_crop = frame[max(0, y1):y2, max(0, x1):x2]
        if person_crop.size == 0:
            continue

        label = _last_label
        confidence = 0.0

        # Run CNN classification periodically
        if frame_count % _CLASSIFY_EVERY_N == 0:
            label, confidence = _classify_crop(person_crop)
            _last_label = f"{label} ({confidence * 100:.1f}%)"

        results_data.append({
            "bbox": [x1, y1, x2, y2],
            "label": label,
            "confidence": confidence,
        })

        # Draw annotation
        color = (0, 255, 0) if "Normal" in label else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame, _last_label, (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
        )

    return frame, results_data


def _scale_bbox(
    xyxy,
    scale_x: float,
    scale_y: float,
) -> tuple[int, int, int, int]:
    """Scale bounding box coordinates from YOLO input size to original frame size."""
    x1, y1, x2, y2 = map(int, xyxy)
    return (
        int(x1 * scale_x),
        int(y1 * scale_y),
        int(x2 * scale_x),
        int(y2 * scale_y),
    )


def _classify_crop(crop: np.ndarray) -> tuple[str, float]:
    """Run CNN classification on a person crop. Returns (label, confidence)."""
    try:
        img = cv2.resize(crop, (IMG_SIZE, IMG_SIZE))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img / 255.0, axis=0)

        preds = _cnn_model(img, training=False)
        idx = int(np.argmax(preds[0]))
        confidence = float(preds[0][idx])

        return LABELS[idx], confidence
    except Exception as exc:
        logger.debug(f"Classification failed: {exc}")
        return "Normal", 0.0