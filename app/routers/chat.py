from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.message import Message
from app.models.room import Room
from app.models.user import User
from app.schemas.chat import RoomCreate
from app.services.auth import RoleChecker, get_current_user, get_user_from_token
from app.services.websocket_manager import manager

router = APIRouter(tags=["Chat"])


@router.post("/rooms")
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    existing_room = db.query(Room).filter(Room.name == room_data.name).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room name already exists",
        )

    room = Room(
        name=room_data.name,
        description=room_data.description,
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "created_at": room.created_at,
    }


@router.get("/rooms")
def list_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rooms = db.query(Room).order_by(Room.id.asc()).all()

    return [
        {
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "created_at": room.created_at,
        }
        for room in rooms
    ]


@router.get("/rooms/{room_id}/messages")
def get_room_messages(
    room_id: int,
    cursor: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found",
        )

    query = (
        db.query(Message)
        .options(joinedload(Message.user))
        .filter(Message.room_id == room_id)
    )

    if cursor is not None:
        query = query.filter(Message.id < cursor)

    messages = query.order_by(Message.id.desc()).limit(limit + 1).all()

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    next_cursor = messages[-1].id if has_more and messages else None

    messages.reverse()

    return {
        "room_id": room.id,
        "room_name": room.name,
        "next_cursor": next_cursor,
        "messages": [
            {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp,
                "user_id": message.user_id,
                "username": message.user.username,
                "room_id": message.room_id,
            }
            for message in messages
        ],
    }


@router.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: int,
    db: Session = Depends(get_db),
):
    token = websocket.query_params.get("token")
    cursor_param = websocket.query_params.get("cursor")
    limit_param = websocket.query_params.get("limit", "20")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        current_user = get_user_from_token(token, db)
    except HTTPException:
        await websocket.close(code=1008)
        return

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        await websocket.close(code=1008)
        return

    try:
        limit = int(limit_param)
    except ValueError:
        limit = 20

    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    cursor = None
    if cursor_param:
        try:
            cursor = int(cursor_param)
        except ValueError:
            cursor = None

    history_query = (
        db.query(Message)
        .options(joinedload(Message.user))
        .filter(Message.room_id == room_id)
    )

    if cursor is not None:
        history_query = history_query.filter(Message.id < cursor)

    history_messages = history_query.order_by(Message.id.desc()).limit(limit + 1).all()

    has_more = len(history_messages) > limit
    if has_more:
        history_messages = history_messages[:limit]

    next_cursor = history_messages[-1].id if has_more and history_messages else None

    history_messages.reverse()

    await manager.connect(room_id, websocket)

    await websocket.send_json(
        {
            "type": "history",
            "room_id": room.id,
            "room_name": room.name,
            "next_cursor": next_cursor,
            "messages": [
                {
                    "id": message.id,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "user_id": message.user_id,
                    "username": message.user.username,
                    "room_id": message.room_id,
                }
                for message in history_messages
            ],
        }
    )

    try:
        while True:
            text = await websocket.receive_text()
            content = text.strip()

            if not content:
                continue

            new_message = Message(
                content=content,
                user_id=current_user.id,
                room_id=room_id,
            )

            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            payload = {
                "type": "new_message",
                "message": {
                    "id": new_message.id,
                    "content": new_message.content,
                    "timestamp": new_message.timestamp.isoformat(),
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "room_id": room_id,
                },
            }

            await manager.broadcast(room_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
    except Exception:
        manager.disconnect(room_id, websocket)
        await websocket.close()