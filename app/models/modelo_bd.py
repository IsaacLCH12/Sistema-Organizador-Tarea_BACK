from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class UsuarioModel(Base):
    __tablename__="Usuario"

    idUsuario = Column (Integer,primary_key=True,index=True,autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo= Column(String(100),unique=True,nullable=False)
    contrasena= Column(String(100), nullable=False)

class ProyectoModel(Base):
    __tablename__ ="Proyecto"

    idProyecto = Column(Integer, primary_key=True,index=True,autoincrement=True)
    nombre = Column(String(80), nullable=False)
    descripcion = Column ( Text, nullable=True)
    codigoInvitacion=Column(String(20), unique=True, nullable=False)
    estado= Column(String(50), server_default="esperando integrantes")

class MiembroEquipoModel(Base):
    __tablename__ = "MiembroEquipo"
    
    idMiembroEquipo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    idUsuario = Column(Integer, ForeignKey("Usuario.idUsuario"), nullable=False)
    idProyecto = Column(Integer, ForeignKey("Proyecto.idProyecto"), nullable=False)
    rolPermiso = Column(String(25), nullable=False)
    rolFuncional = Column(String(30), nullable=False)
    tareasActivas = Column(Integer, server_default="0")

class TareaModel(Base):
    __tablename__ = "Tarea"
    
    idTarea = Column(Integer, primary_key=True, index=True, autoincrement=True)
    idProyecto = Column(Integer, ForeignKey("Proyecto.idProyecto"), nullable=False)
    idMiembroEquipo = Column(Integer, ForeignKey("MiembroEquipo.idMiembroEquipo"), nullable=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    etiquetaRecomendada = Column(String(50), nullable=False)
    estado = Column(String(50), server_default="To Do")
    
    # Nuevos campos estilo Jira
    prioridad = Column(String(20), server_default="Medium")  # Critical, High, Medium, Low
    tipoIssue = Column(String(20), server_default="Task")    # Task, Bug, Story
    fechaLimite = Column(Date, nullable=True)
    puntosHistoria = Column(Integer, nullable=True)           # Fibonacci: 1,2,3,5,8,13
    idReportero = Column(Integer, ForeignKey("Usuario.idUsuario"), nullable=True)  # Quién creó la tarea
    fechaCreacion = Column(DateTime(timezone=True), server_default=func.now())

class ComentarioModel(Base):
    __tablename__ = "Comentario"

    idComentario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    idTarea = Column(Integer, ForeignKey("Tarea.idTarea", ondelete="CASCADE"), nullable=False)
    idUsuario = Column(Integer, ForeignKey("Usuario.idUsuario"), nullable=False)
    contenido = Column(Text, nullable=False)
    fechaCreacion = Column(DateTime(timezone=True), server_default=func.now())

class ActividadModel(Base):
    __tablename__ = "Actividad"

    idActividad = Column(Integer, primary_key=True, index=True, autoincrement=True)
    idTarea = Column(Integer, ForeignKey("Tarea.idTarea", ondelete="CASCADE"), nullable=False)
    idUsuario = Column(Integer, ForeignKey("Usuario.idUsuario"), nullable=False)
    accion = Column(String(100), nullable=False)   # "cambió estado", "asignó tarea", "editó descripción"
    detalle = Column(String(255), nullable=True)    # "de 'To Do' a 'In Progress'"
    fechaCreacion = Column(DateTime(timezone=True), server_default=func.now())