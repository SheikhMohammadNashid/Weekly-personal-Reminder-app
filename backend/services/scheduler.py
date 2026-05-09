"""
services/scheduler.py — APScheduler job that fires weekly,
picks a random reminder from Postgres, and sends it via all
enabled channels.
"""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from config import get_settings
from database import AsyncSessionLocal
from models import NotificationConfig, Reminder, SendHistory
from services.notifier import (
    ReminderPayload,
    send_email,
    send_sms,
    send_whatsapp,
)

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)


async def dispatch_weekly_reminder() -> None:
    """
    Core job:
    1. Pick one random active reminder from the DB.
    2. Load all enabled notification channels.
    3. Dispatch and log results.
    """
    async with AsyncSessionLocal() as db:
        # ── 1. Random active reminder ─────────────────────────
        stmt = (
            select(Reminder)
            .where(Reminder.active == True)
            .options(selectinload(Reminder.category))
            .order_by(func.random())
            .limit(1)
        )
        result = await db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            logger.warning("No active reminders found — skipping dispatch.")
            return

        payload = ReminderPayload(
            title=reminder.title,
            body=reminder.body,
            author=reminder.author,
            category=reminder.category.name if reminder.category else None,
            priority=reminder.priority,
        )

        # ── 2. Load enabled channels ──────────────────────────
        configs_stmt = select(NotificationConfig).where(NotificationConfig.enabled == True)
        configs_result = await db.execute(configs_stmt)
        configs = configs_result.scalars().all()

        if not configs:
            logger.info("No enabled notification channels — skipping.")
            return

        # ── 3. Dispatch ───────────────────────────────────────
        for cfg in configs:
            channel_result = None

            if cfg.channel == "email":
                channel_result = send_email(
                    smtp_host=cfg.smtp_host or settings.SMTP_HOST,
                    smtp_port=cfg.smtp_port or settings.SMTP_PORT,
                    smtp_user=cfg.smtp_user or settings.SMTP_USER,
                    smtp_password=cfg.smtp_password or settings.SMTP_PASSWORD,
                    smtp_tls=cfg.smtp_tls,
                    from_addr=settings.EMAIL_FROM or cfg.smtp_user,
                    to_addr=cfg.recipient or settings.EMAIL_TO,
                    payload=payload,
                )

            elif cfg.channel == "sms":
                channel_result = send_sms(
                    account_sid=cfg.twilio_account_sid or settings.TWILIO_ACCOUNT_SID,
                    auth_token=cfg.twilio_auth_token or settings.TWILIO_AUTH_TOKEN,
                    from_number=cfg.twilio_from_number or settings.TWILIO_FROM_NUMBER,
                    to_number=cfg.recipient or settings.NOTIFICATION_PHONE,
                    payload=payload,
                )

            elif cfg.channel == "whatsapp":
                channel_result = send_whatsapp(
                    account_sid=cfg.twilio_account_sid or settings.TWILIO_ACCOUNT_SID,
                    auth_token=cfg.twilio_auth_token or settings.TWILIO_AUTH_TOKEN,
                    from_number=cfg.twilio_from_number or settings.TWILIO_FROM_NUMBER,
                    to_number=cfg.recipient or settings.NOTIFICATION_PHONE,
                    payload=payload,
                )

            if channel_result:
                db.add(SendHistory(
                    reminder_id=reminder.id,
                    channel=channel_result.channel,
                    status="sent" if channel_result.success else "failed",
                    error_message=None if channel_result.success else channel_result.message,
                ))

        # ── 4. Update reminder metadata ───────────────────────
        await db.execute(
            update(Reminder)
            .where(Reminder.id == reminder.id)
            .values(
                send_count=Reminder.send_count + 1,
                last_sent_at=datetime.utcnow(),
            )
        )
        await db.commit()
        logger.info("Weekly reminder dispatched: '%s'", reminder.title)


def start_scheduler() -> None:
    """Register the weekly job and start the scheduler."""
    day = settings.WEEKLY_SEND_DAY.lower()      # e.g. 'monday'
    hour, minute = settings.WEEKLY_SEND_TIME.split(":")

    scheduler.add_job(
        dispatch_weekly_reminder,
        trigger=CronTrigger(
            day_of_week=day[:3],                # mon, tue, …
            hour=int(hour),
            minute=int(minute),
            timezone=settings.SCHEDULER_TIMEZONE,
        ),
        id="weekly_reminder",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,               # allow 1-hour misfire window
    )
    scheduler.start()
    logger.info(
        "Scheduler started — job fires every %s at %s:%s (%s)",
        day, hour, minute, settings.SCHEDULER_TIMEZONE,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
