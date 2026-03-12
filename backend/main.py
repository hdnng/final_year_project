from fastapi import FastAPI
from database.database import engine
import models.user as user
from api.router import user_router

user.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router.router)