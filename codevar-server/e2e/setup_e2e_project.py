"""
Crea la base de datos de prueba (SQLite) para la demo end-to-end y le
registra un Project con la api_key que usará backend-canchas.

Uso:
    DATABASE_URL="sqlite:////tmp/codevar_e2e.db" python e2e/setup_e2e_project.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Project
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
db = Session()
db.add(Project(name="backend-canchas", api_key="e2e-test-key"))
db.commit()
db.close()

print(f"Base de datos lista en: {DATABASE_URL}")
print("Project creado: name=backend-canchas, api_key=e2e-test-key")
