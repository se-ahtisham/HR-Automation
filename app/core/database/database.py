# This file is the door to your database. It sets up one connection, and all your other code uses that same door.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# The connection to my SQLite database
engine = create_engine(os.environ["DATABASE_URL"])


def run_sql(sql, values=None):
    with engine.begin() as conn:
        conn.execute(text(sql), values or {})
