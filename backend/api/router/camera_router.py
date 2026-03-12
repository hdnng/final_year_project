from fastapi import APIRouter
from service.camera_service import start_camera, stop_camera

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/start")
def start():

    start_camera()

    return {"message": "camera started"}


@router.get("/stop")
def stop():

    stop_camera()

    return {"message": "camera stopped"}