# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Importaciones de módulos locales
from ..database import get_db
from ..models import UserDB # Solo el modelo de SQLAlchemy
from ..schemas import UserCreate, UserLogin, UserOut # Schemas de Pydantic
from ..utils import get_password_hash, verify_password

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"]
)



# USUARIOS 
@router.post("/", response_model=UserOut)
def create_user(p: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserDB).filter((UserDB.username == p.username) | (UserDB.email == p.email)).first():
        raise HTTPException(status_code=400, detail="Usuario o correo ya registrado")
    
    # Aquí usamos la función corregida
    hashed_password = get_password_hash(p.password) 
    
    new_user = UserDB(
        username=p.username, 
        email=p.email, 
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    return UserOut.from_orm(user)

@router.get("/", response_model=List[UserOut])
def get_users_all(db: Session = Depends(get_db)):
    """
    Obtiene una lista de todos los usuarios registrados.
    """
    return db.query(UserDB).all()

@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los detalles de un usuario por su ID.
    """
    user = db.query(UserDB).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user