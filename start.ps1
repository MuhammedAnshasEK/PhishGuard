# start.ps1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\ml_backend\venv\Scripts\Activate.ps1; cd ml_backend; uvicorn main:app --reload --port 8000"
python -m http.server 5500