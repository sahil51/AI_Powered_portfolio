Write-Host "Setting up AI Executive Assistant..." -ForegroundColor Green

Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Installing dev dependencies..." -ForegroundColor Yellow
pip install -r requirements-dev.txt

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the API server:" -ForegroundColor Cyan
Write-Host "  uvicorn main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "To start Celery worker:" -ForegroundColor Cyan
Write-Host "  celery -A infrastructure.queue.celery_app worker -l info" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  pytest" -ForegroundColor White
