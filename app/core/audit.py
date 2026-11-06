from sqlalchemy import text

from app.core.database.database import engine, run_sql


# Writes down who did what. Never put CV text, phone numbers or call text in details
def add_audit_event(actor, action, entity_type, entity_id, details=""):
    run_sql(
        """
        INSERT INTO audit_events (actor, action, entity_type, entity_id, details)
        VALUES (:actor, :action, :entity_type, :entity_id, :details)
        """,
        {
            "actor": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
        },
    )


# Reads the history, newest first. With entity_type and entity_id: one thing's history (like one candidate).
# Without them: everything (the Dashboard's recent activity)
def list_history(entity_type=None, entity_id=None, limit=50):
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT actor, action, entity_type, entity_id, details, timestamp
            FROM audit_events
            WHERE (:entity_type IS NULL OR entity_type = :entity_type)
              AND (:entity_id IS NULL OR entity_id = :entity_id)
            ORDER BY id DESC
            LIMIT :limit
        """), {"entity_type": entity_type, "entity_id": entity_id, "limit": limit}).mappings().all()
    return [dict(row) for row in rows]
