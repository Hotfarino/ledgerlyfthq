CANONICAL_COLUMNS = [
    "date",
    "description",
    "payee",
    "vendor",
    "memo",
    "amount",
    "debit",
    "credit",
    "balance",
    "category",
    "account",
    "transaction_id",
]

COLUMN_ALIASES = {
    "date": ["date", "txn date", "transaction date", "posted date"],
    "description": ["description", "details", "narrative", "item description"],
    "payee": ["payee", "merchant", "counterparty", "name"],
    "vendor": ["vendor", "supplier"],
    "memo": ["memo", "note", "notes", "reference"],
    "amount": ["amount", "value", "total", "transaction amount"],
    "debit": ["debit", "withdrawal", "outflow", "charge"],
    "credit": ["credit", "deposit", "inflow", "payment"],
    "balance": ["balance", "running balance", "acct balance"],
    "category": ["category", "class", "expense type"],
    "account": ["account", "account name", "gl account"],
    "transaction_id": ["transaction id", "txn id", "id", "reference id", "check #"],
}

REQUIRED_FIELDS = ["date", "amount", "description"]
