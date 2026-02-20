#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗃️  Collecting static files..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate

echo "👤 Ensuring superuser exists..."
python manage.py ensure_superuser

echo "✅ Build completed successfully!"
