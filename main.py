# main.py
import os
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import shutil
import uuid

# ==== CONFIG ====
BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"

MEDIA_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{BASE_DIR / 'music.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI()
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


# ==== DB MODELS ====

class ArtistDB(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)

    albums = relationship("AlbumDB", back_populates="artist")
    songs = relationship("SongDB", back_populates="artist")


class AlbumDB(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))

    artist = relationship("ArtistDB", back_populates="albums")
    songs = relationship("SongDB", back_populates="album")


class SongDB(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    duration = Column(String(20), nullable=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=True)
    audio_path = Column(String(300), nullable=True)  # OPCIONAL

    album = relationship("AlbumDB", back_populates="songs")
    artist = relationship("ArtistDB", back_populates="songs")


class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True)
    password = Column(String(150))     # contraseña sin encriptar
    favorites_json = Column(Text, default="{}")  # guarda dict como texto plano


Base.metadata.create_all(bind=engine)


# ==== Pydantic Schemas ====

class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None


class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None
    artist_id: int


class SongCreate(BaseModel):
    title: str
    duration: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None


class UserCreate(BaseModel):
    username: str
    password: str


class Favorites(BaseModel):
    artists: List[int] = []
    albums: List[int] = []
    songs: List[int] = []


class UserOut(BaseModel):
    id: int
    username: str
    favorites: Favorites


# ==== DB Session ====

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==== UTIL ====

def save_audio(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = AUDIO_DIR / filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"audio/{filename}"


# ==== ENDPOINTS ====

# --- ARTISTS ---
@app.post("/artists")
def create_artist(p: ArtistCreate, db: Session = Depends(get_db)):
    a = ArtistDB(**p.dict())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# --- ALBUMS ---
@app.post("/albums")
def create_album(p: AlbumCreate, db: Session = Depends(get_db)):
    a = AlbumDB(**p.dict())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


# --- SONGS ---
@app.post("/songs")
def create_song(
    title: str = Form(...),
    duration: str = Form(None),
    album_id: int = Form(None),
    artist_id: int = Form(None),
    audio: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    audio_path = None
    if audio:
        audio_path = save_audio(audio)

    s = SongDB(
        title=title,
        duration=duration,
        album_id=album_id,
        artist_id=artist_id,
        audio_path=audio_path
    )

    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# --- USERS ---
import json

@app.post("/users", response_model=UserOut)
def create_user(p: UserCreate, db: Session = Depends(get_db)):
    user = UserDB(
        username=p.username,
        password=p.password,
        favorites_json=json.dumps({"artists": [], "albums": [], "songs": []})
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        favorites=json.loads(user.favorites_json)
    )


@app.post("/users/{user_id}/favorites")
def update_favorites(user_id: int, fav: Favorites, db: Session = Depends(get_db)):
    user = db.query(UserDB).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.favorites_json = json.dumps(fav.dict())
    db.commit()
    return {"detail": "Updated"}


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut(
        id=user.id,
        username=user.username,
        favorites=json.loads(user.favorites_json)
    )

# === GET ARTISTS ===
@app.get("/artists")
def get_artists(db: Session = Depends(get_db)):
    artists = db.query(ArtistDB).all()
    return artists


@app.get("/artists/{artist_id}")
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(ArtistDB).get(artist_id)
    if not artist:
        raise HTTPException(404, "Artist not found")
    return artist


# === GET ALBUMS ===
@app.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    albums = db.query(AlbumDB).all()
    return albums


@app.get("/albums/{album_id}")
def get_album(album_id: int, db: Session = Depends(get_db)):
    album = db.query(AlbumDB).get(album_id)
    if not album:
        raise HTTPException(404, "Album not found")
    return album


# === GET SONGS ===
@app.get("/songs")
def get_songs(db: Session = Depends(get_db)):
    songs = db.query(SongDB).all()
    return songs


@app.get("/songs/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.query(SongDB).get(song_id)
    if not song:
        raise HTTPException(404, "Song not found")
    return song


# === GET TODO JUNTO (para tu app Kotlin) ===
@app.get("/all")
def get_all(db: Session = Depends(get_db)):
    artists = db.query(ArtistDB).all()
    albums = db.query(AlbumDB).all()
    songs = db.query(SongDB).all()

    return {
        "artists": artists,
        "albums": albums,
        "songs": songs
    }


# --- ROOT ---
@app.get("/")
def root():
    return {"ok": True, "docs": "/docs"}
