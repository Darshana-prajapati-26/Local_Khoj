# Local Khoj — Deployment Guide

## Local Development (Windows)

```powershell
# 1. Activate venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Run migrations
python manage.py migrate

# 4. Create superuser (first time only)
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

Open: http://localhost:8000

---

## Before Going Live — Checklist

### 1. Configure .env
Copy `.env.example` to `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `SECRET_KEY` | Run: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | Set to `0` |
| `ALLOWED_HOSTS` | Your domain: `yourdomain.com,www.yourdomain.com` |
| `EMAIL_HOST_USER` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (not your login password) |
| `GOOGLE_CLIENT_ID` | [console.cloud.google.com](https://console.cloud.google.com) |
| `GOOGLE_CLIENT_SECRET` | Same as above |
| `RAZORPAY_KEY_ID` | [dashboard.razorpay.com](https://dashboard.razorpay.com/app/keys) |
| `RAZORPAY_KEY_SECRET` | Same as above |

### 2. Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password for "Mail"
4. Use that 16-character password as `EMAIL_HOST_PASSWORD`

### 3. Google OAuth Setup
1. Go to https://console.cloud.google.com
2. Create a project → APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add authorized redirect URI: `https://yourdomain.com/accounts/google/login/callback/`
5. Copy Client ID and Secret to `.env`
6. In Django admin → Sites → update domain to your domain
7. In Django admin → Social Applications → add Google app

### 4. Razorpay Setup
1. Sign up at https://razorpay.com
2. Dashboard → Settings → API Keys → Generate Test Key
3. Add to `.env` (use test keys first, switch to live after testing)

---

## Production Deployment (Railway.app — Free)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/local-khoj.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.app → New Project → Deploy from GitHub
2. Select your repo
3. Add environment variables from your `.env` (set `DEBUG=0`)
4. Railway auto-detects Django and deploys

### Step 3: Add PostgreSQL (free on Railway)
1. Railway dashboard → New → Database → PostgreSQL
2. Copy `DATABASE_URL` to your environment variables
3. Update settings to use `DATABASE_URL` if needed

### Step 4: Collect static files
Railway runs this automatically via `Procfile`:
```
web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn config.wsgi
```

---

## Production Commands

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check for deployment issues
python manage.py check --deploy

# Create cache table (if using DB cache)
python manage.py createcachetable

# Set admin password
python manage.py set_admin_password
```

---

## Architecture Overview

```
Local Khoj/
├── accounts/        — User auth, OTP, profiles
├── core/            — Home, search, dashboard, chat
├── stores/          — Store listings, reviews, favorites
├── products/        — Product catalog
├── services/        — Service listings
├── cart/            — Shopping cart
├── orders/          — Order management, payments
├── vendor_panel/    — Vendor dashboard
├── admin_panel/     — Admin dashboard
├── config/          — Django settings, URLs
├── templates/       — All HTML templates
├── static/          — CSS, JS, images
├── media/           — User-uploaded files
├── .env             — Secrets (never commit this)
└── .env.example     — Template for .env
```
