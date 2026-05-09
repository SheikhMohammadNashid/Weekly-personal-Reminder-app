"""
models.py — SQLAlchemy ORM models matching db/init.sql exactly.
"""
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, SmallInteger, String, Text, Time, ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(100), nullable=False, unique=True)
    description: Optional[str] = Column(Text)
    color: str = Column(String(7), default="#F59E0B")
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

    reminders = relationship("Reminder", back_populates="category")


class Reminder(Base):
    __tablename__ = "reminders"

    id: int = Column(Integer, primary_key=True, index=True)
    uid: uuid.UUID = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    category_id: Optional[int] = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    title: str = Column(String(255), nullable=False)
    body: str = Column(Text, nullable=False)
    author: Optional[str] = Column(String(100))
    tags: Optional[List[str]] = Column(ARRAY(String))
    priority: int = Column(SmallInteger, default=2)
    active: bool = Column(Boolean, default=True)
    send_count: int = Column(Integer, default=0)
    last_sent_at: Optional[datetime] = Column(DateTime(timezone=True))
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="reminders")
    send_history = relationship("SendHistory", back_populates="reminder")


class NotificationConfig(Base):
    __tablename__ = "notification_config"

    id: int = Column(Integer, primary_key=True, index=True)
    channel: str = Column(String(20), nullable=False, unique=True)
    enabled: bool = Column(Boolean, default=False)
    recipient: Optional[str] = Column(String(255))
    # Email
    smtp_host: Optional[str] = Column(String(255))
    smtp_port: Optional[int] = Column(Integer)
    smtp_user: Optional[str] = Column(String(255))
    smtp_password: Optional[str] = Column(String(255))
    smtp_tls: bool = Column(Boolean, default=True)
    # Twilio
    twilio_account_sid: Optional[str] = Column(String(100))
    twilio_auth_token: Optional[str] = Column(String(100))
    twilio_from_number: Optional[str] = Column(String(30))
    # Schedule
    send_day: str = Column(String(10), default="monday")
    send_time = Column(Time, default="08:00:00")
    timezone: str = Column(String(60), default="Asia/Kolkata")
    updated_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SendHistory(Base):
    __tablename__ = "send_history"

    id: int = Column(Integer, primary_key=True, index=True)
    reminder_id: Optional[int] = Column(Integer, ForeignKey("reminders.id", ondelete="SET NULL"))
    channel: str = Column(String(20), nullable=False)
    status: str = Column(String(20), nullable=False, default="pending")
    error_message: Optional[str] = Column(Text)
    sent_at: datetime = Column(DateTime(timezone=True), server_default=func.now())

    reminder = relationship("Reminder", back_populates="send_history")
