import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.activity import Activity
from app.schemas.goal import GoalCreate, GoalUpdate, GoalOut, GoalProgressOut
from app.auth.dependencies import get_current_user
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/goals", tags=["Goals & Carbon Budget"])


@router.get("/current", response_model=GoalProgressOut)
def get_current_goal_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current active monthly target and budget consumption progress.
    """
    summary = DashboardService.get_dashboard_summary(db=db, user_id=current_user.id)
    return summary["goal"]


@router.get("/history", response_model=List[GoalOut])
def list_goals_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all goals configured by the user."""
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == current_user.id)
        .order_by(Goal.created_at.desc())
        .all()
    )
    return goals


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def set_goal(
    goal_in: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a new monthly carbon budget target.
    Deactivates previous active goals and establishes the new active target.
    """
    # Deactivate previous active goals
    db.query(Goal).filter(
        Goal.user_id == current_user.id,
        Goal.is_active == True
    ).update({"is_active": False})

    new_goal = Goal(
        user_id=current_user.id,
        monthly_target=goal_in.monthly_target,
        start_date=goal_in.start_date or datetime.date.today(),
        end_date=goal_in.end_date,
        is_active=True,
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


@router.put("/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int,
    goal_in: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing goal."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found."
        )
    if goal.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied."
        )

    if goal_in.monthly_target is not None:
        goal.monthly_target = goal_in.monthly_target
    if goal_in.start_date is not None:
        goal.start_date = goal_in.start_date
    if goal_in.end_date is not None:
        goal.end_date = goal_in.end_date
    if goal_in.is_active is not None:
        goal.is_active = goal_in.is_active

    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a goal from target history."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found."
        )
    if goal.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied."
        )

    was_active = goal.is_active
    db.delete(goal)
    db.commit()

    # If the active goal was deleted, set the latest remaining goal as active if one exists
    if was_active:
        latest = (
            db.query(Goal)
            .filter(Goal.user_id == current_user.id)
            .order_by(Goal.created_at.desc())
            .first()
        )
        if latest:
            latest.is_active = True
            db.commit()

    return None

