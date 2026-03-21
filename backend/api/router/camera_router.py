from fastapi import APIRouter
from service.camera_service import gen_frames, start_camera, stop_camera
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame")

@router.post("/start")
def start():

    start_camera()

    return {"message": "camera started"}


@router.post("/stop")
def stop():

    stop_camera()

    return {"message": "camera stopped"}