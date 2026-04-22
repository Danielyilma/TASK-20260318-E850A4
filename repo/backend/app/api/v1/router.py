from fastapi import APIRouter

from app.api.v1.routes import (
    activities,
    auth,
    backups,
    funding_routes,
    health,
    materials_public,
    phase5_routes,
    registrations,
    reviews_batch,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(activities.router)
api_router.include_router(users.router)
api_router.include_router(registrations.router)
api_router.include_router(reviews_batch.router)
api_router.include_router(materials_public.router)
api_router.include_router(funding_routes.router)
api_router.include_router(phase5_routes.router)
api_router.include_router(backups.router)
