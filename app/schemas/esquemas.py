
from pydantic import BaseModel, ConfigDict
from typing import Optional

# Esquemas para TAREAS
class TareaCreate(BaseModel):
    idProyecto: int
    titulo: str
    descripcion: Optional[str] = None
    etiquetaRecomendada: str

class TareaResponse(BaseModel):
    idTarea: int
    idProyecto: int
    idMiembroEquipo: Optional[int]
    titulo: str
    descripcion: Optional[str]
    etiquetaRecomendada: str
    estado: str

    model_config = ConfigDict(from_attributes=True)

# Esquemas para PROYECTOS
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    

class ProyectoResponse(BaseModel):
    idProyecto: int
    nombre: str
    descripcion: Optional[str]
    codigoInvitacion: str
    estado: str

    model_config = ConfigDict(from_attributes=True)

# Esquemas para USUARIOS (Login y Registro)
class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    contrasena: str

class UsuarioResponse(BaseModel):
    idUsuario: int
    nombre: str
    correo: str
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    correo: str
    contrasena: str

# Esquema para UNIRSE A UN PROYECTO
class UnirseProyecto(BaseModel):
    idUsuario: int
    codigoInvitacion: str
    rolFuncional: str  # Ej: "Frontend", "Backend", "Tester"

# Esquema para MOVER LA TAREA (Kanban)
class ActualizarEstadoTarea(BaseModel):
    estado: str  # Ej: "In Progress", "Review", "Done"
