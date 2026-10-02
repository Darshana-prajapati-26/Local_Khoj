# Local Khoj — Quick Start Script (Windows PowerShell)
# Run this from the Local_khoj directory

Write-Host "Starting Local Khoj..." -ForegroundColor Cyan

# Activate virtual environment
& ".venv\Scripts\Activate.ps1"

# Apply any pending migrations
python manage.py migrate --run-syncdb

# Collect static files (skip in dev if already done)
# python manage.py collectstatic --noinput

# Start development server
Write-Host "Server starting at http://localhost:8000" -ForegroundColor Green
python manage.py runserver
