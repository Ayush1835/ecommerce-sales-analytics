# ==================================================
# Database Connection Pool
# ==================================================
# Provides a MySQL connection pool for efficient
# database access. Connections are reused from the
# pool rather than created/destroyed per request.
# ==================================================

import mysql.connector
from mysql.connector import pooling, Error
from config import Config


# Initialize connection pool on module import
# Pool size of 10 handles concurrent requests efficiently
try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="ecommerce_pool",
        pool_size=10,
        pool_reset_session=True,
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci',
        autocommit=False
    )
except Error as e:
    print(f"Error creating connection pool: {e}")
    print("Make sure MySQL is running and database 'ecommerce_db' exists.")
    print("Run: mysql -u root -p < database/schema.sql")
    db_pool = None


def get_db_connection():
    """
    Get a connection from the pool.

    Returns:
        MySQLConnection: A database connection from the pool.

    Raises:
        Exception: If the connection pool is not initialized.
    """
    if db_pool is None:
        raise Exception(
            "Database connection pool is not initialized. "
            "Check your MySQL connection settings in .env"
        )
    return db_pool.get_connection()


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Execute a SQL query with automatic connection and cursor management.

    Args:
        query (str): SQL query string with %s placeholders.
        params (tuple): Parameters for the query placeholders.
        fetchone (bool): If True, returns a single row as a dict.
        fetchall (bool): If True, returns all rows as a list of dicts.
        commit (bool): If True, commits the transaction after execution.

    Returns:
        dict | list[dict] | int | None:
            - Single row dict if fetchone=True
            - List of row dicts if fetchall=True
            - Last inserted row ID if commit=True
            - None otherwise

    Raises:
        mysql.connector.Error: On database errors (auto-rollback on commit failure).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())

        if commit:
            conn.commit()
            return cursor.lastrowid

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

        return None

    except Error as e:
        if commit:
            conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()


def execute_transaction(queries):
    """
    Execute multiple queries as a single transaction.

    Args:
        queries (list): List of tuples (query_string, params_tuple).

    Returns:
        bool: True if all queries succeed.

    Raises:
        mysql.connector.Error: On failure (all changes are rolled back).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for query, params in queries:
            cursor.execute(query, params or ())
        conn.commit()
        return True
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
