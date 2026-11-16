# This file is the door to your database. It sets up one connection, and all your other code uses that same door.
#   On my computer: DATABASE_URL in .env, a SQLite file (sqlite:///./data/hr.db)
#   Online:         TURSO_DATABASE_URL + TURSO_AUTH_TOKEN, the same SQLite database kept on Turso's servers
# All my SQL is the same for both, because Turso speaks SQLite.
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text

load_dotenv()

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")


class TursoConnection:
    """libsql works like Python's sqlite3, but has no create_function. SQLAlchemy calls it once (for REGEXP),
    so this small wrapper adds an empty one and passes everything else to the real connection."""

    def __init__(self, connection):
        self.connection = connection

    def create_function(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return getattr(self.connection, name)


def connect_to_turso():
    import certifi
    import libsql
    # On Windows, libsql can't find the list of trusted certificates, so the secure connection fails with
    # "invalid peer certificate: UnknownIssuer". certifi gives it the standard list
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    # The editor can't see inside libsql (it is written in Rust), so it doesn't know "connect" exists. It does
    return TursoConnection(libsql.connect(TURSO_URL, auth_token=os.environ.get("TURSO_AUTH_TOKEN", "")))  # pyrefly: ignore[missing-attribute]


# The connection to my database: Turso when its address is set, else my SQLite file
if TURSO_URL:
    engine = create_engine("sqlite://", creator=connect_to_turso)
else:
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
