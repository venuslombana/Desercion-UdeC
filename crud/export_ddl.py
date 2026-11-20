"""Genera el script de creación para PostgreSQL:  python export_ddl.py > ../db/schema_postgres.sql"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from app.models import Base
d = postgresql.dialect()
print("-- Esquema generado desde app/models.py (PostgreSQL)\n")
for t in Base.metadata.sorted_tables:
    print(str(CreateTable(t).compile(dialect=d)).strip() + ";\n")
    for ix in sorted(t.indexes, key=lambda i: i.name): print(str(CreateIndex(ix).compile(dialect=d)).strip() + ";")
    print()
