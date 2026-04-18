# LENDLYFIN V2 — COMPLETE SETUP GUIDE

## Overview

**Lendlyfin V2** = Same mortgage comparison website + **Google Sheets for rates** + **Google Forms for leads**

Instead of managing rates in a database admin panel, you edit them directly in Google Sheets. Leads come in via Google Forms and your backend stores them + sends you emails.

**Total setup time:** 1-2 hours (most of it is waiting for Google/Render to process)

---

## PART 1: GOOGLE SETUP

### Step 1.1 — Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project → name it "Lendlyfin V2"
3. Wait ~30 seconds for it to initialize
4. Select your new project from the dropdown

### Step 1.2 — Enable Google Sheets API

1. In the Cloud Console, search for "Google Sheets API"
2. Click "Enable"
3. Go to "Credentials" on the left sidebar
4. Click "Create Credentials" → "Service Account"
   - Service account name: `lendlyfin-v2-bot`
   - Click "Create and continue"
5. Grant it these roles:
   - **Editor** (broad, but safe for internal tool)
   - Click "Continue"
6. Skip "Grant users access" → Click "Done"

### Step 1.3 — Download Service Account JSON

1. Go to Credentials → Service Accounts
2. Click on `lendlyfin-v2-bot@...`
3. Go to "Keys" tab
4. Click "Add Key" → "Create new key" → **JSON**
5. This downloads a JSON file to your computer
6. **Keep this file safe** — it's your API access key
7. Copy the entire JSON content (we'll paste it into Render later)

### Step 1.4 — Create Google Sheets Document

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet → name it `Lendlyfin V2 - Rates`
3. Rename the first sheet from "Sheet1" to **"Loan Products"**

#### Sheet 1: "Loan Products"

Add these column headers in row 1:
```
A: Product Name
B: Interest Rate (%)
C: Comparison Rate (%)
D: Minimum Loan Amount
E: Maximum Loan Amount
F: Lender
G: Active
```

Add sample data (rows 2-4):
```
Row 2: Fixed 2yr | 5.45 | 5.50 | 50000 | 2000000 | BigBank | TRUE
Row 3: Variable | 5.20 | 5.25 | 50000 | 2000000 | BigBank | TRUE
Row 4: Fixed 3yr | 5.55 | 5.58 | 50000 | 2000000 | Lender2 | TRUE
```

#### Sheet 2: "Eligibility Criteria" (Optional)

Create a second sheet for eligibility rules:
```
A: Criteria Name
B: Min Value
C: Max Value
D: Description
```

Example:
```
Minimum Income | 30000 | | Annual income requirement
Minimum Credit Score | 500 | | Credit score minimum
Maximum LVR | | 95 | Maximum loan-to-value ratio
```

### Step 1.5 — Share Sheet with Service Account

1. In your Google Sheet, click "Share" (top right)
2. Copy the service account email from your JSON file:
   - It looks like: `lendlyfin-v2-bot@lendlyfin-12345.iam.gserviceaccount.com`
3. Paste it into the Share dialog
4. Give it **Editor** access
5. Click "Share"

### Step 1.6 — Get Your Sheet ID

1. In your Google Sheet URL, find the ID:
   ```
   https://docs.google.com/spreadsheets/d/[THIS-IS-YOUR-ID]/edit
   ```
2. Copy that long string (about 44 characters)
3. Save it — you'll need it for the backend config

### Step 1.7 — Create Google Form for Leads

1. Go to [Google Forms](https://forms.google.com)
2. Create a new blank form → name it `Lendlyfin Lead Submission`
3. Add these questions:

| # | Question | Type | Required |
|---|----------|------|----------|
| 1 | Full Name | Short answer | Yes |
| 2 | Email | Email | Yes |
| 3 | Phone Number | Short answer | Yes |
| 4 | Desired Loan Amount | Short answer | Yes |
| 5 | Loan Purpose | Multiple choice | Yes |
|   | Options: Home Purchase / Refinance / Debt Consolidation / Investment / Other | | |
| 6 | Property Type | Multiple choice | Yes |
|   | Options: House / Unit / Land / Off-the-plan / Other | | |
| 7 | Current Credit Score | Multiple choice | Yes |
|   | Options: Excellent / Good / Fair / Poor / Unsure | | |
| 8 | Employment Status | Multiple choice | Yes |
|   | Options: Employed / Self-employed / Retired / Other | | |
| 9 | Additional Notes | Paragraph | No |

4. Click the "Responses" tab
5. Click "Create spreadsheet" → A new Google Sheet will auto-create to store responses
6. You can now share this form URL with people, or set up a webhook

---

## PART 2: DATABASE SETUP

### Option A: Neon (Free PostgreSQL)

1. Go to [Neon](https://neon.tech)
2. Sign up with GitHub
3. Create a new project → name it "lendlyfin2"
4. Choose a region close to Australia (us-west-2)
5. Once created, go to "Connection string" and copy it
6. It looks like: `postgresql://user:pass@ep-xxx.us-west-2.aws.neon.tech/neondb?sslmode=require`
7. This is your `DATABASE_URL` — save it

### Option B: Use Render's PostgreSQL

If deploying on Render, you can skip this and let Render create the DB automatically.

---

## PART 3: EMAIL SETUP (SendGrid)

1. Go to [SendGrid](https://sendgrid.com)
2. Sign up (free tier = 100 emails/day)
3. Go to Settings → API Keys → Create API Key
   - Name: "lendlyfin-v2"
   - Permissions: Full Access
4. Copy the key (starts with `SG.`)
5. This is your `SENDGRID_API_KEY`

---

## PART 4: PREPARE DEPLOYMENT

### Create a GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Repository name: `lendlyfin-v2`
3. Set to **Private**
4. Do **NOT** add README or .gitignore yet
5. Click "Create repository"

### Push Code to GitHub

In your terminal:
```bash
cd /path/to/lendlyfin2

git init
git branch -M main
git add .
git commit -m "Initial Lendlyfin V2 commit"
git remote add origin https://github.com/YOUR-USERNAME/lendlyfin-v2.git
git push -u origin main
```

When prompted for password, use a Personal Access Token:
- Go to https://github.com/settings/tokens/new
- Tick "repo" scope
- Generate → copy → paste as password

---

## PART 5: DEPLOY FRONTEND (Netlify)

1. Go to [Netlify](https://netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Choose "Deploy with GitHub" → authorize → select "lendlyfin-v2"
4. Settings:
   ```
   Base directory:    frontend
   Build command:     (leave blank)
   Publish directory: frontend
   ```
5. Click "Deploy site"

Your frontend URL will be shown (something like `https://lendlyfin-v2.netlify.app`).

---

## PART 6: DEPLOY BACKEND (Render)

1. Go to [Render](https://render.com)
2. Click "New +" → "Web Service"
3. Connect repo: Select "lendlyfin-v2"
4. Settings:
   ```
   Name:              lendlyfin-v2-api
   Root Directory:    backend
   Runtime:           Python 3
   Build Command:     pip install -r requirements.txt
   Start Command:     uvicorn app.main:app --host 0.0.0.0 --port $PORT
   Instance Type:     Free
   ```
5. Scroll to "Environment Variables" and add **ALL** of these:

| Key | Value |
|-----|-------|
| `APP_ENV` | `production` |
| `SECRET_KEY` | Click "Generate" |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `DATABASE_URL` | Paste from Neon (or Render will create) |
| `ADMIN_EMAIL` | `admin@lendlyfin.com.au` |
| `ADMIN_PASSWORD` | Choose a strong password |
| `BROKER_EMAIL` | `broker@lendlyfin.com.au` |
| `BROKER_PASSWORD` | Choose a strong password |
| `SENDGRID_API_KEY` | Paste from SendGrid |
| `EMAIL_FROM` | `hello@lendlyfin.com.au` |
| `EMAIL_FROM_NAME` | `Lendlyfin` |
| `BROKER_NOTIFICATION_EMAIL` | Your personal email |
| `ALLOWED_ORIGINS` | `https://lendlyfin-v2.netlify.app` |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Paste the entire service account JSON (or path) |
| `GOOGLE_SHEETS_RATES_ID` | Paste your sheet ID from Step 1.6 |
| `GOOGLE_SHEETS_CACHE_TTL` | `3600` |
| `GOOGLE_FORMS_WEBHOOK_SECRET` | (Optional — leave empty for now) |

6. Click "Create Web Service"

Render will now build and deploy. Your backend URL will be shown (something like `https://lendlyfin-v2-api.onrender.com`).

---

## PART 7: CONNECT FRONTEND TO BACKEND

1. In your Lendlyfin2 repo, open `frontend/api.js`
2. Find the line:
   ```javascript
   const RENDER_BACKEND_URL = 'https://lendlyfin-v2-api.onrender.com';
   ```
   (Update if Render gave you a different URL)
3. Save and push:
   ```bash
   git add frontend/api.js
   git commit -m "Update backend URL"
   git push
   ```

Netlify auto-deploys in ~30 seconds.

Also update Render's ALLOWED_ORIGINS:
- Render dashboard → lendlyfin-v2-api → Settings → Environment → Update `ALLOWED_ORIGINS` to your actual Netlify URL

---

## PART 8: TEST END-TO-END

### Test 1: Rates Loading

1. Open your frontend: `https://lendlyfin-v2.netlify.app/compare-loans.html`
2. You should see the rates from your Google Sheet
3. If blank, check browser console (F12) for errors

### Test 2: Change a Rate

1. Go to your Google Sheet
2. Change one rate (e.g., 5.45 → 5.99)
3. Refresh the website (might need to wait 1-5 min due to cache)
4. Verify the new rate shows

### Test 3: Submit a Lead via Form

1. Go to your Google Form URL
2. Submit a test response
3. Check the "Responses" sheet in Google Forms — your submission should be there
4. Check your broker notification email — you should receive an email

### Test 4: Check Database

To verify leads are also stored in the database:
1. The form submission endpoint stores leads in Neon
2. If you set up an admin panel, you could view them there
3. For now, just verify the email arrives

---

## PART 9: DAILY WORKFLOW

### Update Rates
1. Open Google Sheet "Lendlyfin V2 - Rates"
2. Edit the rates in the "Loan Products" sheet
3. Website updates automatically (within 1 hour due to cache)
4. To force immediate update: Call `/api/rates/refresh` endpoint

### View Leads
1. Google Form responses appear in Google Sheets automatically
2. You also receive email notifications for each submission
3. Leads are backed up in your Neon database

### Monitor Site
- Netlify dashboard: `https://app.netlify.com` → your site
- Render dashboard: `https://dashboard.render.com` → your backend
- Check logs if something breaks

---

## PART 10: TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Rates show "error" | Check GOOGLE_SHEETS_CREDENTIALS_JSON and GOOGLE_SHEETS_RATES_ID in Render |
| Frontend won't load | Check ALLOWED_ORIGINS in Render matches your Netlify URL |
| Leads not arriving | Check BROKER_NOTIFICATION_EMAIL is valid |
| Google API auth fails | Verify service account is shared with the Google Sheet |
| Slow on first load | Free tier Render sleeps after 15 min idle — normal behavior |

---

## QUICK REFERENCE

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | `https://lendlyfin-v2.netlify.app` | Website |
| Backend API | `https://lendlyfin-v2-api.onrender.com` | API server |
| Database | Neon dashboard | View database |
| Rates Sheet | Google Sheets doc | Edit rates |
| Leads Form | Google Forms URL | Lead capture |
| Render Dashboard | `https://dashboard.render.com` | Backend logs |
| Netlify Dashboard | `https://app.netlify.com` | Frontend logs |

---

## NEXT STEPS

1. ✅ Complete Parts 1-6 above
2. ✅ Run Part 8 tests
3. ✅ Share frontend URL publicly
4. ✅ Monitor lead submissions

**Your Lendlyfin V2 is live!**

---

**Questions?** Check Render logs: Dashboard → lendlyfin-v2-api → Logs
