# 3. SCHEMAS (Validación de Datos)
from typing import List, Optional
from pydantic import BaseModel


# (Input/Create)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ArtistCreate(BaseModel):
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    
class AlbumCreate(BaseModel):
    title: str
    description: Optional[str] = None
    artist_id: int
    category: str

class SongCreate(BaseModel): 
    title: str
    duration: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None

class PlaylistCreate(BaseModel):
    name: str
    user_id: int

class PlaylistAddSong(BaseModel):
    song_id: int


# Output/Response

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    class Config:
        from_attributes = True

class PlaylistOut(BaseModel):
    id: int
    name: str
    # Nota: Aquí no incluí la lista de canciones en el esquema principal, 
    # ya que endpoint GET la maneja manualmente como List[dict]. 
    class Config:
        from_attributes = True
        
#ENDPOINT DE LIKES 

class ArtistOut(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    country: Optional[str] = None
    artist_pic: Optional[str] = None # URL de la imagen

    class Config:
        from_attributes = True

class AlbumOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    cover_url: Optional[str] = None # URL de la portada
    artist_id: int

    class Config:
        from_attributes = True

class SongOut(BaseModel):
    id: int
    title: str
    duration: Optional[str] = None
    album_id: Optional[int] = None
    artist_id: Optional[int] = None
    audio_path: Optional[str] = None 
    
    # Si quieres precargar el nombre del artista en el DTO de canción, 
    # necesitarías definir la relación aquí. Por simplicidad, usamos los IDs.

    class Config:
        from_attributes = True

# PARA KOTLIN 

class LikesGrouped(BaseModel):
    """Estructura de respuesta para la vista de perfil de Kotlin."""
    songs: List[SongOut] = []
    artists: List[ArtistOut] = []
    albums: List[AlbumOut] = []
    
    class Config:
        from_attributes = True