from fastapi import FastAPI, Request, HTTPException

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import users, auth
from .models import Base
from .database import engine

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from pathlib import Path


app = FastAPI()

#Overwrite HTTPException and Pydantics Output Start

# @app.exception_handler(HTTPException)
# async def http_exception_handler(
#     request: Request, exc: HTTPException
# ):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"msg": exc.detail}
#     )


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(
#     request: Request, exc: RequestValidationError
# ):
#     return JSONResponse(
#         status_code=422,
#         content={"msg": exc.errors()[0]["msg"]}
#     )

#Overwrite HTTPException and Pydantics Output  End

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# templates = Jinja2Templates(directory="StoreWebApp/templates")
# app.mount("/static", StaticFiles(directory="StoreWebApp/static"), name="static")

@app.get("/health-check")
def health_check():
    return {'Detail':'Successfully Connected!'}

app.include_router(users.router)
app.include_router(auth.router)