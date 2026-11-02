from pathlib import Path
from sqlalchemy import text
from app.core.database.database import engine

sql = Path("app/core/database/schema.sql").read_text(encoding="utf-8")


with engine.begin() as conn:
    # Each SQL statement ends with a semicolon
    for statement in sql.split(";"):
        if statement.strip():
            conn.execute(text(statement))

print("Tables are ready")
