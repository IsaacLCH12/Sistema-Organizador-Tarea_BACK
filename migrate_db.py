import sys
sys.path.append('D:/Trabajos de la Universidad/7mo ciclo/Lenguajes de Programacion/AvanceProyecto/Sistema-Organizador-Tarea_BACK')
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

queries = [
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "prioridad" VARCHAR(20) DEFAULT \'Medium\'',
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "tipoIssue" VARCHAR(20) DEFAULT \'Task\'',
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "fechaLimite" DATE',
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "puntosHistoria" INTEGER',
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "idReportero" INTEGER',
    'ALTER TABLE "Tarea" ADD COLUMN IF NOT EXISTS "fechaCreacion" TIMESTAMP WITH TIME ZONE DEFAULT NOW()',
    
    # Also I added these tables, let's make sure they are created if create_all somehow didn't
]

for q in queries:
    try:
        db.execute(text(q))
    except Exception as e:
        print("Skipping/Error:", e)

db.commit()
print("Alter table commands finished")
