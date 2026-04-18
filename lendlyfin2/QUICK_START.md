# LENDLYFIN V2 — QUICK START CHECKLIST

## What You're Getting

✅ A clone of Lendlyfin with:
- Frontend: Same HTML/CSS/JS (ready to deploy)
- Backend: FastAPI + Google Sheets integration (rates from Google Sheets)
- Forms: Webhook endpoint to handle Google Form submissions
- Email: Automated lead notifications via SendGrid

**No database admin panel needed. Everything managed via Google Sheets + Google Forms.**

---

## Folder Structure

```
lendlyfin2/
├── frontend/              ← Website (deploy to Netlify)
├── backend/               ← API (deploy to Render)
│   ├── app/
│   │   ├── services/
│   │   │   ├── google_sheets_service.py   ✨ NEW
│   │   │   ├── google_forms_service.py    ✨ NEW
│   │   │   └── email_service.py           (unchanged)
│   │   ├── api/
│   │   │   ├── rates.py                  🔄 UPDATED (uses Google Sheets)
│   │   │   ├── leads.py                  🔄 UPDATED (Google Forms webhook)
│   │   │   └── ...
│   │   └── core/
│   │       └── config.py                 🔄 UPDATED (Google API config)
│   ├── requirements.txt                  🔄 UPDATED (added gspread, google-api)
│   └── .env.example                      ✨ NEW
├── README.md                             ← Overview
├── SETUP_V2.md                           ← Full setup guide (read this first!)
└── QUICK_START.md                        ← This file
```

---

## 5-Minute Summary

### Before Deployment
1. **Google Cloud**: Create service account, download JSON credentials
2. **Google Sheets**: Create "Lendlyfin V2 - Rates" sheet with loan products
3. **Google Form**: Create "Lendlyfin Lead Submission" form
4. **GitHub**: Push code to private repo
5. **Netlify**: Deploy frontend from GitHub
6. **Render**: Deploy backend, add all environment variables
7. **Test**: Submit a form, change a rate, verify it works

### Daily Workflow
- **To update rates**: Edit Google Sheet
- **To view leads**: Check Google Form responses + email notifications
- **To monitor**: Check Render/Netlify dashboards

---

## Files You MUST Read

1. **[SETUP_V2.md](./SETUP_V2.md)** ← Complete step-by-step setup (REQUIRED)
2. **[README.md](./README.md)** ← Project overview
3. **.env.example** ← Environment variables reference

---

## Files You MIGHT Customize

- **frontend/index.html** — Your branding
- **frontend/api.js** — Backend URL (if different from default)
- **backend/app/core/config.py** — Custom settings
- **backend/app/services/email_service.py** — Email templates

---

## Key API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/rates` | Get all rates from Google Sheets |
| POST | `/api/rates/refresh` | Force cache refresh (admin only) |
| GET | `/api/leads` | List all leads (admin only) |
| POST | `/api/leads/google-form` | Webhook for Google Forms |
| GET | `/api/health` | Health check |

---

## Environment Variables (Render Dashboard)

Must set these in Render for the backend to work:

```
APP_ENV = production
SECRET_KEY = (auto-generate)
DATABASE_URL = postgresql://... (from Neon or Render)
SENDGRID_API_KEY = SG.xxxxx
BROKER_NOTIFICATION_EMAIL = your@email.com
GOOGLE_SHEETS_CREDENTIALS_JSON = (service account JSON)
GOOGLE_SHEETS_RATES_ID = (spreadsheet ID from URL)
ALLOWED_ORIGINS = https://your-netlify-url.netlify.app
```

See **backend/.env.example** for all variables.

---

## Deployment Sequence

1. ✅ GitHub: Push code (`lendlyfin-v2` repo, private)
2. ✅ Netlify: Deploy frontend
   - Base: `frontend`
   - Publish: `frontend`
   - Auto-deploys on every push
3. ✅ Render: Deploy backend
   - Root: `backend`
   - Runtime: Python 3
   - Add all env variables
   - Takes ~3-5 minutes to build
4. ✅ Update frontend's `api.js` with backend URL
5. ✅ Test everything

---

## Testing Checklist

- [ ] Frontend loads at your Netlify URL
- [ ] Rates display on compare-loans.html
- [ ] Edit a rate in Google Sheet → refresh → new rate shows
- [ ] Submit Google Form → you receive notification email
- [ ] Lead appears in database (check `/api/leads` if authenticated)

---

## Troubleshooting

### "Rates not loading"
→ Check `GOOGLE_SHEETS_RATES_ID` and `GOOGLE_SHEETS_CREDENTIALS_JSON` in Render

### "Can't connect to backend"
→ Check `ALLOWED_ORIGINS` in Render matches your Netlify URL

### "Leads not emailing"
→ Check `SENDGRID_API_KEY` and `BROKER_NOTIFICATION_EMAIL` in Render

### "See error in browser"
→ Open DevTools (F12), check Console tab, look for error messages

### "See error in API"
→ Check Render dashboard → Logs tab for Python stack trace

---

## Next Steps

1. Open **[SETUP_V2.md](./SETUP_V2.md)**
2. Follow it step-by-step
3. Come back here if you get stuck
4. Deploy and test

---

## Questions?

All details in **SETUP_V2.md** — it covers:
- Google Cloud & credentials setup
- Creating Google Sheets + Form
- Database setup (Neon)
- Email setup (SendGrid)
- GitHub push
- Netlify + Render deployment
- Testing & troubleshooting

**Time estimate:** 1-2 hours (mostly waiting for services)

**Difficulty:** Medium (lots of copy-paste, straightforward steps)

---

**Ready?** → Open [SETUP_V2.md](./SETUP_V2.md) now!
