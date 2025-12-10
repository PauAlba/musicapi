# main.py
import os
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
import cloudinary # Necesario si la configuración se hace aquí, pero lo movemos a utils.py

# Importaciones de módulos locales
from .database import Base, engine 
from .routers import users, artists, albums, songs, playlists 

from . import utils 


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Música API - Modularizada", 
    description="Backend para App de Streaming Musical con FastAPI y Cloudinary."
)

# Conectar todos los Routers
app.include_router(users.router)
app.include_router(artists.router)
app.include_router(albums.router)
app.include_router(songs.router)
app.include_router(playlists.router)

@app.get("/")
def root():
    return RedirectResponse(url="/docs")