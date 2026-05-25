import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import UsuarioModel
from app.schemas.esquemas import UsuarioCreate, UsuarioResponse, LoginRequest

router = APIRouter(prefix="/usuarios", tags=["Módulo de Usuarios"])

# Función auxiliar para encriptar
def encriptar_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el correo ya existe
    existe = db.query(UsuarioModel).filter(UsuarioModel.correo == usuario.correo).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # 2. Guardar usuario con contraseña encriptada
    nuevo_usuario = UsuarioModel(
        nombre=usuario.nombre,
        correo=usuario.correo,
        contrasena=encriptar_password(usuario.contrasena)
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/login")
def login(credenciales: LoginRequest, db: Session = Depends(get_db)):
    # 1. Buscar al usuario
    usuario = db.query(UsuarioModel).filter(UsuarioModel.correo == credenciales.correo).first()
    
    # 2. Validar correo y contraseña
    if not usuario or usuario.contrasena != encriptar_password(credenciales.contrasena):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        
    return {
        "mensaje": "Login exitoso",
        "usuario": {
            "idUsuario": usuario.idUsuario,
            "nombre": usuario.nombre,
            "correo": usuario.correo
        }
    }
