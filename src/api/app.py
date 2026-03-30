"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings
from src.api.deps import set_city_model, set_city_panel, set_model, set_panel
from src.api.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load model and panel at startup
        if settings.model_dir.exists() and settings.panel_parquet_path.exists():
            import pandas as pd
            from src.models.lgbm import CrashForecaster

            # Cell-level model + panel (for /hotspot endpoints)
            cell_model_path = settings.model_dir / "lgbm_cell_v1.txt"
            if cell_model_path.exists():
                set_model(CrashForecaster.load(cell_model_path))
            panel = pd.read_parquet(settings.panel_parquet_path)
            set_panel(panel)

            # City-level model + panel (for /forecast/city)
            city_model_path = settings.model_dir / "lgbm_city_v1.txt"
            if city_model_path.exists() and settings.city_panel_parquet_path.exists():
                set_city_model(CrashForecaster.load(city_model_path))
                set_city_panel(pd.read_parquet(settings.city_panel_parquet_path))
        yield

    app = FastAPI(title="CrashScope API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
