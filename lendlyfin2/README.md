# LENDLYFIN V2

## What is this?

A simplified, Google-powered version of Lendlyfin that replaces the complex admin panel with simple Google Sheets and Google Forms.

- **Rates Management**: Edit rates directly in Google Sheets (no admin UI needed)
- **Lead Capture**: Leads come in via Google Form (auto-saved to Google Sheets + your database)
- **Email Notifications**: Get emailed when someone submits a lead
- **Caching**: Rates cached for 1 hour to avoid API limits

---

## Quick Start

**First time?** Read [SETUP_V2.md](./SETUP_V2.md) — it's a step-by-step guide covering:

1. Creating a Google Cloud project & getting API credentials
2. Setting up Google Sheets for rates
3. Creating a Google Form for leads
4. Deploying to Netlify (frontend) + Render (backend)
5. Testing everything end-to-end

**Time:** ~1-2 hours (mostly waiting for services to spin up)

---

## Project Structure

```
lendlyfin2/
├── frontend/              # HTML, CSS, JS (same as V1)
│   ├── index.html
│   ├── compare-loans.html
│   ├── eligibility.html
│   ├── borrowing-power.html
│   ├── api.js            # API client
│   └── ...
├── backend/               # FastAPI backend (Python)
│   ├── app/
│   │   ├── api/
│   │   │   ├── rates.py       # Now fetches from Google Sheets
│   │   │   ├── leads.py       # Handles Google Form webhooks
│   │   │   ├── auth.py
│   │   │   └── calculator.py
│   │   ├── services/
│   │   │   ├── google_sheets_service.py  # NEW: Google Sheets integration
│   │   │   ├── google_forms_service.py   # NEW: Google Forms webhook handler
│   │   │   ├── email_service.py
│   │   │   └── seeder.py
│   │   ├── core/
│   │   │   ├── config.py                 # UPDATED: Google API config
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   └── schemas/
│   ├── requirements.txt    # UPDATED: Added gspread + google-api libs
│   ├── Procfile
│   └── .env.example        # NEW: All env variables documented
├── SETUP_V2.md             # NEW: Complete setup guide
├── README.md               # This file
└── .gitignore
```

---

## Key Changes from V1

| Feature | V1 | V2 |
|---------|----|----|
| Rate updates | Admin UI (rates-admin.html) | Google Sheets |
| Lead capture | Contact form on website | Google Form + webhook |
| Admin panel | Full panel with auth | None (just Sheets + Form) |
| Database | Stores rates + leads | Stores leads + cache only |
| Config | Hardcoded in code | Environment variables |

---

## API Endpoints

### Public

- `GET /api/rates` — Fetch all active rates (from Google Sheets, cached 1 hour)
- `GET /api/health` — Health check

### Public (Form Submission)

- `POST /api/leads/google-form` — Webhook for Google Forms submissions
- `POST /api/leads` — Alternative: Direct form submission

### Protected (Broker/Admin)

- `POST /api/rates/refresh` — Force cache refresh from Google Sheets
- `GET /api/leads` — List all leads (with filtering)
- `GET /api/leads/{id}` — Single lead details
- `PATCH /api/leads/{id}` — Update lead status
- `GET /api/leads/stats` — Dashboard stats

---

## Google Sheets Format

### "Loan Products" Sheet

```
A              B                  C                  D                   E                   F       G
Product Name   Interest Rate (%)  Comparison Rate    Minimum Loan Amount Maximum Loan Amount Lender  Active
Fixed 2yr      5.45              5.50               50000               2000000            BigBank TRUE
Variable       5.20              5.25               50000               2000000            BigBank TRUE
```

To add a new product, just add a row. To remove, set `Active` to `FALSE`.

---

## Environment Variables

See `backend/.env.example` for all variables. Key ones:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_JSON=/path/to/credentials.json
GOOGLE_SHEETS_RATES_ID=1AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWw

# Email
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
BROKER_NOTIFICATION_EMAIL=your@email.com

# CORS
ALLOWED_ORIGINS=https://lendlyfin-v2.netlify.app
```

---

## Deployment

### Frontend (Netlify)

```bash
Base directory:     frontend
Build command:      (leave blank)
Publish directory:  frontend
```

Auto-deploys on every `git push`.

### Backend (Render)

```bash
Root directory:     backend
Runtime:            Python 3
Build command:      pip install -r requirements.txt
Start command:      uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set all environment variables in Render dashboard.

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create .env file with your config
cp .env.example .env
# Edit .env with your actual values

# Run
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
# Open any HTML file in your browser
# Or use a simple server:
python -m http.server 8080
# Then visit http://localhost:8080
```

---

## Troubleshooting

### Rates not loading?
- Check `GOOGLE_SHEETS_CREDENTIALS_JSON` and `GOOGLE_SHEETS_RATES_ID` in your environment
- Verify the service account has **Editor** access to your Google Sheet
- Check Render logs: Render dashboard → Logs tab

### Leads not arriving?
- Verify `BROKER_NOTIFICATION_EMAIL` is correct
- Check `SENDGRID_API_KEY` is valid
- Try submitting through `/api/leads/google-form` endpoint directly

### API errors?
- Check `ALLOWED_ORIGINS` matches your frontend URL
- Verify all required env vars are set
- Check Render logs for Python stack traces

---

## Next Steps

1. **Read** [SETUP_V2.md](./SETUP_V2.md)
2. **Create** Google Cloud project + Service Account
3. **Set up** Google Sheets + Google Form
4. **Deploy** to GitHub → Netlify/Render
5. **Test** end-to-end
6. **Share** your frontend URL

---

## Files to Customize

- `frontend/index.html` — Your main website
- `frontend/api.js` — Update `RENDER_BACKEND_URL` if needed
- `backend/app/core/config.py` — Add any custom settings
- `backend/.env.example` → `backend/.env` — Your secrets

---

## Support

- **Render logs**: Render dashboard → Your service → Logs
- **Netlify logs**: Netlify dashboard → Your site → Deploy logs
- **Google Cloud errors**: Check Google Cloud Console → Logs
- **API docs**: `https://your-backend-url/docs` (in development mode)

---

**Ready?** Start with [SETUP_V2.md](./SETUP_V2.md)!
