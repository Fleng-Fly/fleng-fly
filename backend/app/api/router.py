from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.exercises.router import router as exercises_router
from app.modules.gamification.router import router as gamification_router
from app.modules.health.router import router as health_router
from app.modules.password_reset.router import router as password_reset_router
from app.modules.progress.router import router as progress_router
from app.modules.users.router import router as users_router
from app.modules.vocabulary.router import router as vocabulary_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(progress_router)
api_router.include_router(catalog_router)
api_router.include_router(exercises_router)
api_router.include_router(vocabulary_router)
api_router.include_router(gamification_router)
api_router.include_router(password_reset_router)
api_router.include_router(ai_router)
