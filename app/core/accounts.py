# HR login accounts, saved in the hr_accounts table.
# Not the same as employees: employees are the staff HR adds and schedules for interviews.
# Passwords are never saved as plain text: bcrypt scrambles them into password_hash.
import bcrypt

from app.core.audit import add_audit_event
from app.core.database.database import get_one, run_sql


# Scrambles a password. The same password gives a different hash each time, because bcrypt adds a random "salt"
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# True when the typed password matches the saved hash
def password_is_right(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


# Finds one HR account by email, or gives back None
def find_by_email(email):
    return get_one(
        """
        SELECT id, name, email, password_hash, is_active
        FROM hr_accounts
        WHERE email = :email
        """,
        {"email": email.strip().lower()},
    )


# Makes a new HR account. The caller checks the password rules first
def create_account(name, email, password):
    run_sql(
        """
        INSERT INTO hr_accounts (name, email, password_hash)
        VALUES (:name, :email, :password_hash)
        """,
        {
            "name": name.strip(),
            "email": email.strip().lower(),
            "password_hash": hash_password(password),
        },
    )
    account = find_by_email(email)
    add_audit_event(account.email, "account created", "hr_account", account.id)
    return account


# Checks an email and password. Gives back the HR account, or None if they are wrong
def log_in(email, password):
    account = find_by_email(email)
    if account is None or not account.is_active:
        return None
    if not password_is_right(password, account.password_hash):
        return None
    add_audit_event(account.email, "logged in", "hr_account", account.id)
    return account
