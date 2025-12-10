# routers/playlists.py

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session, joinedload 
from typing import Optional, List, Union
from pydantic import BaseModel 


from database import get_db

from models import Playlist, Song, UserDB, Like, Artist, Album 

from schemas import (
    PlaylistCreate, 
    PlaylistAddSong, 
    PlaylistOut,

    SongOut, 
    ArtistOut, 
    AlbumOut
) 

#kotlin
class LikesGrouped(BaseModel):
    songs: List[SongOut] = []
    artists: List[ArtistOut] = []
    albums: List[AlbumOut] = []

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

# VISTA DE PERFIL DE KOTLIN 

@router.get("/users/{user_id}/likes", response_model=LikesGrouped)
def get_user_likes(user_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los elementos (canciones, artistas, álbumes) que un usuario ha dado like, 
    agrupados por tipo. Este endpoint alimenta la ProfileScreen de Kotlin.
    """
    # 1. Verificar si el usuario existe
    user = db.query(UserDB).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Obtener todos los registros de Likes para este usuario
    likes = db.query(Like).filter(Like.user_id == user_id).all()

    # 3. Clasificar los IDs por tipo
    liked_songs_ids = [like.item_id for like in likes if like.item_type == 'song']
    liked_artists_ids = [like.item_id for like in likes if like.item_type == 'artist']
    liked_albums_ids = [like.item_id for like in likes if like.item_type == 'album']

    # 4. Obtener los detalles completos de cada elemento likeado

    # Canciones: Cargamos las canciones y precargamos el artista y el álbum para evitar N+1
    songs_details = db.query(Song).options(
        joinedload(Song.artist), 
        joinedload(Song.album)
    ).filter(Song.id.in_(liked_songs_ids)).all()

    # Artistas:
    artists_details = db.query(Artist).filter(Artist.id.in_(liked_artists_ids)).all()

    # Álbumes:
    albums_details = db.query(Album).filter(Album.id.in_(liked_albums_ids)).all()
    
    # 5. Devolver la respuesta agrupada
    return LikesGrouped(
        songs=songs_details,
        artists=artists_details,
        albums=albums_details
    )