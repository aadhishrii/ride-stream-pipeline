from db_connection import get_connection
from text_to_sql import generate_sql
from validation import is_safe_select, enforce_row_limit
from query_logger import log_query
import time

def run_query(question: str):
    start = time.time()
    sql_query = generate_sql(question)

    if not is_safe_select(sql_query):
        log_query(question, sql_query, success=False, retried=False,
                   error_message="Rejected unsafe/invalid query", elapsed_ms=None)
        return {"question": question, "success": False, "error": f"Rejected unsafe/invalid query: {sql_query}"}

    sql_query = enforce_row_limit(sql_query)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(sql_query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        elapsed_ms = round((time.time() - start) * 1000)
        log_query(question, sql_query, success=True, retried=False,
                   error_message=None, elapsed_ms=elapsed_ms)
        return {
            "question": question, "sql": sql_query, "columns": columns,
            "results": rows, "success": True, "retried": False, "elapsed_ms": elapsed_ms
        }
    except Exception as e:
        retry_prompt = f"{question}\n\nThe previous query failed with error: {e}\nPrevious query: {sql_query}\nFix it."
        retry_sql = generate_sql(retry_prompt)
        if not is_safe_select(retry_sql):
            log_query(question, retry_sql, success=False, retried=True,
                       error_message="Retry also unsafe/invalid", elapsed_ms=None)
            return {"question": question, "success": False, "error": f"Retry also unsafe/invalid: {retry_sql}"}
        retry_sql = enforce_row_limit(retry_sql)
        try:
            cursor.execute(retry_sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            elapsed_ms = round((time.time() - start) * 1000)
            log_query(question, retry_sql, success=True, retried=True,
                       error_message=None, elapsed_ms=elapsed_ms)
            return {
                "question": question, "sql": retry_sql, "columns": columns,
                "results": rows, "success": True, "retried": True, "elapsed_ms": elapsed_ms
            }
        except Exception as e2:
            log_query(question, retry_sql, success=False, retried=True,
                       error_message=str(e2), elapsed_ms=None)
            return {"question": question, "success": False, "error": str(e2), "failed_sql": retry_sql}
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    test_questions = [
        "which pickup city had the most rides",
        "what is the average tip amount by payment method",
        "show me the top 5 drivers by rating",
        "how many rides were paid by card"
    ]
    for q in test_questions:
        result = run_query(q)
        print(f"Q: {q} → success={result['success']}")