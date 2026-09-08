from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserResponse, UserCreate
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Akun pengguna non-aktif"
        )
        
    access_token = create_access_token(subject=user.username, role=user.role)
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        full_name=user.full_name
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/users", response_model=UserResponse)
def create_user(
    req: UserCreate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_current_admin)
):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
        
    new_user = User(
        username=req.username,
        full_name=req.full_name,
        nip=req.nip,
        role=req.role,
        password_hash=get_password_hash(req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
