"""
services/notifier.py — Dispatch reminders via Email, SMS, and WhatsApp.
Each channel is self-contained. Failures are logged but do not abort others.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ReminderPayload:
    title: str
    body: str
    author: Optional[str]
    category: Optional[str]
    priority: int


@dataclass
class ChannelResult:
    channel: str
    success: bool
    message: str


# ── EMAIL ─────────────────────────────────────────────────────

def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    smtp_tls: bool,
    from_addr: str,
    to_addr: str,
    payload: ReminderPayload,
) -> ChannelResult:
    priority_label = {1: "Low", 2: "Medium", 3: "High"}.get(payload.priority, "Medium")
    subject = f"[Weekly Reminder] {payload.title}"

    # Plain-text body
    plain = (
        f"WEEKLY REMINDER\n"
        f"{'─' * 50}\n"
        f"Category : {payload.category or 'General'}\n"
        f"Priority : {priority_label}\n"
        f"{'─' * 50}\n\n"
        f"{payload.title}\n\n"
        f"{payload.body}\n\n"
        + (f"— {payload.author}\n" if payload.author else "")
    )

    # HTML body
    html = f"""
    <html><body style="font-family: monospace; background:#0f1117; color:#e2e8f0; padding:32px;">
      <div style="max-width:600px; margin:auto; border:1px solid #334155; padding:32px;">
        <p style="color:#F59E0B; font-size:11px; letter-spacing:4px; margin:0 0 24px;">
          WEEKLY REMINDER
        </p>
        <h1 style="font-size:22px; color:#f1f5f9; margin:0 0 8px;">{payload.title}</h1>
        <p style="color:#64748b; font-size:12px; margin:0 0 24px;">
          {payload.category or 'General'} &nbsp;·&nbsp; Priority: {priority_label}
        </p>
        <hr style="border:none; border-top:1px solid #334155; margin:0 0 24px;">
        <p style="line-height:1.8; color:#cbd5e1;">{payload.body}</p>
        {"<p style='color:#64748b; margin-top:24px;'>— " + payload.author + "</p>" if payload.author else ""}
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        if smtp_tls:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, to_addr, msg.as_string())
        else:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, to_addr, msg.as_string())

        logger.info("Email sent to %s", to_addr)
        return ChannelResult("email", True, f"Delivered to {to_addr}")
    except Exception as exc:
        logger.error("Email failed: %s", exc)
        return ChannelResult("email", False, str(exc))


# ── SMS ───────────────────────────────────────────────────────

def send_sms(
    *,
    account_sid: str,
    auth_token: str,
    from_number: str,
    to_number: str,
    payload: ReminderPayload,
) -> ChannelResult:
    try:
        from twilio.rest import Client  # type: ignore

        body = (
            f"[Weekly Reminder]\n"
            f"{payload.title}\n\n"
            f"{payload.body[:300]}"
            + ("\n\n— " + payload.author if payload.author else "")
        )

        client = Client(account_sid, auth_token)
        message = client.messages.create(body=body, from_=from_number, to=to_number)
        logger.info("SMS sent: SID %s", message.sid)
        return ChannelResult("sms", True, f"SID: {message.sid}")
    except ImportError:
        return ChannelResult("sms", False, "twilio package not installed")
    except Exception as exc:
        logger.error("SMS failed: %s", exc)
        return ChannelResult("sms", False, str(exc))


# ── WHATSAPP ──────────────────────────────────────────────────

def send_whatsapp(
    *,
    account_sid: str,
    auth_token: str,
    from_number: str,   # must be "whatsapp:+1xxx"
    to_number: str,     # must be "whatsapp:+91xxx"
    payload: ReminderPayload,
) -> ChannelResult:
    try:
        from twilio.rest import Client  # type: ignore

        body = (
            f"*Weekly Reminder*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"*{payload.title}*\n\n"
            f"{payload.body[:1000]}"
            + ("\n\n— _" + payload.author + "_" if payload.author else "")
        )

        wa_from = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        wa_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"

        client = Client(account_sid, auth_token)
        message = client.messages.create(body=body, from_=wa_from, to=wa_to)
        logger.info("WhatsApp sent: SID %s", message.sid)
        return ChannelResult("whatsapp", True, f"SID: {message.sid}")
    except ImportError:
        return ChannelResult("whatsapp", False, "twilio package not installed")
    except Exception as exc:
        logger.error("WhatsApp failed: %s", exc)
        return ChannelResult("whatsapp", False, str(exc))
