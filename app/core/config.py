import os


class Settings:
    PROJECT_NAME: str = "Chat Application Backend"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Newjob#613@localhost:5432/chat_app_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()