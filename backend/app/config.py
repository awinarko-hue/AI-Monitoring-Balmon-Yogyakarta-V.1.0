import os

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        class BaseSettings:
            pass

def get_default_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
        
    # Store SQLite in local physical disk (%LOCALAPPDATA% or user home) to prevent Google Drive I/O lock issues
    base_dir = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    local_data_dir = os.path.join(base_dir, "BalmonMonitoring")
    os.makedirs(local_data_dir, exist_ok=True)
    local_db_path = os.path.join(local_data_dir, "balmon_monitoring.db")
    
    # If a DB already exists in backend workspace and local DB does not exist yet, copy it
    workspace_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'balmon_monitoring.db'))
    if os.path.exists(workspace_db) and not os.path.exists(local_db_path):
        try:
            import shutil
            shutil.copy2(workspace_db, local_db_path)
        except Exception:
            pass
            
    return f"sqlite:///{local_db_path.replace(os.sep, '/')}"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Monitoring Balmon Yogyakarta"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "balmon-jogja-secret-key-2026-sdppi-komdigi")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database URL
    DATABASE_URL: str = get_default_database_url()
    
    # Default Balmon Yogyakarta Bounding Box
    DEFAULT_LAT_MIN: float = -8.213584
    DEFAULT_LAT_MAX: float = -7.503037
    DEFAULT_LON_MIN: float = 109.375246
    DEFAULT_LON_MAX: float = 111.321684
    
    # Default Monitoring Parameters
    DEFAULT_THRESHOLD_DBUVM: float = 50.0
    DEFAULT_DETECTION_RADIUS_KM: float = 50.0

settings = Settings()
