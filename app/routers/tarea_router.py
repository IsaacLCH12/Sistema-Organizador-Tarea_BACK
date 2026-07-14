from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import TareaModel, MiembroEquipoModel, ActividadModel, UsuarioModel
from app.schemas.esquemas import TareaCreate, TareaResponse, TareaUpdate, ActualizarEstadoTarea
from app.core.security import verificar_token, TokenData

router = APIRouter(prefix="/tareas", tags=["Módulo de Tareas"], dependencies=[Depends(verificar_token)])

# Función helper para registrar actividad
def registrar_actividad(db: Session, idTarea: int, idUsuario: int, accion: str, detalle: str = None):
    actividad = ActividadModel(
        idTarea=idTarea,
        idUsuario=idUsuario,
        accion=accion,
        detalle=detalle
    )
    db.add(actividad)

# Helper para verificar si el usuario es líder del proyecto
def es_lider(db: Session, idUsuario: int, idProyecto: int) -> bool:
    miembro = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idUsuario == idUsuario,
        MiembroEquipoModel.idProyecto == idProyecto
    ).first()
    return miembro and 'Líder' in miembro.rolPermiso

# POST /tareas/ - Crear tarea (cualquier miembro)
@router.post("/", response_model=TareaResponse)
def crear_tarea(tarea: TareaCreate, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):

    nueva_tarea = TareaModel(
        idProyecto=tarea.idProyecto,
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        etiquetaRecomendada=tarea.etiquetaRecomendada,
        prioridad=tarea.prioridad,
        tipoIssue=tarea.tipoIssue,
        fechaLimite=tarea.fechaLimite,
        puntosHistoria=tarea.puntosHistoria,
        idReportero=current_user.idUsuario
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    
    # Registrar actividad
    registrar_actividad(db, nueva_tarea.idTarea, current_user.idUsuario, "creó la tarea", f"'{nueva_tarea.titulo}'")
    db.commit()
    
    return nueva_tarea

# GET /tareas/{idTarea} - Detalle de una tarea
@router.get("/{idTarea}", response_model=TareaResponse)
def obtener_tarea(idTarea: int, db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea

# GET /tareas/proyecto/{idProyecto} - Listar tareas de un proyecto
@router.get("/proyecto/{idProyecto}", response_model=list[TareaResponse])
def listar_tareas_proyecto(idProyecto: int, db: Session = Depends(get_db)):
    tareas = db.query(TareaModel).filter(TareaModel.idProyecto == idProyecto).all()
    return tareas

# PUT /tareas/{idTarea} - Editar tarea (solo líder o asignado)
@router.put("/{idTarea}", response_model=TareaResponse)
def editar_tarea(idTarea: int, datos: TareaUpdate, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Verificar permisos: cualquier miembro del proyecto puede editar (estilo Jira)
    es_miembro = db.query(MiembroEquipoModel).filter(
        MiembroEquipoModel.idProyecto == tarea.idProyecto,
        MiembroEquipoModel.idUsuario == current_user.idUsuario
    ).first()
    
    if not es_miembro:
        raise HTTPException(status_code=403, detail="No tienes permisos para editar esta tarea porque no eres miembro del proyecto")
    
    # Aplicar cambios y registrar actividad para cada campo modificado
    cambios = []
    if datos.titulo is not None and datos.titulo != tarea.titulo:
        cambios.append(f"título de '{tarea.titulo}' a '{datos.titulo}'")
        tarea.titulo = datos.titulo
    if datos.descripcion is not None and datos.descripcion != tarea.descripcion:
        cambios.append("la descripción")
        tarea.descripcion = datos.descripcion
    if datos.etiquetaRecomendada is not None and datos.etiquetaRecomendada != tarea.etiquetaRecomendada:
        cambios.append(f"etiqueta de '{tarea.etiquetaRecomendada}' a '{datos.etiquetaRecomendada}'")
        tarea.etiquetaRecomendada = datos.etiquetaRecomendada
    if datos.prioridad is not None and datos.prioridad != tarea.prioridad:
        cambios.append(f"prioridad de '{tarea.prioridad}' a '{datos.prioridad}'")
        tarea.prioridad = datos.prioridad
    if datos.tipoIssue is not None and datos.tipoIssue != tarea.tipoIssue:
        cambios.append(f"tipo de '{tarea.tipoIssue}' a '{datos.tipoIssue}'")
        tarea.tipoIssue = datos.tipoIssue
    if datos.fechaLimite is not None and datos.fechaLimite != tarea.fechaLimite:
        cambios.append(f"fecha límite a '{datos.fechaLimite}'")
        tarea.fechaLimite = datos.fechaLimite
    if datos.puntosHistoria is not None and datos.puntosHistoria != tarea.puntosHistoria:
        cambios.append(f"puntos de historia a {datos.puntosHistoria}")
        tarea.puntosHistoria = datos.puntosHistoria
    
    if cambios:
        registrar_actividad(db, idTarea, current_user.idUsuario, "editó", ", ".join(cambios))
    
    db.commit()
    db.refresh(tarea)
    return tarea

# DELETE /tareas/{idTarea} - Eliminar tarea (solo líder)
@router.delete("/{idTarea}")
def eliminar_tarea(idTarea: int, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if not es_lider(db, current_user.idUsuario, tarea.idProyecto):
        raise HTTPException(status_code=403, detail="Solo el líder del proyecto puede eliminar tareas")
    
    # Si estaba asignada, decrementar tareasActivas
    if tarea.idMiembroEquipo and tarea.estado != "Done":
        miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == tarea.idMiembroEquipo).first()
        if miembro and miembro.tareasActivas > 0:
            miembro.tareasActivas -= 1
    
    db.delete(tarea)
    db.commit()
    return {"mensaje": "Tarea eliminada correctamente"}

# PATCH /tareas/{idTarea}/asignar - Asignar tarea a un miembro
@router.patch("/{idTarea}/asignar")
def asignar_tarea(idTarea: int, idMiembroEquipo: int, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if tarea.idMiembroEquipo is not None:
        raise HTTPException(status_code=400, detail="Esta tarea ya está asignada a un miembro")

    miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == idMiembroEquipo).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    # REGLA: Máximo 2 tareas activas
    if miembro.tareasActivas >= 2:
        raise HTTPException(status_code=400, detail="Sobrecarga laboral: Ya tienes el máximo de tareas activas (2)")

    tarea.idMiembroEquipo = idMiembroEquipo
    tarea.estado = "In Progress"
    miembro.tareasActivas += 1
    
    # Obtener nombre del miembro para el historial
    usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == miembro.idUsuario).first()
    nombre_asignado = usuario.nombre if usuario else "Desconocido"
    
    registrar_actividad(db, idTarea, current_user.idUsuario, "asignó la tarea", f"a {nombre_asignado}")
    db.commit()
    return {"mensaje": "Tarea asignada correctamente"}

# PATCH /tareas/{idTarea}/estado - Cambiar estado (Kanban drag & drop)
@router.patch("/{idTarea}/estado")
def cambiar_estado_tarea(idTarea: int, datos: ActualizarEstadoTarea, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    estado_anterior = tarea.estado
    nuevo_estado = datos.estado

    # Si se mueve a "Done", decrementar tareasActivas
    if nuevo_estado == "Done" and estado_anterior != "Done" and tarea.idMiembroEquipo:
        miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == tarea.idMiembroEquipo).first()
        if miembro and miembro.tareasActivas > 0:
            miembro.tareasActivas -= 1

    # Si se mueve DESDE "Done" a otra columna, incrementar tareasActivas
    if estado_anterior == "Done" and nuevo_estado != "Done" and tarea.idMiembroEquipo:
        miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == tarea.idMiembroEquipo).first()
        if miembro:
            if miembro.tareasActivas >= 2:
                raise HTTPException(status_code=400, detail="No se puede mover: el miembro ya tiene el máximo de tareas activas (2)")
            miembro.tareasActivas += 1

    tarea.estado = nuevo_estado
    registrar_actividad(db, idTarea, current_user.idUsuario, "cambió estado", f"de '{estado_anterior}' a '{nuevo_estado}'")
    db.commit()
    return {"mensaje": f"Estado actualizado a '{nuevo_estado}'"}
