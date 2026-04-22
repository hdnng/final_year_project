"""
Capture pipeline — background loop that reads frames, runs AI, and persists results.
"""

import time
from datetime import datetime
from pathlib import Path

import cv2

from core.config import settings
from core.logger import get_logger
from crud.ai_result_crud import create_ai_result
from crud.frame_crud import create_frame
from crud.statistics_crud import create_statistics
from database.database import SessionLocal
from ai_model.ai_pipeline import process_frame
from service.camera_state import CameraState

logger = get_logger(__name__)

SAVE_INTERVAL_SECONDS = 30


def capture_loop() -> None:
    """
    Main capture loop — runs in a background thread.

    Reads frames from the camera, processes them through the AI model,
    and persists frames + results + statistics to the database every
    SAVE_INTERVAL_SECONDS.
    """
    state = CameraState()

    try:
        db = SessionLocal()
        logger.info("Database connection established for capture loop")
    except Exception as exc:
        logger.error(f"Database connection failed: {exc}", exc_info=True)
        return

    image_dir = settings.IMAGE_DIR
    try:
        image_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error(f"Failed to create image directory: {exc}", exc_info=True)
        return

    last_save_time = 0.0
    frame_count = 0

    logger.info("Capture loop started")

    try:
        while state.running:
            try:
                ret, frame = state.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue

                state.frame_count += 1
                frame_count += 1

                # Run AI inference
                processed_frame, results = process_frame(frame, state.frame_count)
                state.latest_frame = processed_frame

                # Persist data at fixed intervals
                if time.time() - last_save_time > SAVE_INTERVAL_SECONDS:
                    _save_snapshot(db, state, frame, results, image_dir, frame_count)
                    last_save_time = time.time()

                time.sleep(0.05)  # ~20 FPS ceiling (camera set to 15 FPS)

            except KeyboardInterrupt:
                logger.info("Capture loop interrupted by user")
                break
            except Exception as exc:
                logger.error(f"Error in capture loop: {exc}", exc_info=True)
                continue

    except Exception as exc:
        logger.critical(f"Fatal error in capture loop: {exc}", exc_info=True)
    finally:
        db.close()
        logger.info("Capture loop stopped")


def _save_snapshot(
    db,
    state: CameraState,
    frame,
    results: list[dict],
    image_dir: Path,
    frame_count: int,
) -> None:
    """Save a single snapshot (frame image + AI results + statistics) to DB."""
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    image_path = image_dir / filename

    try:
        cv2.imwrite(str(image_path), frame)
    except Exception as exc:
        logger.error(f"Failed to save image: {exc}", exc_info=True)
        return

    if not state.current_session_id:
        return

    try:
        frame_obj = create_frame(db, str(image_path), state.current_session_id)

        for r in results:
            create_ai_result(db, r, frame_obj.frame_id)

        stats_data = calculate_stats(results)
        create_statistics(db, stats_data, state.current_session_id)

        db.commit()
        logger.info(f"Snapshot saved — frames: {frame_count}, detections: {len(results)}")

    except Exception as exc:
        db.rollback()
        logger.error(f"Database transaction failed: {exc}", exc_info=True)


def calculate_stats(results: list[dict]) -> dict:
    """
    Compute aggregate statistics from AI detection results.

    Returns dict with keys: total, sleeping, focus_rate.
    """
    total = len(results)
    sleeping = sum(1 for r in results if "Sleeping" in r.get("label", ""))
    focus_rate = 1 - (sleeping / total) if total else 0.0

    return {"total": total, "sleeping": sleeping, "focus_rate": focus_rate}