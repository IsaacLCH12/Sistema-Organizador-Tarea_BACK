import uuid  
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import ProyectoModel, MiembroEquipoModel, UsuarioModel, TareaModel
from app.schemas.esquemas import ProyectoCreate, ProyectoResponse, UnirseProyecto, MiembroEquipoResponse
from app.core.security import verificar_token, TokenData

router = APIRouter(prefix="/proyectos", tags=["Módulo de Proyectos"], dependencies=[Depends(verificar_token)])

@router.post("/", response_model=ProyectoResponse)
def crear_proyecto(proyecto: ProyectoCreate, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    
    # 1. Verificar si el usuario ya tiene un proyecto con este nombre exacto
    proyecto_duplicado = db.query(ProyectoModel).join(
        MiembroEquipoModel, ProyectoModel.idProyecto == MiembroEquipoModel.idProyecto
    ).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario,
        ProyectoModel.nombre == proyecto.nombre
    ).first()
    
    if proyecto_duplicado:
        raise HTTPException(status_code=400, detail="Ya tienes un proyecto creado con este nombre exacto")

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
        rolFuncional="Gestor de Proyecto" # Por defecto
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
    
    # Actualizar estado del proyecto si ya son 2 o más
    if total_miembros + 1 >= 2:
        proyecto.estado = "En desarrollo"
        
    db.commit()
    return {"mensaje": "Te has unido al proyecto exitosamente", "idProyecto": proyecto.idProyecto}

@router.get("/{idProyecto}/miembros", response_model=list[MiembroEquipoResponse])
def listar_miembros_proyecto(idProyecto: int, db: Session = Depends(get_db)):
    miembros = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idProyecto == idProyecto).all()
    
    # Enriquecer con nombres de usuario
    resultado = []
    for m in miembros:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == m.idUsuario).first()
        resp = MiembroEquipoResponse.model_validate(m)
        resp.nombreUsuario = usuario.nombre if usuario else "Desconocido"
        resultado.append(resp)
    
    return resultado

# DELETE /proyectos/{idProyecto}/miembros/{idMiembroEquipo} - Eliminar miembro (solo líder)
@router.delete("/{idProyecto}/miembros/{idMiembroEquipo}")
def eliminar_miembro(idProyecto: int, idMiembroEquipo: int, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    # Verificar que el usuario actual sea líder del proyecto
    lider = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario,
        MiembroEquipoModel.idProyecto == idProyecto
    ).first()
    
    if not lider or 'Líder' not in lider.rolPermiso:
        raise HTTPException(status_code=403, detail="Solo el líder puede eliminar miembros del proyecto")
    
    # Buscar al miembro a eliminar
    miembro = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idMiembroEquipo == idMiembroEquipo,
        MiembroEquipoModel.idProyecto == idProyecto
    ).first()
    
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado en este proyecto")
    
    # No se puede eliminar al líder
    if 'Líder' in miembro.rolPermiso:
        raise HTTPException(status_code=400, detail="No se puede eliminar al líder del proyecto")
    
    # Desasignar tareas del miembro
    tareas_asignadas = db.query(TareaModel).filter(
        TareaModel.idMiembroEquipo == idMiembroEquipo,
        TareaModel.estado != "Done"
    ).all()
    for t in tareas_asignadas:
        t.idMiembroEquipo = None
        t.estado = "To Do"
    
    db.delete(miembro)
    db.commit()
    return {"mensaje": "Miembro eliminado del proyecto correctamente"}

# DELETE /proyectos/{idProyecto} - Eliminar un proyecto (solo líder)
@router.delete("/{idProyecto}")
def eliminar_proyecto(idProyecto: int, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    proyecto = db.query(ProyectoModel).filter(ProyectoModel.idProyecto == idProyecto).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
    lider = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idUsuario == current_user.idUsuario,
        MiembroEquipoModel.idProyecto == idProyecto
    ).first()
    
    if not lider or 'Líder' not in lider.rolPermiso:
        raise HTTPException(status_code=403, detail="Solo el líder del proyecto puede eliminarlo")
        
    # Eliminar tareas asociadas
    db.query(TareaModel).filter(TareaModel.idProyecto == idProyecto).delete()
    
    # Eliminar miembros asociados
    db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idProyecto == idProyecto).delete()
    
    # Eliminar el proyecto
    db.delete(proyecto)
    db.commit()
    
    return {"mensaje": "Proyecto eliminado correctamente"}

