# ledgerlyftHQ Frontend (V1)

Next.js + TypeScript UI for local spreadsheet cleanup workflows.

## Run

```bash
cd ~/Desktop/LedgerLift/frontend
npm install
cp .env.example .env.local
npm run dev -- --hostname 127.0.0.1 --port 3001
```

Open: `http://127.0.0.1:3001/dashboard`

## Build Checks

```bash
npm run lint
npm run build
```

## Environment

`.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Active Job Storage

The selected job persists in browser localStorage key:

- `ledgerlyfthq.activeJobId`
