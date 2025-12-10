# CANCIONES (CON CLOUDINARY) 
# routers/songs.py
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session
from typing import List

# Importaciones de módulos locales
from database import get_db
from models import Song
from schemas import SongCreate # Lo usamos como referencia para los campos
from utils import upload_file_to_cloudinary

# 1. Definición del Router
router = APIRouter(
    prefix="/songs",
    tags=["Canciones"]
)


@router.post("/songs")
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

@router.get("/songs")
def get_songs(db: Session = Depends(get_db)):
    return db.query(Song).all()


@router.get("/{song_id}")
def get_song_by_id(song_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de una canción por su ID.
    """
    song = db.query(Song).get(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    return song