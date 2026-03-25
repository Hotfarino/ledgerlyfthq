# LedgerLift

LedgerLift is a local-first desktop-style web app for bookkeeping data cleanup workflows. It is built for experienced bookkeepers and accounting specialists who need to normalize messy CSV/XLSX exports, review exceptions, inspect duplicate candidates, apply category rules, and export review-ready output files.

## What LedgerLift Does (Phase 1)

- Imports local CSV and XLSX transaction exports.
- Detects common bookkeeping columns and supports manual column mapping overrides.
- Normalizes dates, payee/vendor text, whitespace/casing, and signed amounts.
- Preserves original row values and logs before/after field changes.
- Flags exceptions requiring human review (missing fields, invalid values, suspicious rows, uncategorized transactions, possible transfers, outliers).
- Detects exact and near duplicates with confidence levels.
- Supports custom category suggestion rules.
- Provides review workflow pages for cleaned data, exceptions, duplicates, and suggestions.
- Exports cleaned CSV/XLSX, exceptions CSV, duplicate review CSV, and summary CSV.

## What LedgerLift Does Not Do (Phase 1)

- No live QuickBooks API integration.
- No automatic final accounting decisions.
- No automatic deletion of duplicate transactions.
- No forced category assignment without user action.
- No multi-user auth/SaaS deployment in this phase.

## Critical Workflow Principle

Accounting judgment remains with the user. LedgerLift surfaces cleaned values, exceptions, and suggestions to accelerate review, but it does not replace professional bookkeeping/accounting judgment.

## Tech Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python, Pandas, openpyxl
- Storage: SQLite (local)
- Files: Local upload and local export only

## Project Structure

```text
LedgerLift/
  desktop/
    main.js
    preload.js
  frontend/
    app/
      dashboard/
      import/
      review/
      exceptions/
      duplicates/
      category-rules/
      export/
      audit-log/
      settings/
    components/
    lib/
  backend/
    app/
    services/
    models/
    parsers/
    rules/
    exporters/
    db/
    mock_data/
  data/
    uploads/
    exports/
```

## Backend API (Phase 1)

- `POST /upload`
- `GET /jobs/{id}/summary`
- `GET /jobs/{id}/rows`
- `GET /jobs/{id}/exceptions`
- `GET /jobs/{id}/duplicates`
- `GET /jobs/{id}/suggestions`
- `POST /jobs/{id}/apply-cleanup`
- `POST /jobs/{id}/apply-category-rules`
- `POST /jobs/{id}/mark-reviewed`
- `GET /jobs/{id}/export/cleaned`
- `GET /jobs/{id}/export/exceptions`
- `GET /jobs/{id}/export/duplicates`
- `GET /jobs/{id}/export/summary`
- `GET /jobs/{id}/audit-log`

## Setup

### 1) Backend

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Frontend

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/frontend
npm install
cp .env.example .env.local
```

Default API base URL in `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Run

### Start backend

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/frontend
npm run dev
```

Open: `http://localhost:3000`

### Start desktop app

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/desktop
npm install
npm run dev
```

The desktop shell opens LedgerLift in an Electron window and targets:

- Frontend: `http://127.0.0.1:3001`
- Backend: `http://127.0.0.1:8000`

If those services are already running, the desktop shell reuses them.

## Sample Data

A sample messy import file is included at:

- `/Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/backend/mock_data/messy_transactions.csv`

Use this file to test import, normalization, exceptions, duplicate detection, category suggestions, and exports.

## Data Models Implemented

- `UploadedFile`
- `TransactionRow`
- `ExceptionFlag`
- `DuplicateGroup`
- `CategoryRule`
- `AuditEntry`
- `ExportJobSummary`

## Future-Ready Roadmap

Phase 1 architecture is modular to support:

- QuickBooks API integration
- bank feed adapters
- reconciliation assistant
- recurring rules engine
- multi-client workspaces
- user login/auth
- SaaS deployment
- AI-assisted categorization
- PDF statement parsing
- monthly close checklist
- client report generator

## Notes for Internal Teams

- LedgerLift separates cleaned data, exception queues, duplicate candidates, and category suggestions.
- Human review is a required workflow step before final accounting usage.
- Export files are generated into `data/exports/` for downstream accounting system import or controlled review.
