from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryDetailOut, CategoryOut

router = APIRouter(prefix="/categories", tags=["Categories & Emission Factors"])


@router.get("", response_model=List[CategoryDetailOut])
def list_categories_with_factors(db: Session = Depends(get_db)):
    """
    List all active categories with their associated emission factors and units.
    Used by frontend forms to dynamically populate activity options.
    """
    categories = (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.name.asc())
        .all()
    )
    return categories


@router.get("/{category_id}", response_model=CategoryDetailOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Retrieve category details by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category
