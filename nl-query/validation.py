import re

FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|MERGE)\b",
    re.IGNORECASE
)

def is_safe_select(sql_query: str) -> bool:
    if sql_query.startswith("ERROR:"):
        return False
    stripped = sql_query.strip().upper()
    if not stripped.startswith("SELECT"):
        return False
    if FORBIDDEN_PATTERN.search(sql_query):
        return False
    return True

def enforce_row_limit(sql_query: str, max_rows: int = 1000) -> str:
    if re.search(r"\bLIMIT\s+\d+", sql_query, re.IGNORECASE):
        return sql_query
    return f"{sql_query.rstrip(';')} LIMIT {max_rows}"