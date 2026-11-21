from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.goal import Goal
from app.models.category import Category
from app.models.emission_factor import EmissionFactor
from app.models.achievement import Achievement, UserAchievement
from app.schemas.admin import AdminUserOut, AdminUserUpdateRole, SystemStatsOut
from app.schemas.category import EmissionFactorCreate, EmissionFactorOut
from app.auth.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get("/stats", response_model=SystemStatsOut)
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Retrieve platform-wide system usage statistics (Admin Only)."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_activities = db.query(func.count(Activity.id)).scalar() or 0
    total_emissions = db.query(func.sum(Activity.calculated_co2)).scalar() or 0.0
    total_goals = db.query(func.count(Goal.id)).scalar() or 0
    total_achievements = db.query(func.count(UserAchievement.id)).scalar() or 0
    categories_count = db.query(func.count(Category.id)).scalar() or 0
    factors_count = db.query(func.count(EmissionFactor.id)).scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_activities_logged": total_activities,
        "total_emissions_tracked_kg": round(float(total_emissions), 2),
        "total_goals_set": total_goals,
        "total_achievements_unlocked": total_achievements,
        "categories_count": categories_count,
        "factors_count": factors_count,
    }


@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """List all registered users with summary statistics (Admin Only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    results = []
    for u in users:
        act_count = db.query(func.count(Activity.id)).filter(Activity.user_id == u.id).scalar() or 0
        total_co2 = db.query(func.sum(Activity.calculated_co2)).filter(Activity.user_id == u.id).scalar() or 0.0
        results.append(AdminUserOut(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            leaderboard_opt_in=u.leaderboard_opt_in,
            public_handle=u.public_handle,
            created_at=u.created_at,
            updated_at=u.updated_at,
            total_activities=act_count,
            total_emissions_kg=round(float(total_co2), 2),
        ))
    return results


@router.put("/users/{user_id}/status", response_model=AdminUserOut)
def update_user_status(
    user_id: int,
    update_in: AdminUserUpdateRole,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Toggle user active status or role (Admin Only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id and not update_in.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate own admin account")

    user.role = update_in.role
    user.is_active = update_in.is_active
    db.commit()
    db.refresh(user)

    act_count = db.query(func.count(Activity.id)).filter(Activity.user_id == user.id).scalar() or 0
    total_co2 = db.query(func.sum(Activity.calculated_co2)).filter(Activity.user_id == user.id).scalar() or 0.0

    return AdminUserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        leaderboard_opt_in=user.leaderboard_opt_in,
        public_handle=user.public_handle,
        created_at=user.created_at,
        updated_at=user.updated_at,
        total_activities=act_count,
        total_emissions_kg=round(float(total_co2), 2),
    )


@router.post("/emission-factors", response_model=EmissionFactorOut, status_code=status.HTTP_201_CREATED)
def create_emission_factor(
    factor_in: EmissionFactorCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create a new configurable emission factor (Admin Only)."""
    category = db.query(Category).filter(Category.id == factor_in.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    factor = EmissionFactor(
        category_id=factor_in.category_id,
        activity_type=factor_in.activity_type.strip(),
        unit=factor_in.unit.strip(),
        factor=factor_in.factor,
        source=factor_in.source,
        version=factor_in.version,
        description=factor_in.description,
        is_active=factor_in.is_active,
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return factor
