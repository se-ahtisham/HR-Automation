# Web addresses for HR login and making an HR account
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.accounts import create_account, find_by_email, log_in

router = APIRouter(prefix="/auth", tags=["HR login"])


# No files here, so the request body is JSON. Pydantic checks that every field is there
class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


# What the page gets back. Never send the password hash
def public_account(account):
    return {"id": account.id, "name": account.name, "email": account.email, "role": "HR"}


@router.post("/login")
def login(request: LoginRequest):
    account = log_in(request.email, request.password)
    if account is None:
        # The same message for a wrong email and a wrong password, so nobody can guess which emails exist
        raise HTTPException(status_code=401, detail="Email or password is wrong.")
    return public_account(account)


@router.post("/signup")
def signup(request: SignupRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Please write your name.")
    if "@" not in request.email or "." not in request.email:
        raise HTTPException(status_code=400, detail="Please write a real email address.")
    # bcrypt only uses the first 72 bytes, so I don't allow longer passwords
    if len(request.password) < 8 or len(request.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="The password must be 8 to 72 characters.")
    if find_by_email(request.email) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    account = create_account(request.name, request.email, request.password)
    return public_account(account)
