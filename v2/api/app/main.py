from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import boroughs, compare, health, postcodes


def create_app() -> FastAPI:
    app = FastAPI(
        title="Housing in London API",
        version="0.1.0",
        description="Backend for v2 web app. Postcode lookup, TfL journeys, council tax, rent.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(postcodes.router, prefix="/api")
    app.include_router(boroughs.router, prefix="/api")
    app.include_router(compare.router, prefix="/api")

    return app


app = create_app()
