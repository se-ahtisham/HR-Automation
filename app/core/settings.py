# The Settings rules: one row (id = 1) in scheduling_settings.
# The Pydantic model holds each rule's default and its allowed range, so a wrong value can never be saved
from typing import Literal

from pydantic import BaseModel, Field

from app.core.audit import add_audit_event
from app.core.database.database import get_one, run_sql


class Settings(BaseModel):
    interview_minutes: int = Field(45, ge=15, le=240)
    break_minutes: int = Field(15, ge=0, le=120)
    timezone: Literal["Asia/Karachi", "Asia/Dubai", "Europe/London", "America/New_York"] = "Asia/Karachi"
    meeting_type: Literal["Online", "In the office"] = "Online"
    booking_days: int = Field(7, ge=1, le=60)
    notice_hours: int = Field(24, ge=0, le=168)
    time_choices: int = Field(3, ge=1, le=10)
    max_per_day: int = Field(4, ge=1, le=20)
    keep_data_days: int = Field(90, ge=30, le=365)


# Gives back the rules as a dictionary. No row saved yet = the defaults
def get_settings() -> dict:
    row = get_one("SELECT * FROM scheduling_settings WHERE id = 1")
    return Settings.model_validate(dict(row._mapping) if row else {}).model_dump()


# Saves the rules and writes what changed to the audit log ("interview_minutes: 45 → 60").
# A wrong value raises pydantic's ValidationError. Gives back the list of changes
def save_settings(values, hr_email):
    new = Settings.model_validate(values).model_dump()
    old = get_settings()
    changes = [f"{name}: {old[name]} → {value}" for name, value in new.items() if old[name] != value]
    if not changes:
        return []

    # Make the one row if it isn't there yet, then update it
    run_sql("INSERT OR IGNORE INTO scheduling_settings (id) VALUES (1)")
    run_sql("""
        UPDATE scheduling_settings
        SET interview_minutes = :interview_minutes, break_minutes = :break_minutes, timezone = :timezone,
            meeting_type = :meeting_type, booking_days = :booking_days, notice_hours = :notice_hours,
            time_choices = :time_choices, max_per_day = :max_per_day,
            keep_data_days = :keep_data_days, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, new)
    add_audit_event(hr_email, "Settings changed", "settings", 1, "; ".join(changes))
    return changes
