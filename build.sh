#!/usr/bin/env bash
# Render build script for Local Khoj
set -o errexit   # exit on any error

# Upgrade pip and install build tools first
pip install --upgrade pip wheel setuptools

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Create cache table (used when Redis is not configured)
python manage.py createcachetable || true
