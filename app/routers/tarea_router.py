from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import TareaModel, MiembroEquipoModel
from app.schemas.esquemas import TareaCreate, TareaResponse
from app.schemas.esquemas import ActualizarEstadoTarea

router = APIRouter(prefix="/tareas", tags=["Módulo de Tareas"])

@router.post("/", response_model=TareaResponse)
def crear_tarea(tarea: TareaCreate, db: Session = Depends(get_db)):
    nueva_tarea = TareaModel(
        idProyecto=tarea.idProyecto,
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        etiquetaRecomendada=tarea.etiquetaRecomendada
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea

@router.put("/asignar/{idTarea}")
def asignar_tarea(idTarea: int, idMiembroEquipo: int, db: Session = Depends(get_db)):
    miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == idMiembroEquipo).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")

    if miembro.tareasActivas >= 2:
        raise HTTPException(
            status_code=400, 
            detail="Sobrecarga laboral: El estudiante ya tiene 2 tareas activas."
        )

    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea.idMiembroEquipo = idMiembroEquipo
    tarea.estado = "In Progress"
    miembro.tareasActivas += 1
    
    db.commit()
    return {"mensaje": f"Tarea asignada. Tareas activas del miembro: {miembro.tareasActivas}"}

@router.put("/{idTarea}/estado")
def mover_tarea_kanban(idTarea: int, datos: ActualizarEstadoTarea, db: Session = Depends(get_db)):
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Si la tarea pasa a "Done" (Finalizada), liberamos la carga del estudiante
    if datos.estado == "Done" and tarea.estado != "Done":
        if tarea.idMiembroEquipo:
            miembro = db.query(MiembroEquipoModel).filter(MiembroEquipoModel.idMiembroEquipo == tarea.idMiembroEquipo).first()
            if miembro and miembro.tareasActivas > 0:
                miembro.tareasActivas -= 1
                
    tarea.estado = datos.estado
    db.commit()
    
    return {"mensaje": f"Tarea movida a la columna: {datos.estado}"}


