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

# routers/artists.py

# ... (tus imports)

# Importamos Form para manejar campos de texto/link
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
# ... (resto de imports)

router = APIRouter(
    prefix="/artists",
    tags=["Artistas"]
)

@router.post("/")
def create_artist(
    name: str = Form(...),
    bio: str = Form(None),
    country: str = Form(None),
    artist_pic_file: UploadFile = File(None), # Opción 1
    artist_pic_link: str = Form(None),       # Opción 2
    db: Session = Depends(get_db)
):
    """
    Crea un nuevo artista. Acepta una imagen subida o un link URL.
    """
    final_pic_url = None
    
   
    if artist_pic_file and artist_pic_file.filename:
        
        # Subir el archivo binario a Cloudinary
        final_pic_url = upload_file_to_cloudinary(artist_pic_file, folder="music_app_artist_pics")
        
        if not final_pic_url:
            raise HTTPException(500, "Error al subir la imagen a Cloudinary")
            
    elif artist_pic_link:
        
        final_pic_url = artist_pic_link
        
    # 3. Guardar en BD
    a = Artist(
        name=name, 
        bio=bio, 
        country=country,
        
        artist_pic=final_pic_url 
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