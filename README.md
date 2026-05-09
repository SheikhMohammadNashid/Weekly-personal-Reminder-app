# REMINDR — Weekly Dispatch System

A self-hosted weekly reminder app. Each week a random reminder is pulled from
PostgreSQL and dispatched via **Email**, **SMS**, and/or **WhatsApp**.

---

## Project Structure

```
reminder-app/
├── db/
│   ├── init.sql            ← Schema: tables, indexes, triggers
│   └── reminders_data.sql  ← Seed data (add more reminders here easily)
│
├── backend/
│   ├── main.py             ← FastAPI app entry point
│   ├── config.py           ← Settings from .env
│   ├── database.py         ← Async SQLAlchemy engine
│   ├── models.py           ← ORM models
│   ├── schemas.py          ← Pydantic v2 schemas
│   ├── routes/
│   │   ├── reminders.py    ← CRUD + random-pick endpoints
│   │   └── notifications.py← Config + manual dispatch + history
│   ├── services/
│   │   ├── notifier.py     ← Email / SMS / WhatsApp dispatch logic
│   │   └── scheduler.py    ← APScheduler weekly cron job
│   ├── requirements.txt
│   └── .env.example        ← Copy to .env and fill in values
│
└── frontend/
    ├── index.html          ← Dashboard UI
    ├── style.css           ← Dark command-center styles
    └── app.js              ← All API calls and interactions
```

---

## Quick Start (Local Development)

### 1 — Database

```bash
# Start PostgreSQL (or use Docker)
docker run -d --name pg \
  -e POSTGRES_DB=reminders \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:16-alpine

# Load schema then seed data
psql -h localhost -U postgres -d reminders -f db/init.sql
psql -h localhost -U postgres -d reminders -f db/reminders_data.sql
```

### 2 — Backend

```bash
cd backend
cp .env.example .env          # fill in your SMTP / Twilio credentials
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3 — Frontend

No build step required. Serve with any static server:

```bash
cd frontend
python -m http.server 5173    # or: npx serve .
```

Open http://localhost:5173

---

## Adding More Reminders

1. Open `db/reminders_data.sql`
2. Add a new `INSERT INTO reminders (...)` row following the existing pattern
3. Run against the database:
   ```bash
   psql -h localhost -U postgres -d reminders -f db/reminders_data.sql
   ```
   (Existing rows are unaffected — inserts are additive)

Or use the **+ ADD** button in the frontend Reminder Bank tab.

---

## Notification Setup

### Email (Gmail)
1. Enable 2FA on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Set `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO` in `.env`

### SMS & WhatsApp (Twilio)
1. Create a free account at https://www.twilio.com
2. Get a Twilio phone number (SMS) or join the WhatsApp sandbox
3. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` in `.env`

Then enable each channel in the **Channels** tab of the dashboard.

---

## API Reference

| Method | Endpoint                          | Description                  |
|--------|-----------------------------------|------------------------------|
| GET    | /api/reminders/                   | List all reminders           |
| GET    | /api/reminders/random             | Get one random active        |
| GET    | /api/reminders/categories         | List categories              |
| POST   | /api/reminders/                   | Create reminder              |
| PATCH  | /api/reminders/{id}               | Update reminder              |
| DELETE | /api/reminders/{id}               | Delete reminder              |
| GET    | /api/notifications/config         | Get all channel configs      |
| PATCH  | /api/notifications/config/{ch}    | Update channel (email/sms/wa)|
| POST   | /api/notifications/send-now       | Manual dispatch              |
| GET    | /api/notifications/history        | Send log (last 50)           |
| GET    | /health                           | Health check                 |

---

