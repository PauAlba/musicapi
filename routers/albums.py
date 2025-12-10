# routers/albums.py
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

# Importaciones de módulos locales
from database import get_db
from models import Album
from schemas import AlbumCreate # Lo usamos como referencia para los campos
from utils import upload_file_to_cloudinary

# 1. Definición del Router
router = APIRouter(
    prefix="/albums",
    tags=["Álbumes"]
)

@router.post("/albums")

def create_album(
    title: str = Form(...),
    description: str = Form(None),
    artist_id: int = Form(...),
    category: str = Form(...),
    cover_file: UploadFile = File(None), # Ahora recibe el archivo de portada
    db: Session = Depends(get_db)
):
    cover_url = None
    
    # 1. Si se adjuntó un archivo, subirlo a Cloudinary
    if cover_file:
        # Reutilizamos la función de utilidad
        cover_url = upload_file_to_cloudinary(cover_file, folder="music_app_album_covers")
        
        if not cover_url:
            raise HTTPException(500, "Error al subir la portada del álbum a Cloudinary")

    # 2. Guardar en BD con la URL generada
    a = Album(
        title=title, 
        description=description, 
        artist_id=artist_id,
        category=category,
        cover_url=cover_url # <-- Aquí se guarda el link
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@router.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    return db.query(Album).all()

@router.get("/{album_id}")
def get_album_by_id(album_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un álbum por su ID.
    """
    album = db.query(Album).get(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Álbum no encontrado")
    return album