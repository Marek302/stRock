"""

Initialisation de gestion et la BD

"""

import os
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session

# Import models so SQLModel registers them for create_all
from app.models import listing_entity, listing_view_entity  # noqa: F401


DATABASE_URL = os.getenv("DATABASE_URL")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

CONNECTION_STR = os.getenv("CONNECTION_STR")
if not CONNECTION_STR:
    CONNECTION_STR = f"postgresql+psycopg2://{USER}:{PASSWORD}@{DATABASE_URL}/{DB_NAME}"
elif CONNECTION_STR.startswith("postgresql://"):
    CONNECTION_STR = CONNECTION_STR.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(CONNECTION_STR, echo=True)

def init_db():
    """Initilisation"""
    SQLModel.metadata.create_all(engine)

def shutdown():
    """Fermuture"""
    print("Shutting down the database engine...")
    engine.dispose()

def get_session() -> Generator[Session, None, None]:
    """Récupération d'une session"""
    with Session(engine) as session:
        yield session