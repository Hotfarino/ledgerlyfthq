# ledgerlyftHQ Backend (V1)

FastAPI service for local CSV/XLSX cleanup, exception flagging, duplicate detection, and export.

## Run

```bash
cd ~/Desktop/LedgerLift/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API health:

- `http://127.0.0.1:8000/health`
