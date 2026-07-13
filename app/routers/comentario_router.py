from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import ComentarioModel, TareaModel, MiembroEquipoModel, ActividadModel, UsuarioModel
from app.schemas.esquemas import ComentarioCreate, ComentarioResponse
from app.core.security import verificar_token, TokenData

router = APIRouter(prefix="/comentarios", tags=["Módulo de Comentarios"], dependencies=[Depends(verificar_token)])

# POST /comentarios/{idTarea} - Crear comentario en una tarea
@router.post("/{idTarea}", response_model=ComentarioResponse)
def crear_comentario(idTarea: int, datos: ComentarioCreate, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    # Verificar que la tarea existe
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == idTarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    nuevo_comentario = ComentarioModel(
        idTarea=idTarea,
        idUsuario=current_user.idUsuario,
        contenido=datos.contenido
    )
    db.add(nuevo_comentario)
    
    # Registrar actividad
    actividad = ActividadModel(
        idTarea=idTarea,
        idUsuario=current_user.idUsuario,
        accion="añadió un comentario",
        detalle=datos.contenido[:80] + "..." if len(datos.contenido) > 80 else datos.contenido
    )
    db.add(actividad)
    db.commit()
    db.refresh(nuevo_comentario)
    
    # Agregar nombre del usuario al response
    usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == current_user.idUsuario).first()
    response = ComentarioResponse.model_validate(nuevo_comentario)
    response.nombreUsuario = usuario.nombre if usuario else "Desconocido"
    return response

# GET /comentarios/{idTarea} - Listar comentarios de una tarea
@router.get("/{idTarea}", response_model=list[ComentarioResponse])
def listar_comentarios(idTarea: int, db: Session = Depends(get_db)):
    comentarios = db.query(ComentarioModel).filter(
        ComentarioModel.idTarea == idTarea
    ).order_by(ComentarioModel.fechaCreacion.desc()).all()
    
    # Enriquecer con nombres de usuario
    resultado = []
    for c in comentarios:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == c.idUsuario).first()
        resp = ComentarioResponse.model_validate(c)
        resp.nombreUsuario = usuario.nombre if usuario else "Desconocido"
        resultado.append(resp)
    
    return resultado

# DELETE /comentarios/{idComentario} - Eliminar comentario (solo autor o líder)
@router.delete("/{idComentario}")
def eliminar_comentario(idComentario: int, current_user: TokenData = Depends(verificar_token), db: Session = Depends(get_db)):
    comentario = db.query(ComentarioModel).filter(ComentarioModel.idComentario == idComentario).first()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    
    # Verificar permisos: el autor del comentario o el líder del proyecto
    es_autor = comentario.idUsuario == current_user.idUsuario
    
    tarea = db.query(TareaModel).filter(TareaModel.idTarea == comentario.idTarea).first()
    es_lider_proy = False
    if tarea:
        miembro = db.query(MiembroEquipoModel).filter(
            MiembroEquipoModel.idUsuario == current_user.idUsuario,
            MiembroEquipoModel.idProyecto == tarea.idProyecto
        ).first()
        es_lider_proy = miembro and 'Líder' in miembro.rolPermiso
    
    if not es_autor and not es_lider_proy:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este comentario")
    
    db.delete(comentario)
    db.commit()
    return {"mensaje": "Comentario eliminado correctamente"}
