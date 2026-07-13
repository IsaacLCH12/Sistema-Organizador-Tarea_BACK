import uuid  
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import ProyectoModel, MiembroEquipoModel
from app.schemas.esquemas import ProyectoCreate, ProyectoResponse, UnirseProyecto, MiembroEquipoResponse
from app.core.security import verificar_token, TokenData

router = APIRouter(prefix="/proyectos", tags=["Módulo de Proyectos"], dependencies=[Depends(verificar_token)])

@router.post("/", response_model=ProyectoResponse)
def crear_proyecto(proyecto: ProyectoCreate, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    
    codigo_generado = str(uuid.uuid4())[:8].upper()
    nuevo_proyecto = ProyectoModel(
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion,
        codigoInvitacion=codigo_generado
    )
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)

    # Añadir automáticamente al creador como Líder
    nuevo_miembro = MiembroEquipoModel(
        idUsuario=current_user.idUsuario,
        idProyecto=nuevo_proyecto.idProyecto,
        rolPermiso="Líder / Creador",
        rolFuncional="Scrum Master" # Por defecto
    )
    db.add(nuevo_miembro)
    db.commit()
    
    return nuevo_proyecto

@router.get("/", response_model=list[ProyectoResponse])
def listar_proyectos(current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    # Solo traer los proyectos donde el usuario actual sea miembro
    proyectos = db.query(ProyectoModel).join(
        MiembroEquipoModel, ProyectoModel.idProyecto == MiembroEquipoModel.idProyecto
    ).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario
    ).all()
    return proyectos

@router.post("/unirse")
def unirse_a_proyecto(datos: UnirseProyecto, db: Session = Depends(get_db)):
    # 1. Buscar el proyecto por código
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.codigoInvitacion == datos.codigoInvitacion).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Código de invitación inválido")

    # 2. REGLA: Verificar límite de 6 integrantes
    total_miembros = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idProyecto == proyecto.idProyecto).count()
    if total_miembros >= 6:
        raise HTTPException(status_code=400, detail="El equipo ya está lleno (Máximo 6 integrantes)")

    # 3. Verificar si el usuario ya está en el equipo
    existe_miembro = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idUsuario == datos.idUsuario,
        MiembroEquipoModel.idProyecto == proyecto.idProyecto
    ).first()
    if existe_miembro:
        raise HTTPException(status_code=400, detail="Ya perteneces a este proyecto")

    # 4. Asignar como "Miembro"
    nuevo_miembro = MiembroEquipoModel(
        idUsuario=datos.idUsuario,
        idProyecto=proyecto.idProyecto,
        rolPermiso="Miembro",
        rolFuncional=datos.rolFuncional
    )
    db.add(nuevo_miembro)
    
    # Actualizar estado del proyecto si ya son 3 o más
    if total_miembros + 1 >= 2:
        proyecto.estado = "En desarrollo"
        
    db.commit()
    return {"mensaje": "Te has unido al proyecto exitosamente", "idProyecto": proyecto.idProyecto}

@router.get("/{idProyecto}/miembros", response_model=list[MiembroEquipoResponse])
def listar_miembros_proyecto(idProyecto: int, db: Session = Depends(get_db)):
    miembros = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idProyecto == idProyecto).all()
    return miembros
