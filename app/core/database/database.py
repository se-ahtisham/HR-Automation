# This file is the door to your database. It sets up one connection, and all your other code uses that same door.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text


load_dotenv()

# The connection to my SQLite database
engine = create_engine(os.environ["DATABASE_URL"])


def run_sql(sql, values=None):
    with engine.begin() as conn:
        conn.execute(text(sql), values or {})

# SQLite leaves foreign keys off, so I turn them on for each new connection
@event.listens_for(engine, "connect")
def turn_on_foreign_keys(connection, record):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def get_one(sql, values=None):
    with engine.begin() as conn:
        return conn.execute(text(sql), values or {}).fetchone()
