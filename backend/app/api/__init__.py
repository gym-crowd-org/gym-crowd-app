from fastapi import APIRouter

from app.api.routes import gyms, health, history, occupancy, predict

api_router = APIRouter(prefix="/api")
api_router.include_router(gyms.router)
api_router.include_router(occupancy.router)
api_router.include_router(predict.router)
api_router.include_router(history.router)

health_router = health.router
