# routers/artists.py
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import Artist
from utils import upload_file_to_cloudinary

router = APIRouter(
    prefix="/artists",
    tags=["Artistas"]
)

@router.post("/")
def create_artist(
    name: str = Form(...),
    bio: str = Form(None),
    country: str = Form(None),
    artist_pic_file: UploadFile = File(None), # Ahora recibe el archivo
    db: Session = Depends(get_db)
):
    artist_pic_url = None
    
    # 1. Si se adjuntó una imagen, se sube a Cloudinary
    if artist_pic_file:
        # Usamos la misma función, pero con una carpeta diferente
        artist_pic_url = upload_file_to_cloudinary(artist_pic_file, folder="music_app_artist_pics")
        
        if not artist_pic_url:
            raise HTTPException(500, "Error al subir la imagen del artista a Cloudinary")

    # 2. Guardar en BD con la URL devuelta por Cloudinary
    a = Artist(
        name=name, 
        bio=bio, 
        country=country,
        artist_pic=artist_pic_url # <-- Aquí se guarda el link
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@router.get("/")
def get_artists_all(db: Session = Depends(get_db)):
    return db.query(Artist).all()

@router.get("/{artist_id}")
def get_artist_by_id(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).get(artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    return artist