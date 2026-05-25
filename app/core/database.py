import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

#cargar las variables de entorno desde el archivo .env
load_dotenv()

#obtener la url de render
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontro la variable DATABA_URL en el archivo .env")

#crear motor de conexion
engine = create_engine(DATABASE_URL,pool_pre_ping=True)

#configuracion de sesiones . las transacciones de la bd
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#clase base de la que heredan todas las tablas
Base = declarative_base()

#Funcion inyectora de dependecias para usar en los endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
