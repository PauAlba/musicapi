# main.py

# imports
import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
import shutil
import uuid
import json


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

# models
class Artist(Base):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    artist_pic = Column(String(400), nullable = True) #agregado
    albums = relationship("Album", back_populates="artist")
    songs = relationship("Song", back_populates="artist")
    

class Album(Base):
    __tablename__ = "album"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable = False) #agregado
    cover_url = Column(String(300), nullable=True)
    artist_id = Column(Integer, ForeignKey("artist.id"))
    artist = relationship("Artist", back_populates="albums")
    songs = relationship("Song", back_populates="album")

class Song(Base):
    __tablename__ = "song"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    duration = Column(String(20), nullable=True)
    album_id = Column(Integer, ForeignKey("album.id"), nullable=True)
    artist_id = Column(Integer, ForeignKey("artist.id"), nullable=True)
    audio_path = Column(String(300), nullable=True)
    album = relationship("Album", back_populates="songs")
    artist = relationship("Artist", back_populates="songs")

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True)
    password = Column(String(150))
    favorites_json = Column(Text, default="{}")

class Like(Base):
    __tablename__ = "likes"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    item_type = Column(String(50), primary_key=True)  # "artist" | "album" | "song"
    item_id = Column(Integer, primary_key=True)

Base.metadata.create_all(bind=engine)

#  schemas
class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    artist_pic: str #agregado

class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None
    artist_id: int
    cover_url: Optional[str] = None
    category: str #agregado

class SongCreate(BaseModel):
    title: str
    duration: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    password: str

# class Favorites(BaseModel):
#     artists: List[int] = []
#     albums: List[int] = []
#     songs: List[int] = []

class UserOut(BaseModel):
    id: int
    username: str
    #favorites: Favorites

# session 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#  audio
def save_audio(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = AUDIO_DIR / filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"audio/{filename}"

# endpoints artist
@app.post("/artists")
def create_artist(p: ArtistCreate, db: Session = Depends(get_db)):
    a = Artist(**p.dict())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@app.get("/artists")
def get_artists(db: Session = Depends(get_db)):
    return db.query(Artist).all()

@app.get("/artists/{artist_id}")
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    a = db.query(Artist).get(artist_id)
    if not a:
        raise HTTPException(404, "Artist not found")
    return a

# endpoints album
@app.post("/albums")
def create_album(p: AlbumCreate, db: Session = Depends(get_db)):
    a = Album(**p.dict())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@app.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    return db.query(Album).all()

@app.get("/albums/{album_id}")
def get_album(album_id: int, db: Session = Depends(get_db)):
    a = db.query(Album).get(album_id)
    if not a:
        raise HTTPException(404, "Album not found")
    return a

# endpoints song
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

    s = Song(
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

@app.get("/songs")
def get_songs(db: Session = Depends(get_db)):
    return db.query(Song).all()

@app.get("/songs/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    s = db.query(Song).get(song_id)
    if not s:
        raise HTTPException(404, "Song not found")
    return s

# user creation and favorites
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
    return UserOut(id=user.id, username=user.username)#, favorites=json.loads(user.favorites_json))

# @app.post("/users/{user_id}/favorites")
# def update_favorites(user_id: int, fav: Favorites, db: Session = Depends(get_db)):
#     user = db.query(UserDB).get(user_id)
#     if not user:
#         raise HTTPException(404, "User not found")
#     user.favorites_json = json.dumps(fav.dict())
#     db.commit()
#     return {"updated": True}

@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return UserOut(id=user.id, username=user.username) #favorites=json.loads(user.favorites_json))

# get all
@app.get("/all")
def get_all(db: Session = Depends(get_db)):
    return {
        "artists": db.query(Artist).all(),
        "albums": db.query(Album).all(),
        "songs": db.query(Song).all()
    }

# root redirect
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.post("/users/{user_id}/like/{item_type}/{item_id}")
def toggle_like(user_id: int, item_type: str, item_id: int, db: Session = Depends(get_db)):
    if item_type not in ["artist", "album", "song"]:
        raise HTTPException(400, "Invalid item type")

    like = db.query(Like).filter_by(
        user_id=user_id,
        item_type=item_type,
        item_id=item_id
    ).first()

    if like:
        db.delete(like)
        db.commit()
        return {"liked": False}

    new_like = Like(user_id=user_id, item_type=item_type, item_id=item_id)
    db.add(new_like)
    db.commit()
    return {"liked": True}

@app.get("/users/{user_id}/likes")
def get_likes(user_id: int, db: Session = Depends(get_db)):
    likes = db.query(Like).filter_by(user_id=user_id).all()

    result = {"artists": [], "albums": [], "songs": []}

    for l in likes:
        result[l.item_type + "s"].append(l.item_id)

    return result

