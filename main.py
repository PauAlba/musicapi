import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine, Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader



# CLOUDINARY 

cloudinary.config( 
  cloud_name = os.getenv("dbycdkgpm"), 
  api_key = os.getenv("932942664653819"), 
  api_secret = os.getenv("**********"),
  secure = True
)

# (MySQL Nube) 

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
   
    # DATABASE_URL = ""
    pass

# Crear conexión
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Seguridad para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


# MODELOS(Tablas)



playlist_songs = Table(
    'playlist_songs', Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id')),
    Column('song_id', Integer, ForeignKey('song.id'))
)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255))
    
    playlists = relationship("Playlist", back_populates="owner")

class Artist(Base):
    __tablename__ = "artist"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    artist_pic = Column(String(400), nullable=True)
    
    albums = relationship("Album", back_populates="artist")
    songs = relationship("Song", back_populates="artist")

class Album(Base):
    __tablename__ = "album"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    cover_url = Column(String(300), nullable=True)
    artist_id = Column(Integer, ForeignKey("artist.id"))
    
    artist = relationship("Artist", back_populates="albums")
    songs = relationship("Song", back_populates="album")

class Song(Base):
    __tablename__ = "song"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    duration = Column(String(20), nullable=True)
    album_id = Column(Integer, ForeignKey("album.id"), nullable=True)
    artist_id = Column(Integer, ForeignKey("artist.id"), nullable=True)
    audio_path = Column(String(500), nullable=True) # URL de Cloudinary
    
    album = relationship("Album", back_populates="songs")
    artist = relationship("Artist", back_populates="songs")
    playlists = relationship("Playlist", secondary=playlist_songs, back_populates="songs")

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("UserDB", back_populates="playlists")
    songs = relationship("Song", secondary=playlist_songs, back_populates="playlists")

class Like(Base):
    __tablename__ = "likes"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    item_type = Column(String(50), primary_key=True) # "artist", "album", "song"
    item_id = Column(Integer, primary_key=True)

# Crea las tablas si no existen
Base.metadata.create_all(bind=engine)


# 3. SCHEMAS (Validación de Datos)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        orm_mode = True

class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    artist_pic: str

class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None
    artist_id: int
    cover_url: Optional[str] = None
    category: str

class SongCreate(BaseModel): # Solo datos, el archivo va aparte
    title: str
    duration: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None

class PlaylistCreate(BaseModel):
    name: str
    user_id: int

class PlaylistAddSong(BaseModel):
    song_id: int

class PlaylistOut(BaseModel):
    id: int
    name: str
    songs: List[dict] = [] # Simplificado
    class Config:
        orm_mode = True


# 4. FUNCIONES DE UTILIDAD


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def upload_file_to_cloudinary(file: UploadFile, folder: str = "music_app") -> str:
    """Sube archivo a Cloudinary y devuelve la URL"""
    try:
        # resource_type="auto" detecta si es audio, video o imagen
        result = cloudinary.uploader.upload(file.file, resource_type="auto", folder=folder)
        return result.get("secure_url")
    except Exception as e:
        print(f"Error subiendo a Cloudinary: {e}")
        return None


# 5. ENDPOINTS


@app.get("/")
def root():
    return RedirectResponse(url="/docs")

# USUARIOS 
@app.post("/users", response_model=UserOut)
def create_user(p: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter((UserDB.username == p.username) | (UserDB.email == p.email)).first():
        raise HTTPException(status_code=400, detail="Usuario o correo ya registrado")
    
    new_user = UserDB(
        username=p.username, 
        email=p.email, 
        hashed_password=get_password_hash(p.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    return UserOut.from_orm(user)

# ARTISTAS 
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

# ALBUMS 
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

# CANCIONES (CON CLOUDINARY) 
@app.post("/songs")
def create_song(
    title: str = Form(...),
    duration: str = Form(None),
    album_id: int = Form(None),
    artist_id: int = Form(None),
    audio: UploadFile = File(...), # Archivo obligatorio
    db: Session = Depends(get_db)
):
    # 1. Subir a Cloudinary
    url_audio = upload_file_to_cloudinary(audio, folder="music_app_songs")
    
    if not url_audio:
        raise HTTPException(500, "Error al subir el archivo de audio")

    # 2. Guardar en BD con la URL
    s = Song(
        title=title, 
        duration=duration, 
        album_id=album_id,
        artist_id=artist_id, 
        audio_path=url_audio
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.get("/songs")
def get_songs(db: Session = Depends(get_db)):
    return db.query(Song).all()

# PLAYLISTS 
@app.post("/playlists", response_model=PlaylistOut)
def create_playlist(p: PlaylistCreate, db: Session = Depends(get_db)):
    user = db.query(UserDB).get(p.user_id)
    if not user: raise HTTPException(404, "Usuario no encontrado")

    pl = Playlist(name=p.name, user_id=p.user_id)
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return pl

@app.post("/playlists/{playlist_id}/add_song")
def add_song_to_playlist(playlist_id: int, p: PlaylistAddSong, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).get(playlist_id)
    song = db.query(Song).get(p.song_id)
    
    if not playlist or not song:
        raise HTTPException(404, "Playlist o canción no encontrada")
        
    if song in playlist.songs:
        return {"message": "La canción ya estaba en la playlist"}

    playlist.songs.append(song)
    db.commit()
    return {"message": "Canción agregada correctamente"}

@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    pl = db.query(Playlist).get(playlist_id)
    if not pl: raise HTTPException(404, "Playlist no encontrada")
    
    # Formateamos la respuesta manual para evitar problemas de recursión
    songs_data = [{"id": s.id, "title": s.title, "audio": s.audio_path} for s in pl.songs]
    return {"id": pl.id, "name": pl.name, "owner_id": pl.user_id, "songs": songs_data}

# LIKES 
@app.post("/users/{user_id}/like/{item_type}/{item_id}")
def toggle_like(user_id: int, item_type: str, item_id: int, db: Session = Depends(get_db)):
    if item_type not in ["artist", "album", "song"]:
        raise HTTPException(400, "Tipo inválido")

    like = db.query(Like).filter_by(user_id=user_id, item_type=item_type, item_id=item_id).first()

    if like:
        db.delete(like)
        db.commit()
        return {"liked": False}

    new_like = Like(user_id=user_id, item_type=item_type, item_id=item_id)
    db.add(new_like)
    db.commit()
    return {"liked": True}

@app.get("/all")
def get_all_data(db: Session = Depends(get_db)):
    return {
        "artists": db.query(Artist).all(),
        "albums": db.query(Album).all(),
        "songs": db.query(Song).all()
    }