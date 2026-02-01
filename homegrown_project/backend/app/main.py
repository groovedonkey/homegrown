from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from . import models, database
from .routers.chat import router as chat_router
from .routers.enrollments import router as enrollments_router
from .routers.uploads import router as uploads_router

# Init Environment
load_dotenv(override=True)

app = FastAPI(title="Homegrown API")

# --- CORS SETUP ---
cors_allow_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = ["*"] if cors_allow_origins.strip() == "*" else [o.strip() for o in cors_allow_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(enrollments_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")

# --- Initialization ---
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)