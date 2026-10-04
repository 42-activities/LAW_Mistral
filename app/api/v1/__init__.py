from fastapi import APIRouter

from app.api.v1 import analyze, health, jurisdictions, product, recommend

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jurisdictions.router)
api_router.include_router(analyze.router)
api_router.include_router(recommend.router)
api_router.include_router(product.router)
