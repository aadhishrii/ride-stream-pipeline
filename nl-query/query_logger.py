from db_connection import get_connection
from datetime import datetime

def log_query(question, sql_query, success, retried, error_message, elapsed_ms):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO uber.bronze.text2sql_query_log
            (question, generated_sql, success, retried, error_message, elapsed_ms, logged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (question, sql_query, success, retried, error_message, elapsed_ms, datetime.utcnow())
        )
    finally:
        cursor.close()
        connection.close()