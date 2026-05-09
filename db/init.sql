-- ============================================================
-- REMINDER APP — DATABASE SCHEMA
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── CATEGORIES ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color       VARCHAR(7) DEFAULT '#F59E0B',   -- hex color for UI
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── REMINDERS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reminders (
    id           SERIAL PRIMARY KEY,
    uid          UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    category_id  INT REFERENCES categories(id) ON DELETE SET NULL,
    title        VARCHAR(255) NOT NULL,
    body         TEXT NOT NULL,
    author       VARCHAR(100),                  -- optional attribution
    tags         TEXT[],                        -- e.g. '{productivity,mindset}'
    priority     SMALLINT DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),
                                               -- 1=low 2=medium 3=high
    active       BOOLEAN DEFAULT TRUE,
    send_count   INT DEFAULT 0,                -- how many times it has been sent
    last_sent_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Index for random selection (active only)
CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(active) WHERE active = TRUE;

-- ── NOTIFICATION CONFIG ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS notification_config (
    id               SERIAL PRIMARY KEY,
    channel          VARCHAR(20) NOT NULL UNIQUE,
                                    -- 'email' | 'sms' | 'whatsapp'
    enabled          BOOLEAN DEFAULT FALSE,
    recipient        VARCHAR(255),  -- email address or E.164 phone number
    -- Email-specific
    smtp_host        VARCHAR(255),
    smtp_port        INT,
    smtp_user        VARCHAR(255),
    smtp_password    VARCHAR(255),
    smtp_tls         BOOLEAN DEFAULT TRUE,
    -- Twilio-specific (SMS + WhatsApp)
    twilio_account_sid  VARCHAR(100),
    twilio_auth_token   VARCHAR(100),
    twilio_from_number  VARCHAR(30),  -- E.164, e.g. +12015550123
    -- Schedule
    send_day         VARCHAR(10) DEFAULT 'monday',
                                    -- weekday name
    send_time        TIME DEFAULT '08:00:00',
    timezone         VARCHAR(60) DEFAULT 'Asia/Kolkata',
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── SEND HISTORY ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS send_history (
    id            SERIAL PRIMARY KEY,
    reminder_id   INT REFERENCES reminders(id) ON DELETE SET NULL,
    channel       VARCHAR(20) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
                             -- 'pending' | 'sent' | 'failed'
    error_message TEXT,
    sent_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── TRIGGER: keep updated_at fresh ───────────────────────────
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER reminders_updated_at
    BEFORE UPDATE ON reminders
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER notification_config_updated_at
    BEFORE UPDATE ON notification_config
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ── SEED: default channels (disabled until user configures) ───
INSERT INTO notification_config (channel, enabled, send_day, send_time, timezone)
VALUES
    ('email',    FALSE, 'monday', '08:00:00', 'Asia/Kolkata'),
    ('sms',      FALSE, 'monday', '08:00:00', 'Asia/Kolkata'),
    ('whatsapp', FALSE, 'monday', '08:00:00', 'Asia/Kolkata')
ON CONFLICT (channel) DO NOTHING;
