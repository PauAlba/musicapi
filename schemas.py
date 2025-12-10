# 3. SCHEMAS (Validación de Datos)
from typing import List, Optional
from pydantic import BaseModel

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
       from_attributes = True

class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    
class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None
    artist_id: int
    # cover_url: Optional[str] = None
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
        from_attributes = True

