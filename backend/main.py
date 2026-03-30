from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from database.database import engine
import models

from api.router import user_router
from api.router import camera_router
from api.router import statistics_router
from api.router import history_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # cho phép tất cả frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router)
app.include_router(camera_router.router)
app.include_router(statistics_router.router)
app.include_router(history_router.router)