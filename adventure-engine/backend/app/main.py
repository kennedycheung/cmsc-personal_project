from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    activities_router,
    adventures_router,
    auth_router,
    deals_router,
    destinations_router,
    discovery_router,
    favorites_router,
    geocode_router,
    health_router,
    itineraries_router,
    local_activities_router,
    optimizations_router,
    preferences_router,
    recommendations_router,
    saved_adventures_router,
)
from app.core.config import settings
from app.database.connection import SessionLocal, engine
from app.database.seed import seed_sample_data
from app.models.base import Base
from app.services.deals.pipeline import run_ingestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_sample_data(db)
        # Placeholder connectors are pure local functions (no network calls),
        # and ingestion is an upsert keyed by (source, external_id), so
        # running it on every startup is cheap and safe.
        run_ingestion(db)
    yield


app = FastAPI(title='Adventure Arbitrage Engine API', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(health_router, prefix='/api')
app.include_router(destinations_router, prefix='/api')
app.include_router(activities_router, prefix='/api')
app.include_router(recommendations_router, prefix='/api')
app.include_router(itineraries_router, prefix='/api')
app.include_router(deals_router, prefix='/api')
app.include_router(auth_router, prefix='/api')
app.include_router(preferences_router, prefix='/api')
app.include_router(saved_adventures_router, prefix='/api')
app.include_router(favorites_router, prefix='/api')
app.include_router(optimizations_router, prefix='/api')
app.include_router(geocode_router, prefix='/api')
app.include_router(local_activities_router, prefix='/api')
app.include_router(discovery_router, prefix='/api')
app.include_router(adventures_router, prefix='/api')

@app.get('/')
def root():
    return {'message': 'Adventure Arbitrage Engine backend is running.'}
