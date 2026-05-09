"""
routes/reminders.py — CRUD + random-pick endpoints for reminders.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Category, Reminder
from schemas import (
    CategoryOut,
    MessageResponse,
    ReminderCreate,
    ReminderOut,
    ReminderUpdate,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


# ── GET /reminders ─────────────────────────────────────────────

@router.get("/", response_model=List[ReminderOut])
async def list_reminders(
    active_only: bool = Query(False),
    category_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).options(selectinload(Reminder.category))
    if active_only:
        stmt = stmt.where(Reminder.active == True)
    if category_id is not None:
        stmt = stmt.where(Reminder.category_id == category_id)
    stmt = stmt.order_by(Reminder.id)
    result = await db.execute(stmt)
    return result.scalars().all()


# ── GET /reminders/random ──────────────────────────────────────

@router.get("/random", response_model=ReminderOut)
async def get_random_reminder(
    category_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return one random active reminder (optionally filtered by category)."""
    stmt = (
        select(Reminder)
        .where(Reminder.active == True)
        .options(selectinload(Reminder.category))
        .order_by(func.random())
        .limit(1)
    )
    if category_id is not None:
        stmt = stmt.where(Reminder.category_id == category_id)

    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="No active reminders found.")
    return reminder


# ── GET /reminders/categories ──────────────────────────────────

@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


# ── GET /reminders/{id} ────────────────────────────────────────

@router.get("/{reminder_id}", response_model=ReminderOut)
async def get_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Reminder)
        .where(Reminder.id == reminder_id)
        .options(selectinload(Reminder.category))
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return reminder


# ── POST /reminders ────────────────────────────────────────────

@router.post("/", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_reminder(data: ReminderCreate, db: AsyncSession = Depends(get_db)):
    reminder = Reminder(**data.model_dump())
    db.add(reminder)
    await db.flush()
    await db.refresh(reminder, attribute_names=["category"])
    return reminder


# ── PATCH /reminders/{id} ──────────────────────────────────────

@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)

    await db.flush()
    await db.refresh(reminder, attribute_names=["category"])
    return reminder


# ── DELETE /reminders/{id} ─────────────────────────────────────

@router.delete("/{reminder_id}", response_model=MessageResponse)
async def delete_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    await db.delete(reminder)
    return MessageResponse(message=f"Reminder {reminder_id} deleted.")
