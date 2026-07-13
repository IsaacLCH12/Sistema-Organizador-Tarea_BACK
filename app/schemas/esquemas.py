
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import date, datetime

# ==================== TAREAS ====================

class TareaCreate(BaseModel):
    idProyecto: int
    titulo: str
    descripcion: Optional[str] = None
    etiquetaRecomendada: str
    prioridad: str = "Medium"
    tipoIssue: str = "Task"
    fechaLimite: Optional[date] = None
    puntosHistoria: Optional[int] = None

    @field_validator('prioridad')
    @classmethod
    def validar_prioridad(cls, v):
        opciones = ["Critical", "High", "Medium", "Low"]
        if v not in opciones:
            raise ValueError(f"Prioridad inválida. Use: {', '.join(opciones)}")
        return v
    
    @field_validator('tipoIssue')
    @classmethod
    def validar_tipo(cls, v):
        opciones = ["Task", "Bug", "Story"]
        if v not in opciones:
            raise ValueError(f"Tipo inválido. Use: {', '.join(opciones)}")
        return v

    @field_validator('fechaLimite')
    @classmethod
    def validar_fecha(cls, v):
        if v is not None and v < date.today():
            raise ValueError("La fecha límite debe ser hoy o una fecha futura")
        return v

    @field_validator('puntosHistoria')
    @classmethod
    def validar_puntos(cls, v):
        if v is not None and v not in [1, 2, 3, 5, 8, 13]:
            raise ValueError("Los puntos de historia deben ser: 1, 2, 3, 5, 8, 13")
        return v

class TareaResponse(BaseModel):
    idTarea: int
    idProyecto: int
    idMiembroEquipo: Optional[int]
    titulo: str
    descripcion: Optional[str]
    etiquetaRecomendada: str
    estado: str
    prioridad: str
    tipoIssue: str
    fechaLimite: Optional[date]
    puntosHistoria: Optional[int]
    idReportero: Optional[int]
    fechaCreacion: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class TareaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    etiquetaRecomendada: Optional[str] = None
    prioridad: Optional[str] = None
    tipoIssue: Optional[str] = None
    fechaLimite: Optional[date] = None
    puntosHistoria: Optional[int] = None

    @field_validator('prioridad')
    @classmethod
    def validar_prioridad(cls, v):
        if v is not None:
            opciones = ["Critical", "High", "Medium", "Low"]
            if v not in opciones:
                raise ValueError(f"Prioridad inválida. Use: {', '.join(opciones)}")
        return v
    
    @field_validator('tipoIssue')
    @classmethod
    def validar_tipo(cls, v):
        if v is not None:
            opciones = ["Task", "Bug", "Story"]
            if v not in opciones:
                raise ValueError(f"Tipo inválido. Use: {', '.join(opciones)}")
        return v

    @field_validator('fechaLimite')
    @classmethod
    def validar_fecha(cls, v):
        if v is not None and v < date.today():
            raise ValueError("La fecha límite debe ser hoy o una fecha futura")
        return v

    @field_validator('puntosHistoria')
    @classmethod
    def validar_puntos(cls, v):
        if v is not None and v not in [1, 2, 3, 5, 8, 13]:
            raise ValueError("Los puntos de historia deben ser: 1, 2, 3, 5, 8, 13")
        return v

# ==================== PROYECTOS ====================

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

# ==================== USUARIOS ====================

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

class PerfilResponse(BaseModel):
    idUsuario: int
    nombre: str
    correo: str
    tareasCompletadas: int = 0
    tareasEnProgreso: int = 0
    tareasPendientes: int = 0
    totalProyectos: int = 0

class ActualizarPerfil(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    contrasena: Optional[str] = None

# ==================== UNIRSE A PROYECTO ====================

class UnirseProyecto(BaseModel):
    idUsuario: int
    codigoInvitacion: str
    rolFuncional: str  # Ej: "Frontend", "Backend", "Tester"

# ==================== MOVER TAREA (Kanban) ====================

class ActualizarEstadoTarea(BaseModel):
    estado: str  # Ej: "In Progress", "In Review", "Done"

    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        opciones = ["To Do", "In Progress", "In Review", "Done"]
        if v not in opciones:
            raise ValueError(f"Estado inválido. Use: {', '.join(opciones)}")
        return v

# ==================== MIEMBROS ====================

class MiembroEquipoResponse(BaseModel):
    idMiembroEquipo: int
    idUsuario: int
    idProyecto: int
    rolPermiso: str
    rolFuncional: str
    tareasActivas: int
    nombreUsuario: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# ==================== COMENTARIOS ====================

class ComentarioCreate(BaseModel):
    contenido: str

    @field_validator('contenido')
    @classmethod
    def validar_contenido(cls, v):
        if not v or not v.strip():
            raise ValueError("El comentario no puede estar vacío")
        return v.strip()

class ComentarioResponse(BaseModel):
    idComentario: int
    idTarea: int
    idUsuario: int
    contenido: str
    fechaCreacion: Optional[datetime]
    nombreUsuario: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# ==================== ACTIVIDAD / HISTORIAL ====================

class ActividadResponse(BaseModel):
    idActividad: int
    idTarea: int
    idUsuario: int
    accion: str
    detalle: Optional[str]
    fechaCreacion: Optional[datetime]
    nombreUsuario: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
