from pydantic import BaseModel


class RoomCreate(BaseModel):
    name: str
    description: str | None = None