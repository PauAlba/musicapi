# (MySQL Nube) 
# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
   
    # DATABASE_URL = ""
    pass

CONNECT_ARGS = {
    "ssl": {
        "ssl_mode": "required" 
    }
}
# Crear conexión
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args=CONNECT_ARGS 
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

