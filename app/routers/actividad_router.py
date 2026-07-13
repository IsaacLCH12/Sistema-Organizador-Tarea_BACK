from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.modelo_bd import ActividadModel, UsuarioModel
from app.schemas.esquemas import ActividadResponse
from app.core.security import verificar_token

router = APIRouter(prefix="/actividades", tags=["Módulo de Actividades"], dependencies=[Depends(verificar_token)])

# GET /actividades/{idTarea} - Listar historial de actividad de una tarea
@router.get("/{idTarea}", response_model=list[ActividadResponse])
def listar_actividades(idTarea: int, db: Session = Depends(get_db)):
    actividades = db.query(ActividadModel).filter(
        ActividadModel.idTarea == idTarea
    ).order_by(ActividadModel.fechaCreacion.desc()).all()
    
    # Enriquecer con nombres de usuario
    resultado = []
    for a in actividades:
        usuario = db.query(UsuarioModel).filter(UsuarioModel.idUsuario == a.idUsuario).first()
        resp = ActividadResponse.model_validate(a)
        resp.nombreUsuario = usuario.nombre if usuario else "Desconocido"
        resultado.append(resp)
    
    return resultado
