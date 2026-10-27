from fastapi import APIRouter, status, Depends,HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel, Field

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets

from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse

from ..database import SessionLocal, blacklisted_tokens
from ..models import Users
from ..security import verify_password

from pathlib import Path


router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

load_dotenv("D:\Live_Hosting_Projects\Fastapi_Online_Personalized_Store_Project\.env")

#Access Token Start
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_acess_token(username: str, userid: int, userrole: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "username": username,
        "userid": userid,
        "userrole": userrole,
        "jti": secrets.token_urlsafe(32),
        "exp": expires_at
        }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )
#Access Token End


security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],):
    token = credentials.credentials
    scheme = credentials.scheme

    print(scheme,token,sep=":")
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    jti = payload.get("jti")
    print(jti)
    if not jti or jti in blacklisted_tokens:
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

class UserLoginRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str


###  Pages Start Down  ###
BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# templates = Jinja2Templates(directory="StoreWebApp/templates")


@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


@router.get('/login-page')
def render_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.get("/home")
def render_home_page(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/auth/login-page", status_code=303)

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        response = RedirectResponse(url="/auth/login-page", status_code=303)

    jti = payload.get("jti")

    if not jti or jti in blacklisted_tokens:
        response = RedirectResponse(url="/auth/login-page", status_code=303)
        response.delete_cookie("access_token")
        return response

    return templates.TemplateResponse(request=request, name="homepage.html",
        context={
            "username": payload.get("username")
        }
    )
###  Pages   End   Up  ###



@router.post('/login', status_code=status.HTTP_200_OK)
def user_login(db: db_dependency, user_login_request: UserLoginRequest) -> dict:
    ''' User Login'''
    user = db.query(Users).filter(user_login_request.username == Users.username).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User Not Found")

    verify = verify_password(user_login_request.password, user.hashed_password)

    if not verify:
        raise HTTPException(status_code=401, detail="Incorrect Password!")

    access_token = create_acess_token(user.username, user.id, user.role)

    # return {'access_token': access_token}
    response = JSONResponse(
        content={"message":"Login Successful"}
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False, #will be setting true when using https
        samesite="lax",
        max_age= ACCESS_TOKEN_EXPIRE_MINUTES*60,
        path="/"
    )

    return response


@router.post("/logout", status_code=status.HTTP_200_OK)
# def user_logout(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    # token = credentials.credentials
# def user_logout(request: Request):
    # token = request.cookies.get("access_token")
def user_logout(request: Request, response: Response
                , credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None):

    # print(credentials.credentials)
    # print(request.cookies.get("access_token"))
    token = (credentials.credentials if credentials else request.cookies.get("access_token"))

    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(status_code=401, detail="Token ID missing")

    if jti in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Already logged out")

    blacklisted_tokens.add(jti)

    #Delete browser cookies
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=False,  # Use True in production with HTTPS
        samesite="lax",
    )

    return {"message": "Successfully logged out"}

@router.get("/me")
def get_my_profile(current_user: Annotated[dict, Depends(get_current_user)]):
    return {
        "username": current_user["username"],
        "userid": current_user["userid"],
        "userrole": current_user["userrole"]
    }