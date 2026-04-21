# Chat Application Backend

A real-time chat backend built with FastAPI, PostgreSQL, SQLAlchemy, JWT authentication, RBAC, and WebSockets.

## Features

- User signup and login
- Password hashing with Passlib
- JWT authentication with expiry
- Role-based access control (admin/user)
- Protected HTTP routes
- Protected WebSocket chat using JWT query token
- Multi-room support
- PostgreSQL persistence
- Cursor-based pagination for message history

## Tech Stack

- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- psycopg2
- passlib
- python-jose
- websockets

## Project Setup

### 1. Clone the repository

git clone <your-github-repo-url>
cd chat_backend_assignment

2. Create and activate virtual environment
Windows
python -m venv venv
venv\Scripts\activate

macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Create PostgreSQL database
Create a database named:
chat_app_db

5. Configure database connection
Update app/core/config.py with your PostgreSQL credentials:
DATABASE_URL = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/chat_app_db"

6. Run the application
uvicorn app.main:app --reload

API Endpoints
Authentication
POST /auth/signup
POST /auth/login
GET /auth/me
GET /auth/admin-only

Rooms
POST /rooms (admin only)
GET /rooms
GET /rooms/{room_id}/messages

WebSocket
ws://127.0.0.1:8000/ws/{room_id}?token=YOUR_JWT_TOKEN

Authentication Flow
signup a user uisng /auth/signup
Login in using /auth/login
Copy the returned JWT token
Use the token in Swagger Authorize for HTTP routes
Use the token as a query parameter for WebSocket connections

Cursor-based Pagination
Message history is fetched using cursor pagination

Example:
GET /rooms/1/messages
GET /rooms/1/messages?cursor=10


ebSocket Behavior

On connection
 validates JWT token
 validates room
 sends recent room history from database

On message
  saves message to PostgreSQL
  broadcasts to all connected clients in the same room

On disconnect
 removes the client connection cleanly

Notes
 -passwords are stored as hashes, never plain text
 -JWT tokens include user role and expiry
 -RBAC is implemented as a reusable dependency
 -For assignment,signup accepts a role field.In a production system,admin creation would normally be restricted.

Testing
you can test HTTP endpoints in:
http://127.0.0.1:8000/docs
you can test WebSocket in the browser console:

const token = "YOUR_TOKEN_HERE";
const ws = new WebSocket(`ws://127.0.0.1:8000/ws/1?token=${token}`);

ws.onmessage = (event) => { console.log(JSON.parse(event.data));};

Assignment Coverage

Group A
Environment and dependencies setup
JWT authentication and RBAC
Protected WebSocket chat

Group B
PostgreSQL persistence and full data modelling
SQLAlchemy relationships
Cursor-based pagination for message history