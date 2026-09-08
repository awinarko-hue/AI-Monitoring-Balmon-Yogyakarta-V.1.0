from pydantic import BaseModel
from typing import Optional, Dict, Any

class ConfigSettingSchema(BaseModel):
    id: Optional[int] = None
    setting_key: str = "default"
    lat_min: float = -8.213584
    lat_max: float = -7.503037
    lon_min: float = 109.375246
    lon_max: float = 111.321684
    default_threshold_dbuvm: float = 50.0
    default_radius_km: float = 50.0
    extra_params: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
