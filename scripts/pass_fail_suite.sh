#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
WEB_BASE="${WEB_BASE:-http://127.0.0.1:3001}"

PASS_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "PASS | $1"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "FAIL | $1"
}

run_test() {
  local name="$1"
  shift
  if "$@"; then
    pass "$name"
  else
    fail "$name"
  fi
}

upload_job() {
  local file_path="$1"
  curl -sS -F "file=@${file_path}" "${API_BASE}/upload" | python3 -c 'import sys,json; print(json.load(sys.stdin)["job"]["job_id"])'
}

json_check() {
  local code="$1"
  python3 -c "import sys,json; payload=json.load(sys.stdin); ${code}"
}
export -f json_check

echo "Running ledgerlyftHQ pass/fail suite..."
echo "API: ${API_BASE}"
echo "WEB: ${WEB_BASE}"
echo

run_test "API health endpoint" bash -c "curl -sS '${API_BASE}/health' | json_check \"assert payload.get('status') == 'ok'\""
run_test "Execution guardrails endpoint" bash -c "curl -sS '${API_BASE}/execution/guardrails' | json_check \"assert payload.get('default_mode') == 'isolated'; assert payload.get('allow_legacy_live_send_reuse') is False\""
run_test "Phase 0 report endpoint" bash -c "curl -sS '${API_BASE}/phase0/report?days=60' | json_check \"assert payload.get('lookback_days') == 60; assert 'pain_points' in payload\""

MERGED_FILE="/Users/brandonwilliams/Desktop/LedgerLift/sample_data/merged_test_with_17_duplicates.csv"
JOB_MERGED="$(upload_job "${MERGED_FILE}")"
run_test "Upload merged 17-duplicate dataset" bash -c "[[ -n '${JOB_MERGED}' ]]"
run_test "Merged summary row count is 45" bash -c "curl -sS '${API_BASE}/jobs/${JOB_MERGED}/summary' | json_check \"assert payload.get('total_rows_imported') == 45\""
run_test "Merged dataset has duplicate groups" bash -c "curl -sS '${API_BASE}/jobs/${JOB_MERGED}/duplicates' | json_check \"assert len(payload.get('duplicates', [])) > 0\""

HEADER_FILE="$(mktemp /tmp/ledgerlyfthq_headers_XXXXXX.csv)"
cat > "${HEADER_FILE}" <<'CSV'
Txn Dt,Details,Party,Dr,Cr,Cat,Acct,Memo
2025-01-10,Service fee,Acme,25,,Ops,Checking,fee row
2025-01-11,Refund,Acme,,25,Ops,Checking,refund row
CSV

JOB_HEADERS="$(upload_job "${HEADER_FILE}")"
run_test "Header mismatch upload accepted" bash -c "[[ -n '${JOB_HEADERS}' ]]"
run_test "Header preview includes Txn Dt" bash -c "curl -sS '${API_BASE}/jobs/${JOB_HEADERS}/preview' | json_check \"assert 'Txn Dt' in payload.get('source_headers', [])\""

CLEANUP_PAYLOAD='{"column_mapping":{"date":"Txn Dt","description":"Details","payee":"Party","debit":"Dr","credit":"Cr","category":"Cat","account":"Acct","notes":"Memo"},"execution_mode":"isolated"}'
run_test "Apply cleanup with explicit mapping" bash -c "curl -sS -X POST -H 'Content-Type: application/json' -d '${CLEANUP_PAYLOAD}' '${API_BASE}/jobs/${JOB_HEADERS}/apply-cleanup' | json_check \"assert payload.get('summary', {}).get('total_rows_imported') == 2\""

EDGE_FILE="$(mktemp /tmp/ledgerlyfthq_edges_XXXXXX.csv)"
cat > "${EDGE_FILE}" <<'CSV'
Date,Description,Payee,Amount,Debit,Credit,Category,Account,Notes
,,,,,,, ,lonely note
13/40/2025,Invalid date row,Vendor A,100,,,,Ops,bad date
2025-01-02,Invalid amount row,Vendor B,ABC,,,,Ops,bad amount
2025-01-03,Ambiguous row,Vendor C,,10,10,,Ops,both sides
CSV

JOB_EDGES="$(upload_job "${EDGE_FILE}")"
run_test "Edge-case upload accepted" bash -c "[[ -n '${JOB_EDGES}' ]]"
run_test "Edge exceptions include required flags" bash -c "curl -sS '${API_BASE}/jobs/${JOB_EDGES}/exceptions' | json_check \"flags={e['flag_type'] for e in payload.get('exceptions', [])}; required={'missing_date','invalid_date','invalid_amount','ambiguous_debit_credit','blank_description_payee','malformed_row'}; assert required.issubset(flags)\""

DUP_FILE="$(mktemp /tmp/ledgerlyfthq_dups_XXXXXX.csv)"
cat > "${DUP_FILE}" <<'CSV'
Date,Description,Payee,Amount,Category,Account,Notes
2025-02-01,Office Depot purchase,Office Depot,120,,Ops,one
2025-02-01,Office Depot purchase,Office Depot,120,,Ops,two
2025-02-02,Uber Ride Downtown,Uber,45,,Ops,three
2025-02-02,Uber Ride Downtown!,Uber,45,,Ops,four
CSV

JOB_DUPS="$(upload_job "${DUP_FILE}")"
run_test "Duplicate scenario upload accepted" bash -c "[[ -n '${JOB_DUPS}' ]]"
run_test "Duplicate detection returns exact and likely" bash -c "curl -sS '${API_BASE}/jobs/${JOB_DUPS}/duplicates' | json_check \"types={d['match_type'] for d in payload.get('duplicates', [])}; assert 'exact' in types and 'likely' in types\""
run_test "Duplicate detection does not auto-delete rows" bash -c "curl -sS '${API_BASE}/jobs/${JOB_DUPS}/rows' | json_check \"assert len(payload.get('rows', [])) == 4\""

ROW_ID="$(curl -sS "${API_BASE}/jobs/${JOB_DUPS}/rows" | python3 -c 'import sys,json; print(json.load(sys.stdin)["rows"][0]["row_id"])')"
EXC_ID="$(curl -sS "${API_BASE}/jobs/${JOB_DUPS}/exceptions" | python3 -c 'import sys,json; p=json.load(sys.stdin); print(p["exceptions"][0]["id"] if p["exceptions"] else "")')"
DUP_ID="$(curl -sS "${API_BASE}/jobs/${JOB_DUPS}/duplicates" | python3 -c 'import sys,json; print(json.load(sys.stdin)["duplicates"][0]["id"])')"

run_test "Mark row reviewed" bash -c "curl -sS -X POST -H 'Content-Type: application/json' -d '{\"target\":\"rows\",\"ids\":[\"${ROW_ID}\"],\"review_status\":\"reviewed\"}' '${API_BASE}/jobs/${JOB_DUPS}/mark-reviewed' | json_check \"assert payload.get('updated', 0) >= 1\""
run_test "Row review status persisted" bash -c "curl -sS '${API_BASE}/jobs/${JOB_DUPS}/rows' | json_check \"rows=payload.get('rows', []); hit=[r for r in rows if r['row_id']=='${ROW_ID}']; assert hit and hit[0]['review_status']=='reviewed'\""

if [[ -n "${EXC_ID}" ]]; then
  run_test "Mark exception reviewed" bash -c "curl -sS -X POST -H 'Content-Type: application/json' -d '{\"target\":\"exceptions\",\"ids\":[\"${EXC_ID}\"],\"review_status\":\"reviewed\"}' '${API_BASE}/jobs/${JOB_DUPS}/mark-reviewed' | json_check \"assert payload.get('updated', 0) >= 1\""
fi

run_test "Mark duplicate reviewed" bash -c "curl -sS -X POST -H 'Content-Type: application/json' -d '{\"target\":\"duplicates\",\"ids\":[\"${DUP_ID}\"],\"review_status\":\"reviewed\"}' '${API_BASE}/jobs/${JOB_DUPS}/mark-reviewed' | json_check \"assert payload.get('updated', 0) >= 1\""
run_test "Duplicate reviewed status persisted" bash -c "curl -sS '${API_BASE}/jobs/${JOB_DUPS}/duplicates' | json_check \"dups=payload.get('duplicates', []); hit=[d for d in dups if d['id']=='${DUP_ID}']; assert hit and hit[0]['reviewed'] is True\""

CAT_FILE="$(mktemp /tmp/ledgerlyfthq_category_XXXXXX.csv)"
cat > "${CAT_FILE}" <<'CSV'
Date,Description,Payee,Amount,Category,Account,Notes
2025-03-01,Fuel purchase,Shell,67.42,,Ops,rule target
CSV

JOB_CAT="$(upload_job "${CAT_FILE}")"
run_test "Category suggestion exists for Shell" bash -c "curl -sS '${API_BASE}/jobs/${JOB_CAT}/suggestions' | json_check \"rows=payload.get('rows', []); assert rows and rows[0].get('category_suggestion') == 'Fuel'\""
run_test "Apply category rules persists category" bash -c "curl -sS -X POST -H 'Content-Type: application/json' -d '{\"preview_only\":false,\"execution_mode\":\"isolated\"}' '${API_BASE}/jobs/${JOB_CAT}/apply-category-rules' | json_check \"assert payload.get('summary', {}).get('rows_cleaned') == 1\""
run_test "Category value updated after apply" bash -c "curl -sS '${API_BASE}/jobs/${JOB_CAT}/rows' | json_check \"rows=payload.get('rows', []); assert rows and rows[0].get('category') == 'Fuel'\""

run_test "Export cleaned CSV" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/cleaned?file_type=csv' | grep -qx '200'"
run_test "Export cleaned XLSX" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/cleaned?file_type=xlsx' | grep -qx '200'"
run_test "Export exceptions CSV" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/exceptions' | grep -qx '200'"
run_test "Export duplicates CSV" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/duplicates' | grep -qx '200'"
run_test "Export summary CSV" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/summary' | grep -qx '200'"
run_test "Export audit log CSV" bash -c "curl -sS -o /dev/null -w '%{http_code}' '${API_BASE}/jobs/${JOB_DUPS}/export/audit-log' | grep -qx '200'"

SHARED_GUARD_RESPONSE="$(curl -sS -X POST -H 'Content-Type: application/json' -d '{"column_mapping":{},"execution_mode":"shared_adapter"}' "${API_BASE}/jobs/${JOB_DUPS}/apply-cleanup")"
export SHARED_GUARD_RESPONSE
run_test "Shared adapter mode is guarded" bash -c "python3 -c \"import json, os; p=json.loads(os.environ['SHARED_GUARD_RESPONSE']); assert 'shared_adapter mode is disabled' in p.get('detail','')\""

run_test "Frontend dashboard loads" bash -c "curl -sS '${WEB_BASE}/dashboard' | grep -q 'Dashboard'"
run_test "Frontend review page has Print View" bash -c "curl -sS '${WEB_BASE}/review' | grep -q 'Print View'"
run_test "Frontend audit-log page has Print View" bash -c "curl -sS '${WEB_BASE}/audit-log' | grep -q 'Print View'"
run_test "Frontend phase-0 page loads" bash -c "curl -sS '${WEB_BASE}/phase-0' | grep -q 'Phase 0 Diagnostics'"

echo
echo "Suite complete: PASS=${PASS_COUNT} FAIL=${FAIL_COUNT}"
if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
