from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.routers.appointments import router as appointments_router
from src.routers.admin.services import router as admin_services_router
from src.routers.services import router as services_router
from src.routers.admin.availability import router as admin_availability_router
from src.routers.admin.blocked_time import router as blocked_time_router
from src.routers.admin.appointment import router as admin_appointments_router
from src.routers.slots import router as slots_router
from src.routers.admin.auth import router as admin_auth_router
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.limiter import limiter
from src.exceptions import NotFoundError, ConflictError, ValidationError
from mangum import Mangum

origins = [
    "http://localhost:5173",
    "http://localhost:3000"
]

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(appointments_router)
app.include_router(admin_services_router)
app.include_router(services_router)
app.include_router(admin_availability_router)
app.include_router(blocked_time_router)
app.include_router(admin_appointments_router)
app.include_router(slots_router)
app.include_router(admin_auth_router)

@app.get("/")
def health_check():
    return {"status": "ok"}

handler = Mangum(app)