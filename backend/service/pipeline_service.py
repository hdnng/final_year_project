import cv2
import time

from datetime import datetime
from pathlib import Path
from database.database import SessionLocal
from crud.frame_crud import create_frame
from ai_model.ai_pipeline import process_frame
from crud.statistics_crud import create_statistics
from crud.ai_result_crud import create_ai_result
from service.camera_state import CameraState
from core.logger import get_logger

logger = get_logger(__name__)


def capture_loop():
    """
    Main capture loop - Chạy trong background thread
    Đọc frame từ camera, xử lý AI, và lưu vào database
    """
    state = CameraState()

    try:
        db = SessionLocal()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}", exc_info=True)
        return

    BASE_DIR = Path(__file__).resolve().parents[2]
    IMAGE_DIR = BASE_DIR / "images"

    try:
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Image directory ready: {IMAGE_DIR}")
    except Exception as e:
        logger.error(f"❌ Failed to create image directory: {str(e)}", exc_info=True)
        return

    last_save_time = 0
    frame_count = 0

    logger.info("🎬 Capture loop started")

    try:
        while state.running:
            try:
                ret, frame = state.cap.read()
                if not ret:
                    logger.warning("⚠️ Failed to read frame from camera")
                    continue

                state.frame_count += 1
                frame_count += 1

                # Process frame qua AI model
                processed_frame, results = process_frame(frame, state.frame_count)
                state.latest_frame = processed_frame

                # Save data mỗi 30s
                if time.time() - last_save_time > 30:
                    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                    image_path = IMAGE_DIR / filename

                    try:
                        cv2.imwrite(str(image_path), frame)
                        logger.debug(f"📷 Frame saved: {filename}")
                    except Exception as e:
                        logger.error(f"❌ Failed to save image: {str(e)}", exc_info=True)
                        continue

                    if state.current_session_id:
                        try:
                            # Create frame record
                            frame_obj = create_frame(db, str(image_path), state.current_session_id)

                            # Save AI results
                            if results:
                                for r in results:
                                    create_ai_result(db, r, frame_obj.frame_id)
                                logger.debug(f"💾 Saved {len(results)} AI results")

                            # Calculate & save statistics
                            stats_data = calculate_stats(results)
                            create_statistics(db, stats_data, state.current_session_id)

                            # Single commit - Transaction safety
                            db.commit()
                            logger.info(f"✅ Data saved - Frames: {frame_count}, Detections: {len(results)}")

                        except Exception as e:
                            db.rollback()
                            logger.error(f"❌ Database transaction failed: {str(e)}", exc_info=True)

                    last_save_time = time.time()

                time.sleep(0.03)  # ~30 FPS

            except KeyboardInterrupt:
                logger.info("🛑 Capture loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in capture loop: {str(e)}", exc_info=True)
                continue

    except Exception as e:
        logger.critical(f"💥 Fatal error in capture loop: {str(e)}", exc_info=True)
    finally:
        db.close()
        logger.info("❌ Capture loop stopped")


def calculate_stats(results):
    """
    Tính toán thống kê từ AI detection results
    - Total: số người phát hiện
    - Sleeping: số người ngủ gật
    - Focus rate: tỷ lệ tập trung
    """
    total = len(results)
    sleeping = sum(1 for r in results if "Sleeping" in r["label"])

    focus_rate = 1 - (sleeping / total) if total else 0

    return {
        "total": total,
        "sleeping": sleeping,
        "focus_rate": focus_rate
    }