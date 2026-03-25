# ledgerlyftHQ V1

`ledgerlyftHQ V1` is a local-first spreadsheet cleanup tool for bookkeeping workflows.
It helps experienced bookkeeping/accounting users clean CSV/XLSX exports faster while keeping human review in control.

## What V1 Does

- Imports local CSV/XLSX files
- Shows first-row preview after upload
- Detects source headers and supports column mapping
- Normalizes row values (date/text/amount/debit/credit)
- Preserves original values for auditability
- Flags exceptions that require review
- Detects exact and likely duplicates
- Exports cleaned data + exceptions + duplicates + summary

## What V1 Does Not Do

- No authentication
- No SaaS billing
- No QuickBooks API integration
- No SAP integration
- No cloud deployment
- No automatic accounting decisions
- No auto-delete of duplicates

## Project Home

This project is now consolidated at:

- `~/Desktop/LedgerLift`

## Project Structure

```text
LedgerLift/
  backend/
    app/
    db/
    exporters/
    models/
    parsers/
    rules/
    services/
    requirements.txt
  frontend/
    app/
      dashboard/
      import/
      column-mapping/
      review/
      exceptions/
      duplicates/
      category-rules/
      export/
      audit-log/
      settings/
    components/
    lib/
  desktop/
    main.js
    preload.js
  sample_data/
  scripts/
  data/
    uploads/
    exports/
```

## Backend API Contract (V1)

- `POST /upload`
- `GET /jobs`
- `GET /dashboard/metrics`
- `GET /execution/guardrails`
- `GET /phase0/report`
- `GET /jobs/{job_id}/preview`
- `GET /jobs/{job_id}/summary`
- `GET /jobs/{job_id}/rows`
- `GET /jobs/{job_id}/exceptions`
- `GET /jobs/{job_id}/duplicates`
- `GET /jobs/{job_id}/suggestions`
- `POST /jobs/{job_id}/apply-cleanup`
- `POST /jobs/{job_id}/apply-category-rules`
- `POST /jobs/{job_id}/mark-reviewed`
- `GET /jobs/{job_id}/audit-log`
- `GET /jobs/{job_id}/export/cleaned`
- `GET /jobs/{job_id}/export/exceptions`
- `GET /jobs/{job_id}/export/duplicates`
- `GET /jobs/{job_id}/export/summary`
- `GET /jobs/{job_id}/export/audit-log`

## V1 Row Contract

`TransactionRow` fields used consistently across backend + frontend:

- `row_id`
- `source_row_index`
- `date`
- `description`
- `payee`
- `amount`
- `debit`
- `credit`
- `category`
- `account`
- `notes`
- `flags`
- `cleaned_values`
- `original_values`
- `review_status`

## Quick Start

### 1) Start backend

```bash
cd ~/Desktop/LedgerLift
./scripts/start_backend.sh
```

Backend URL: `http://127.0.0.1:8000`

### 2) Start frontend

```bash
cd ~/Desktop/LedgerLift
./scripts/start_frontend.sh
```

Frontend URL: `http://127.0.0.1:3001/dashboard`

### Optional: Start desktop shell

```bash
cd ~/Desktop/LedgerLift
./scripts/start_desktop.sh
```

## Manual Install Commands (if preferred)

### Backend

```bash
cd ~/Desktop/LedgerLift/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd ~/Desktop/LedgerLift/frontend
npm install
cp .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3001
```

## Sample Test Files

Located in `~/Desktop/LedgerLift/sample_data`:

- `normal_transactions.csv`
- `normal_transactions.xlsx`
- `messy_transactions.csv`
- `duplicates_and_exceptions.csv`
- `merged_test_with_25_duplicates.csv` (generated test file)

## Build a Merged Test Dataset

Use the helper script to merge multiple files and inject a controlled number of duplicates.

```bash
cd ~/Desktop/LedgerLift
./backend/.venv/bin/python scripts/build_test_dataset.py \
  --inputs sample_data/normal_transactions.csv sample_data/messy_transactions.csv sample_data/duplicates_and_exceptions.csv sample_data/normal_transactions.xlsx \
  --output sample_data/merged_test_with_25_duplicates.csv \
  --duplicate-count 25 \
  --seed 42 \
  --shuffle
```

Adjust `--duplicate-count` to match your target duplicate volume for testing.

## Sample V1 Test Flow

1. Open Import page and upload `messy_transactions.csv`.
2. Verify preview rows render.
3. Go to Column Mapping page, adjust mappings, apply cleanup.
4. Review rows on Cleaned Data Review page.
5. Check Exceptions and Duplicate Review pages.
6. Export cleaned, exceptions, duplicates, and summary files.
7. Export audit log CSV and use Print View on review/audit pages for workpapers.

## Known Limitations (V1)

- Heuristic header detection may need manual mapping for some files.
- Date normalization uses parse heuristics and may require review for ambiguous locales.
- Duplicate logic is deterministic but not exhaustive across all edge cases.
- Category suggestions are rule-based only (no ML in V1).
- `shared_adapter` execution mode is reserved and blocked in V1 to preserve isolation by default.

## Roadmap (Future Versions)

- Improved reconciliation tooling
- Rule versioning and stronger audit controls
- Optional AI-assisted categorization
- Multi-workspace support
- Integrations (kept out of V1 by design)

## Version Boundaries

V1 is intentionally local-first and review-first. Accounting judgment remains with the user.
