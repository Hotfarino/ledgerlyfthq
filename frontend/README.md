# LedgerLift Frontend (Phase 1)

LedgerLift frontend is a Next.js desktop-style internal UI for bookkeeping cleanup workflows.

## Scope in This Task

This frontend provides:

- Sidebar navigation and page workflow
- Import/upload UI and column-mapping controls
- Cleaned data review table with search/filter actions
- Exceptions and duplicate review pages
- Category rule management UI and suggestions view
- Export action page and audit log page
- Dashboard metrics and recent jobs view

The frontend keeps human review central and does not claim accounting decisions are automated.

## Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

## Run Frontend

```bash
cd /Users/brandonwilliams/Desktop/Toastem/ios/ToastDeezV3/LedgerLift/frontend
npm install
cp .env.example .env.local
npm run dev
```

Open: `http://localhost:3000`

## Production Check

```bash
npm run lint
npm run build
```

## Environment

`.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Pages

- `/dashboard`
- `/import`
- `/review`
- `/exceptions`
- `/duplicates`
- `/category-rules`
- `/export`
- `/audit-log`
- `/settings`

## Active Job Behavior

Frontend uses local storage key `ledgerlift.activeJobId` to persist the selected job across pages.

## Expected API Contract

Frontend expects the following backend routes:

- `POST /upload`
- `GET /jobs`
- `GET /dashboard/metrics`
- `GET /jobs/{id}/summary`
- `GET /jobs/{id}/rows`
- `GET /jobs/{id}/exceptions`
- `GET /jobs/{id}/duplicates`
- `GET /jobs/{id}/suggestions`
- `POST /jobs/{id}/apply-cleanup`
- `POST /jobs/{id}/apply-category-rules`
- `POST /jobs/{id}/mark-reviewed`
- `GET /jobs/{id}/audit-log`
- `GET /jobs/{id}/export/cleaned`
- `GET /jobs/{id}/export/exceptions`
- `GET /jobs/{id}/export/duplicates`
- `GET /jobs/{id}/export/summary`
- `GET /category-rules`
- `POST /category-rules`

## UX Principles

- Workflow-oriented, internal-tool style
- Clear separation of cleaned data, exceptions, duplicates, and suggestions
- Review-first behavior for accounting decisions
