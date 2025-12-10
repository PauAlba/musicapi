# Base.metadata.create_all(bind=engine)
# MODELOS(Tablas)
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine, Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from .database import Base



playlist_songs = Table(
    'playlist_songs', Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id'), primary_key=True),  
    Column('song_id', Integer, ForeignKey('song.id'), primary_key=True)            
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


