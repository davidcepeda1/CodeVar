import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Render (y Heroku) entregan DATABASE_URL con el esquema legado "postgres://",
# que SQLAlchemy >= 1.4 ya no reconoce (requiere "postgresql://").
DATABASE_URL = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
