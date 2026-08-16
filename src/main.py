from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.limiter import limiter
from src.middleware import LoggingMiddleware
from src.routers.admin.appointment import router as admin_appointments_router
from src.routers.admin.auth import router as admin_auth_router
from src.routers.admin.availability import router as admin_availability_router
from src.routers.admin.blocked_time import router as blocked_time_router
from src.routers.admin.design_tiers import router as admin_design_tiers_router
from src.routers.admin.nail_types import router as admin_nail_types_router
from src.routers.appointments import router as appointments_router
from src.routers.checkout import router as checkout_router
from src.routers.design_tiers import router as design_tiers_router
from src.routers.nail_analysis import router as nail_analysis_router
from src.routers.nail_types import router as nail_types_router
from src.routers.slots import router as slots_router

origins = ["http://localhost:5173", "http://localhost:3000"]

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(appointments_router)
app.include_router(checkout_router)
app.include_router(nail_types_router)
app.include_router(design_tiers_router)
app.include_router(admin_nail_types_router)
app.include_router(admin_design_tiers_router)
app.include_router(nail_analysis_router)
app.include_router(admin_availability_router)
app.include_router(blocked_time_router)
app.include_router(admin_appointments_router)
app.include_router(slots_router)
app.include_router(admin_auth_router)


@app.get("/")
def health_check():
    return {"status": "ok"}


handler = Mangum(app)
