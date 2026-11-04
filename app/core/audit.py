from app.core.database.database import run_sql


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
