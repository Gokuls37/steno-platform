# DT-STENO — Stenography Platform

## Deploy on Render.com (Free) — Step by Step

### Step 1: Push these files to GitHub

Your repo should look like this:
```
steno-platform/
├── app.py
├── requirements.txt
├── database/
│   ├── __init__.py
│   └── db.py
└── templates/
    ├── index.html            ← your existing landing page
    ├── student_dashboard.html
    ├── typing_test.html
    └── admin_dashboard.html
```

### Step 2: Create account on Render.com

1. Go to https://render.com → Sign up (free)
2. Connect your GitHub account

### Step 3: Create a new Web Service

1. Click **New +** → **Web Service**
2. Connect your `steno-platform` GitHub repo
3. Fill in these settings:
   - **Name**: dt-steno
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. Add **Environment Variables**:
   - `SECRET_KEY` → any random string (e.g. `mySecretKey2024xyz`)
   - `ADMIN_PASSWORD` → your chosen admin password
5. Click **Create Web Service**

### Step 4: Update index.html

After deploy, Render gives you a URL like `https://dt-steno.onrender.com`

In `index.html`, find this line:
```javascript
const API_BASE = '';
```
Change it to:
```javascript
const API_BASE = 'https://dt-steno.onrender.com';
```

Then commit and push to GitHub.

---

## Default Class Code
A default batch with code **DT2024** is created automatically.
Students register with this code.

## Admin Login
Go to your site → Footer → "Admin"
Password = whatever you set in `ADMIN_PASSWORD` env variable.

## Adding More Batches
Log in as admin → Batches tab → New Batch
Share the class code with your students via WhatsApp.
