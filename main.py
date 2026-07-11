from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
import app.models.modelo_bd
from app.routers import tarea_router, proyecto_router, usuario_router

#se lee todas los modelos y crea las tablas en postgreSQL automaticamente
Base.metadata.create_all(bind=engine)

#inicializar la aplicacion
app= FastAPI(
    title="StudyFlow API",
    description="Backend para el gestor de tareas universitarias",
    version="1.0.0"
)

#Configuracion de CORS para permitir el front
origins = [
    "*",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Conectar las rutas a la aplicación (Para que aparezcan en /docs)
app.include_router(usuario_router.router)
app.include_router(proyecto_router.router)
app.include_router(tarea_router.router)

# prueba endpoint
@app.get ("/", tags=["Estado del Servidor"])

def ruta_raiz():
    return{
        "estado":"Online",
        "mensaje":"El backend de studyflow esta conectado",
        "base_de_datos":"Conectada a render",
    }
