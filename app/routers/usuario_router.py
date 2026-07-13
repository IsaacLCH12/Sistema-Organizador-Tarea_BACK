import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import UsuarioModel, TareaModel, MiembroEquipoModel, ProyectoModel
from app.schemas.esquemas import UsuarioCreate, UsuarioResponse, LoginRequest, PerfilResponse, ActualizarPerfil, TareaResponse
from app.core.security import crear_access_token, verificar_token, TokenData

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
        
    # 3. Generar token JWT
    access_token = crear_access_token(
        data={"idUsuario": usuario.idUsuario, "correo": usuario.correo}
    )
    
    return {
        "mensaje": "Login exitoso",
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "idUsuario": usuario.idUsuario,
            "nombre": usuario.nombre,
            "correo": usuario.correo
        }
    }

# GET /usuarios/perfil - Obtener perfil del usuario autenticado con estadísticas
@router.get("/perfil", response_model=PerfilResponse)
def obtener_perfil(current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == current_user.idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener IDs de miembros del usuario
    miembros_ids = db.query(MiembroEquipoModel.idMiembroEquipo).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario
    ).all()
    ids = [m[0] for m in miembros_ids]
    
    # Estadísticas de tareas
    tareas_completadas = 0
    tareas_en_progreso = 0
    tareas_pendientes = 0
    
    if ids:
        tareas_completadas = db.query(TareaModel).filter(
            TareaModel.idMiembroEquipo.in_(ids),
            TareaModel.estado == "Done"
        ).count()
        tareas_en_progreso = db.query(TareaModel).filter(
            TareaModel.idMiembroEquipo.in_(ids),
            TareaModel.estado.in_(["In Progress", "In Review"])
        ).count()
        tareas_pendientes = db.query(TareaModel).filter(
            TareaModel.idMiembroEquipo.in_(ids),
            TareaModel.estado == "To Do"
        ).count()
    
    # Total de proyectos
    total_proyectos = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario
    ).count()
    
    return PerfilResponse(
        idUsuario=usuario.idUsuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        tareasCompletadas=tareas_completadas,
        tareasEnProgreso=tareas_en_progreso,
        tareasPendientes=tareas_pendientes,
        totalProyectos=total_proyectos
    )

# PUT /usuarios/perfil - Actualizar perfil
@router.put("/perfil")
def actualizar_perfil(datos: ActualizarPerfil, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == current_user.idUsuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if datos.nombre:
        usuario.nombre = datos.nombre
    if datos.correo:
        # Verificar que el nuevo correo no esté tomado por otro usuario
        existe = db.query(UsuarioModel).filter(UsuarioModel.correo == datos.correo, UsuarioModel.idUsuario != usuario.idUsuario).first()
        if existe:
            raise HTTPException(status_code=400, detail="Este correo ya está en uso por otra cuenta")
        usuario.correo = datos.correo
    if datos.contrasena:
        usuario.contrasena = encriptar_password(datos.contrasena)
    
    db.commit()
    return {"mensaje": "Perfil actualizado correctamente"}

# GET /usuarios/mis-tareas - Listar todas las tareas del usuario
@router.get("/mis-tareas", response_model=list[TareaResponse])
def mis_tareas(current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    miembros_ids = db.query(MiembroEquipoModel.idMiembroEquipo).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario
    ).all()
    ids = [m[0] for m in miembros_ids]
    
    if not ids:
        return []
    
    tareas = db.query(TareaModel).filter(
        TareaModel.idMiembroEquipo.in_(ids)
    ).order_by(TareaModel.fechaCreacion.desc()).all()
    
    return tareas
