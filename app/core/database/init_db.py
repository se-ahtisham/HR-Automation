from pathlib import Path
from sqlalchemy import text
from app.core.database.database import engine

sql = Path("app/core/database/schema.sql").read_text(encoding="utf-8")


with engine.begin() as conn:
    # Each SQL statement ends with a semicolon. A piece with only comments is skipped:
    # SQLite allows it, but Turso (libsql) says "not an error" and stops
    for statement in sql.split(";"):
        code = [line for line in statement.splitlines() if line.strip() and not line.strip().startswith("--")]
        if code:
            conn.execute(text(statement))

print("Tables are ready")
