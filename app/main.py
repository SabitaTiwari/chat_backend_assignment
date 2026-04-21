from fastapi import FastAPI

from app.db.session import Base, engine
from app.models.message import Message
from app.models.room import Room
from app.models.user import User
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router

app = FastAPI(title="Chat Application Backend")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/")
def read_root():
    return {"message": "Chat backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}