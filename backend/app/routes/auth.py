import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal
from app.schemas.auth import LoginRequest, RegisterRequest, Token, PasswordChangeRequest
from app.schemas.user import UserOut, UserUpdate
from app.auth.security import verify_password, get_password_hash, create_access_token
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Hashes password, initializes default settings, and returns an access token.
    """
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Derive public handle if not provided
    handle = request.public_handle
    if not handle:
        handle = request.full_name.split()[0] if request.full_name else "EcoTracker"

    # Create new user
    new_user = User(
        full_name=request.full_name.strip(),
        email=request.email.lower().strip(),
        password_hash=get_password_hash(request.password),
        role="user",
        is_active=True,
        leaderboard_opt_in=True,
        public_handle=handle,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Set default starter goal of 250 kg CO2e / month
    starter_goal = Goal(
        user_id=new_user.id,
        monthly_target=250.0,
        start_date=datetime.date.today(),
        is_active=True,
    )
    db.add(starter_goal)
    db.commit()

    # Generate JWT token
    access_token = create_access_token(
        subject=new_user.id,
        role=new_user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.model_validate(new_user),
    }


@router.post("/login", response_model=dict)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email and password.
    Returns JWT access token and user metadata.
    """
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support."
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserOut.model_validate(user),
    }


@router.post("/login-form", response_model=Token)
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 form endpoint for Swagger UI authentication."""
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve the currently authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile preferences."""
    if request.full_name is not None:
        current_user.full_name = request.full_name.strip()
    if request.leaderboard_opt_in is not None:
        current_user.leaderboard_opt_in = request.leaderboard_opt_in
    if request.public_handle is not None:
        current_user.public_handle = request.public_handle.strip()

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user password."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password updated successfully."}
