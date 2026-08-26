"""Authentication API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenRefresh, TokenResponse, UserLogin, UserRegister, UserResponse,
)
from app.services import auth as auth_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user and return tokens."""
    existing_user = await auth_service.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = await auth_service.create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        role=user_in.role,
    )

    access_token = auth_service.create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,  # 30 mins
        "user": user,
    }


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 compatible token login, getting an access token for future requests."""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": user,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_in: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    payload = auth_service.decode_token(token_in.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    import uuid
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await auth_service.get_user_by_id(db, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = auth_service.create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = auth_service.create_refresh_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return current_user
