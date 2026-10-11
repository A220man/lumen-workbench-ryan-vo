"""API route definitions for lumen-workbench-ryan-vo."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...models.title import Title
from ...core.db import get_db
from ...schemas.title import TitleCreate, TitleUpdate, TitleResponse

router = APIRouter(tags=["API"])


@router.get("/titles", response_model=List[TitleResponse])
async def list_titles(
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """List titles with optional filtering."""
    query = select(Title)
    
    if search:
        query = query.where(Title.name.ilike(f"%{search}%"))
    if status:
        query = query.where(Title.status == status)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    titles = db.execute(query).scalars().all()
    return [TitleResponse.model_validate(title) for title in titles]


@router.get("/titles/{title_id}", response_model=TitleResponse)
async def get_title(title_id: int, db: Session = Depends(get_db)):
    """Get a specific title by ID."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    return TitleResponse.model_validate(title)


@router.post("/titles", response_model=TitleResponse)
async def create_title(title_data: TitleCreate, db: Session = Depends(get_db)):
    """Create a new title."""
    title = Title(**title_data.model_dump())
    db.add(title)
    db.commit()
    db.refresh(title)
    return TitleResponse.model_validate(title)


@router.put("/titles/{title_id}", response_model=TitleResponse)
async def update_title(
    title_id: int, 
    title_data: TitleUpdate, 
    db: Session = Depends(get_db)
):
    """Update a title."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    
    update_data = title_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(title, field, value)
    
    db.commit()
    db.refresh(title)
    return TitleResponse.model_validate(title)


@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(title_id: int, db: Session = Depends(get_db)):
    """Delete a title."""
    title = db.get(Title, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")
    
    db.delete(title)
    db.commit()
    return None