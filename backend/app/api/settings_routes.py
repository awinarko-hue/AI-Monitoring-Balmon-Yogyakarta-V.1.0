from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.config_setting import ConfigSetting
from app.schemas.config import ConfigSettingSchema
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Balmon Configuration"])

@router.get("", response_model=ConfigSettingSchema)
def get_config_settings(db: Session = Depends(get_db)):
    cfg = db.query(ConfigSetting).filter(ConfigSetting.setting_key == "default").first()
    if not cfg:
        cfg = ConfigSetting(
            setting_key="default",
            lat_min=-8.213584,
            lat_max=-7.503037,
            lon_min=109.375246,
            lon_max=111.321684,
            default_threshold_dbuvm=50.0,
            default_radius_km=50.0
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg

@router.put("", response_model=ConfigSettingSchema)
def update_config_settings(
    req: ConfigSettingSchema, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    cfg = db.query(ConfigSetting).filter(ConfigSetting.setting_key == "default").first()
    if not cfg:
        cfg = ConfigSetting(setting_key="default")
        db.add(cfg)
        
    cfg.lat_min = req.lat_min
    cfg.lat_max = req.lat_max
    cfg.lon_min = req.lon_min
    cfg.lon_max = req.lon_max
    cfg.default_threshold_dbuvm = req.default_threshold_dbuvm
    cfg.default_radius_km = req.default_radius_km
    if req.extra_params:
        cfg.extra_params = req.extra_params
        
    db.commit()
    db.refresh(cfg)
    return cfg
