# utils.py
import os
import cloudinary
import cloudinary.uploader
from passlib.context import CryptContext
from fastapi import UploadFile


#4. FUNCIONES DE UTILIDAD

# CLOUDINARY 


cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Crea el hash de la contraseña (truncando a 72 caracteres)."""
    return pwd_context.hash(password[:72])

# CORREGIDO: Esta función debe VERIFICAR
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contraseña."""
    # Truncamos la contraseña plana AQUI para que coincida con el hash
    safe_password = plain_password[:72] 
    return pwd_context.verify(safe_password, hashed_password)

def upload_file_to_cloudinary(file: UploadFile, folder: str = "music_app") -> str:
    """Sube archivo a Cloudinary y devuelve la URL"""
    try:
        # resource_type="auto" detecta si es audio, video o imagen
        result = cloudinary.uploader.upload(file.file, resource_type="auto", folder=folder)
        return result.get("secure_url")
    except Exception as e:
        print(f"Error subiendo a Cloudinary: {e}")
        return None
