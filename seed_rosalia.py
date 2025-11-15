# seed_rosalia.py
from main import SessionLocal, ArtistDB, AlbumDB, SongDB, UserDB
import json

db = SessionLocal()

# ====== ARTISTA ======
rosalia = ArtistDB(
    name="Rosalía",
    bio="Cantante española, autora del álbum LUX.",
    country="España"
)
db.add(rosalia)
db.commit()
db.refresh(rosalia)

# ====== ALBUM LUX ======
lux = AlbumDB(
    title="LUX",
    description="Álbum 2024 de Rosalía",
    artist_id=rosalia.id
)
db.add(lux)
db.commit()
db.refresh(lux)

# ====== TODAS LAS CANCIONES ======
songs_data = [
    ("Sexo, violencia y llantas", "2:20"),
    ("Reliquia", "3:49"),
    ("Divinize", "4:03"),
    ("Porcelana", "4:07"),
    ("Mio Cristo Piange Diamanti", "4:29"),

    ("Berghain", "2:58"),
    ("La perla", "3:15"),
    ("Mundo nuevo", "2:20"),
    ("De madrugá", "1:44"),

    ("Dios es un stalker", "2:10"),
    ("La yugular", "4:18"),
    ("Focu 'ranni", "2:50"),
    ("Sauvignon blanc", "2:42"),
    ("Jeanne", "3:51"),

    ("Novia robot", "3:12"),
    ("La rumba del perdón", "4:11"),
    ("Memória", "3:45"),
    ("Magnolias", "3:14"),
]

for title, duration in songs_data:

    # Una canción con audio opcional de ejemplo
    audio_example = "audio/example.mp3" if title == "Porcelana" else None

    s = SongDB(
        title=title,
        duration=duration,
        album_id=lux.id,
        artist_id=rosalia.id,
        audio_path=audio_example
    )
    db.add(s)

db.commit()



# ====== USUARIOS ======
usernames = [
    "musikita_uwu",
    "juanpismata11",
    "PanteraRosaFrix",
    "xav",
    "EdgarPro"
]

for name in usernames:
    u = UserDB(
        username=name,
        password="123456",  # contraseña simple
        favorites_json=json.dumps({"artists": [], "albums": [], "songs": []})
    )
    db.add(u)

db.commit()

print("Seed completado: Rosalía + LUX + canciones + usuarios")
