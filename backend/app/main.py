import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.config_setting import ConfigSetting
from app.models.manual_station import ManualStation
from app.core.security import get_password_hash

from app.api.auth_routes import router as auth_router
from app.api.scan_routes import router as scan_router
from app.api.sims_routes import router as sims_router
from app.api.identification_routes import router as identification_router
from app.api.report_routes import router as report_router
from app.api.settings_routes import router as settings_router

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed default Admin
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin = User(
                username="admin",
                full_name="Administrator Balmon DIY",
                nip="198501012010011001",
                role="admin",
                password_hash=get_password_hash("admin123"),
                is_active=True
            )
            db.add(admin)
            
        # Seed sample Petugas
        officer_user = db.query(User).filter(User.username == "petugas").first()
        if not officer_user:
            officer = User(
                username="petugas",
                full_name="Agus Dong (PPFR Ahli Muda)",
                nip="199002022015021002",
                role="petugas",
                password_hash=get_password_hash("petugas123"),
                is_active=True
            )
            db.add(officer)
            
        # Seed default ConfigSetting
        cfg = db.query(ConfigSetting).filter(ConfigSetting.setting_key == "default").first()
        if not cfg:
            default_cfg = ConfigSetting(
                setting_key="default",
                lat_min=-8.213584,
                lat_max=-7.503037,
                lon_min=109.375246,
                lon_max=111.321684,
                default_threshold_dbuvm=50.0,
                default_radius_km=50.0
            )
            db.add(default_cfg)
            
        # Seed sample manual stations
        if db.query(ManualStation).count() == 0:
            sample_manuals = [
                ManualStation(
                    freq_mhz=463.5, client_name="STI", latitude=-7.733042, longitude=110.471837,
                    service="BERGERAK DARAT", subservice="CDMA", emission_class="G7W", status_legality="Legal"
                ),
                ManualStation(
                    freq_mhz=465.0, client_name="STI", latitude=-7.733042, longitude=110.471837,
                    service="BERGERAK DARAT", subservice="CDMA", emission_class="G7W", status_legality="Legal"
                ),
                ManualStation(
                    freq_mhz=466.5, client_name="STI", latitude=-7.733042, longitude=110.471837,
                    service="BERGERAK DARAT", subservice="CDMA", emission_class="G7W", status_legality="Legal"
                ),
                ManualStation(
                    freq_mhz=874.0, client_name="SMARTFREN", latitude=-7.733042, longitude=110.471837,
                    service="BERGERAK DARAT", subservice="LTE", emission_class="G7W", status_legality="Legal"
                ),
                ManualStation(
                    freq_mhz=100.2, client_name="RADIO RETJO BUNTUNG FM", latitude=-7.7956, longitude=110.3695,
                    service="PENYIARAN", subservice="RADIO FM", emission_class="F3E", status_legality="Legal"
                ),
                ManualStation(
                    freq_mhz=97.0, client_name="RADIO GERONIMO FM", latitude=-7.7828, longitude=110.3742,
                    service="PENYIARAN", subservice="RADIO FM", emission_class="F3E", status_legality="Legal"
                )
            ]
            db.bulk_save_objects(sample_manuals)
            
        db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-Stack Web API untuk Auto-Identifikasi Spektrum Frekuensi Radio Balmon SFR Kelas I Yogyakarta",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(scan_router, prefix=settings.API_V1_STR)
app.include_router(sims_router, prefix=settings.API_V1_STR)
app.include_router(identification_router, prefix=settings.API_V1_STR)
app.include_router(report_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)

# Static files for web frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }
