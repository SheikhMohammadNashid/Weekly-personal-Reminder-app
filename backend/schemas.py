"""
schemas.py — Pydantic v2 request/response models.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Category ─────────────────────────────────────────────────

class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    color: str


# ── Reminder ─────────────────────────────────────────────────

class ReminderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: UUID
    title: str
    body: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: int
    active: bool
    send_count: int
    last_sent_at: Optional[datetime] = None
    created_at: datetime
    category: Optional[CategoryOut] = None


class ReminderCreate(BaseModel):
    category_id: Optional[int] = None
    title: str = Field(..., min_length=3, max_length=255)
    body: str = Field(..., min_length=10)
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: int = Field(2, ge=1, le=3)
    active: bool = True


class ReminderUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    body: Optional[str] = Field(None, min_length=10)
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    active: Optional[bool] = None


# ── Notification Config ───────────────────────────────────────

class NotificationConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    enabled: bool
    recipient: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_tls: bool = True
    twilio_account_sid: Optional[str] = None
    twilio_from_number: Optional[str] = None
    send_day: str
    send_time: time
    timezone: str
    updated_at: datetime


class NotificationConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    recipient: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: Optional[bool] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    send_day: Optional[str] = None
    send_time: Optional[time] = None
    timezone: Optional[str] = None


# ── Send History ──────────────────────────────────────────────

class SendHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    status: str
    error_message: Optional[str] = None
    sent_at: datetime
    reminder: Optional[ReminderOut] = None


# ── Generic Responses ─────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class SendResult(BaseModel):
    channel: str
    status: str
    message: Optional[str] = None


class BulkSendResponse(BaseModel):
    reminder: ReminderOut
    results: List[SendResult]
