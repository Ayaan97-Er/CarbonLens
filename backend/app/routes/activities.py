import datetime
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.category import Category
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ActivityOut,
    PaginatedActivities,
    ActivityCalculationPreview,
)
from app.auth.dependencies import get_current_user
from app.services.carbon_calculator import CarbonCalculationService
from app.services.achievement_service import AchievementService

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("/preview", response_model=ActivityCalculationPreview)
def preview_activity_calculation(
    activity_type: str = Query(..., description="Activity type name"),
    quantity: float = Query(..., gt=0, description="Numerical quantity"),
    category_id: Optional[int] = Query(None, description="Category ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get live preview of calculated carbon footprint for a given activity and quantity.
    """
    preview = CarbonCalculationService.preview_calculation(
        db=db,
        activity_type=activity_type,
        quantity=quantity,
        category_id=category_id,
    )
    return preview


@router.get("", response_model=PaginatedActivities)
def list_activities(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    start_date: Optional[datetime.date] = Query(None, description="Filter start date"),
    end_date: Optional[datetime.date] = Query(None, description="Filter end date"),
    search: Optional[str] = Query(None, description="Search term in activity type or notes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List activities for the authenticated user with filtering and pagination.
    """
    query = db.query(Activity).filter(Activity.user_id == current_user.id)

    if category_id:
        query = query.filter(Activity.category_id == category_id)
    if activity_type:
        query = query.filter(Activity.activity_type.ilike(f"%{activity_type}%"))
    if start_date:
        query = query.filter(Activity.activity_date >= start_date)
    if end_date:
        query = query.filter(Activity.activity_date <= end_date)
    if search:
        query = query.filter(
            (Activity.activity_type.ilike(f"%{search}%"))
            | (Activity.notes.ilike(f"%{search}%"))
        )

    # Total count and aggregate emissions
    total_count = query.count()
    total_emissions = (
        query.with_entities(func.sum(Activity.calculated_co2)).scalar() or 0.0
    )

    # Pagination
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size
    items = (
        query.order_by(Activity.activity_date.desc(), Activity.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_emissions_kg": round(float(total_emissions), 2),
    }


@router.post("", response_model=ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_in: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a new carbon activity. Automatically retrieves emission factor snapshot,
    calculates CO2e, stores record, and triggers achievement evaluation.
    """
    # Verify category exists
    category = db.query(Category).filter(Category.id == activity_in.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified category not found."
        )

    # Calculate emission factor and CO2
    factor, unit, _ = CarbonCalculationService.get_factor_for_activity(
        db=db,
        activity_type=activity_in.activity_type,
        category_id=activity_in.category_id,
    )

    calculated_co2 = CarbonCalculationService.calculate_co2(
        quantity=activity_in.quantity,
        emission_factor=factor,
    )

    activity = Activity(
        user_id=current_user.id,
        category_id=activity_in.category_id,
        activity_type=activity_in.activity_type.strip(),
        quantity=activity_in.quantity,
        unit=activity_in.unit.strip() or unit,
        emission_factor=factor,
        calculated_co2=calculated_co2,
        activity_date=activity_in.activity_date,
        notes=activity_in.notes.strip() if activity_in.notes else None,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    # Check and trigger achievements
    try:
        AchievementService.evaluate_user_achievements(db, current_user.id)
    except Exception:
        pass  # Non-blocking for activity creation

    return activity


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve an activity by ID. Validates user ownership."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found."
        )
    if activity.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this activity."
        )
    return activity


@router.put("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: int,
    activity_in: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing activity. Recalculates CO2e if quantity or type changed."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found."
        )
    if activity.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this activity."
        )

    # Apply updates
    if activity_in.category_id is not None:
        activity.category_id = activity_in.category_id
    if activity_in.activity_type is not None:
        activity.activity_type = activity_in.activity_type.strip()
    if activity_in.quantity is not None:
        activity.quantity = activity_in.quantity
    if activity_in.unit is not None:
        activity.unit = activity_in.unit.strip()
    if activity_in.activity_date is not None:
        activity.activity_date = activity_in.activity_date
    if activity_in.notes is not None:
        activity.notes = activity_in.notes.strip()

    # Recalculate
    factor, unit, _ = CarbonCalculationService.get_factor_for_activity(
        db=db,
        activity_type=activity.activity_type,
        category_id=activity.category_id,
    )
    activity.emission_factor = factor
    activity.calculated_co2 = CarbonCalculationService.calculate_co2(
        quantity=activity.quantity,
        emission_factor=factor,
    )

    db.commit()
    db.refresh(activity)

    # Trigger achievement evaluation
    try:
        AchievementService.evaluate_user_achievements(db, current_user.id)
    except Exception:
        pass

    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_200_OK)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an activity. Validates user ownership."""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found."
        )
    if activity.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this activity."
        )

    db.delete(activity)
    db.commit()
    return {"message": "Activity deleted successfully.", "id": activity_id}
