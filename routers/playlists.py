#routers/playlists.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

# Importaciones de módulos locales
from ..database import get_db
from ..models import Playlist, Song, UserDB, Like
from ..schemas import PlaylistCreate, PlaylistAddSong, PlaylistOut

# 1. Definición del Router
# Usamos un prefijo simple, ya que los likes son globales y la playlist es específica
router = APIRouter(
    tags=["Playlists y Likes"]
)

@router.post("/playlists", response_model=PlaylistOut)
def create_playlist(p: PlaylistCreate, db: Session = Depends(get_db)):
    user = db.query(UserDB).get(p.user_id)
    if not user: raise HTTPException(404, "Usuario no encontrado")

    pl = Playlist(name=p.name, user_id=p.user_id)
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return pl

@router.post("/playlists/{playlist_id}/add_song")
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

@router.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    pl = db.query(Playlist).get(playlist_id)
    if not pl: raise HTTPException(404, "Playlist no encontrada")
    
    # Formateamos la respuesta manual para evitar problemas de recursión
    songs_data = [{"id": s.id, "title": s.title, "audio": s.audio_path} for s in pl.songs]
    return {"id": pl.id, "name": pl.name, "owner_id": pl.user_id, "songs": songs_data}

# LIKES 
@router.post("/users/{user_id}/like/{item_type}/{item_id}")
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