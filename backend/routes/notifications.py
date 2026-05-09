"""
routes/notifications.py — Configure channels, trigger manual sends, view history.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import NotificationConfig, Reminder, SendHistory
from schemas import (
    BulkSendResponse,
    NotificationConfigOut,
    NotificationConfigUpdate,
    SendHistoryOut,
    SendResult,
)
from services.notifier import ReminderPayload, send_email, send_sms, send_whatsapp
from services.scheduler import dispatch_weekly_reminder

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── GET /notifications/config ──────────────────────────────────

@router.get("/config", response_model=List[NotificationConfigOut])
async def get_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NotificationConfig).order_by(NotificationConfig.channel)
    )
    return result.scalars().all()


# ── PATCH /notifications/config/{channel} ─────────────────────

@router.patch("/config/{channel}", response_model=NotificationConfigOut)
async def update_config(
    channel: str,
    data: NotificationConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationConfig).where(NotificationConfig.channel == channel)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Channel '{channel}' not found.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)

    await db.flush()
    await db.refresh(cfg)
    return cfg


# ── POST /notifications/send-now ──────────────────────────────

@router.post("/send-now", response_model=BulkSendResponse)
async def send_now(
    reminder_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a send.
    - If reminder_id is supplied, send that specific reminder.
    - Otherwise pick a random one (same logic as the weekly job).
    """
    from sqlalchemy import func as sqlfunc

    if reminder_id:
        stmt = (
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .options(selectinload(Reminder.category))
        )
    else:
        stmt = (
            select(Reminder)
            .where(Reminder.active == True)
            .options(selectinload(Reminder.category))
            .order_by(sqlfunc.random())
            .limit(1)
        )

    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="No reminder found.")

    payload = ReminderPayload(
        title=reminder.title,
        body=reminder.body,
        author=reminder.author,
        category=reminder.category.name if reminder.category else None,
        priority=reminder.priority,
    )

    configs_result = await db.execute(
        select(NotificationConfig).where(NotificationConfig.enabled == True)
    )
    configs = configs_result.scalars().all()

    results: List[SendResult] = []

    for cfg in configs:
        channel_result = None

        if cfg.channel == "email":
            channel_result = send_email(
                smtp_host=cfg.smtp_host or "",
                smtp_port=cfg.smtp_port or 587,
                smtp_user=cfg.smtp_user or "",
                smtp_password=cfg.smtp_password or "",
                smtp_tls=cfg.smtp_tls,
                from_addr=cfg.smtp_user or "",
                to_addr=cfg.recipient or "",
                payload=payload,
            )
        elif cfg.channel == "sms":
            channel_result = send_sms(
                account_sid=cfg.twilio_account_sid or "",
                auth_token=cfg.twilio_auth_token or "",
                from_number=cfg.twilio_from_number or "",
                to_number=cfg.recipient or "",
                payload=payload,
            )
        elif cfg.channel == "whatsapp":
            channel_result = send_whatsapp(
                account_sid=cfg.twilio_account_sid or "",
                auth_token=cfg.twilio_auth_token or "",
                from_number=cfg.twilio_from_number or "",
                to_number=cfg.recipient or "",
                payload=payload,
            )

        if channel_result:
            from models import SendHistory as SH
            db.add(SH(
                reminder_id=reminder.id,
                channel=channel_result.channel,
                status="sent" if channel_result.success else "failed",
                error_message=None if channel_result.success else channel_result.message,
            ))
            results.append(SendResult(
                channel=channel_result.channel,
                status="sent" if channel_result.success else "failed",
                message=channel_result.message,
            ))

    if not results:
        results.append(SendResult(
            channel="none",
            status="skipped",
            message="No channels are enabled. Configure notifications first.",
        ))

    await db.flush()
    return BulkSendResponse(reminder=reminder, results=results)


# ── GET /notifications/history ─────────────────────────────────

@router.get("/history", response_model=List[SendHistoryOut])
async def get_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SendHistory)
        .options(selectinload(SendHistory.reminder).selectinload(Reminder.category))
        .order_by(SendHistory.sent_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
