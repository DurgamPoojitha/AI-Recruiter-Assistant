from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import init_db
from backend.core.exceptions import AppError, app_error_handler, global_exception_handler
from backend.core.logging import logger
from backend.api.routes import matches, copilot, ats

app = FastAPI(title="Enterprise AI Recruiter API")

# Initialize database
init_db()

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Routers
app.include_router(matches.router, tags=["Matches & ATS"])
app.include_router(copilot.router, tags=["AI Copilot"])
app.include_router(ats.router, prefix="/ats", tags=["ATS Pipeline"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Enterprise AI Recruiter API (Phase 1)"}

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting...")
    # Trigger lazy load of embedding model on startup
    from backend.services.embedding_service import get_embedding_service
    get_embedding_service()
