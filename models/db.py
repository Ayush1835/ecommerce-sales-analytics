# ==================================================
# Database Connection Pool & Cloud SQLite Fallback
# ==================================================
# Provides a MySQL connection pool for efficient
# database access. If MySQL is not available (e.g. cloud hosting),
# it automatically falls back to an SQLite database so live demos work 100%.
# ==================================================

import os
import sqlite3
import mysql.connector
from mysql.connector import pooling, Error
from config import Config

# Initialize connection pool on module import
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
except Exception as e:
    print(f"MySQL Pool Initialization Note: {e}")
    print("Switching to SQLite database fallback for cloud demo deployment...")
    db_pool = None

# SQLite Fallback Path & Setup
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'app_fallback.db')


def init_sqlite_db():
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        phone TEXT,
        address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL DEFAULT 0,
        category_id INTEGER,
        image_url TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        shipping_address TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        payment_method TEXT NOT NULL,
        transaction_id TEXT NOT NULL UNIQUE,
        amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'completed',
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)
    conn.commit()

    # Seed Default Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        admin_pass = generate_password_hash("Admin@123")
        cust_pass = generate_password_hash("Customer@123")

        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('System Admin', 'admin@shopanalytica.com', ?, 'admin')", (admin_pass,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES ('Demo Customer', 'customer@shopanalytica.com', ?, 'customer')", (cust_pass,))

        categories = [
            ("Electronics", "Gadgets and devices"),
            ("Fashion", "Clothing and accessories"),
            ("Home & Kitchen", "Appliances and decor"),
            ("Books", "Printed and digital books"),
            ("Sports", "Fitness and outdoor gear")
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

        products = [
            ("Wireless Noise-Canceling Headphones", "Premium over-ear headphones with 30hr battery life.", 14999.00, 45, 1, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"),
            ("Smart OLED TV 55-inch", "4K Ultra HD Display with Dolby Vision and Gaming Mode.", 54999.00, 20, 1, "https://images.unsplash.com/photo-1593784991095-a205069470b6?w=500"),
            ("Ergonomic Mechanical Keyboard", "RGB Backlit keyboard with tactile blue switches.", 4500.00, 80, 1, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500"),
            ("Men's Tailored Slim Fit Suit", "Italian wool blend suit jacket and trousers.", 8999.00, 35, 2, "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=500"),
            ("Women's Leather Crossbody Bag", "Genuine full-grain leather handbag with gold accents.", 3200.00, 50, 2, "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500"),
            ("Automatic Espresso Coffee Machine", "15-Bar Italian pump with milk frother wand.", 18500.00, 15, 3, "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=500"),
            ("Non-Stick Ceramic Cookware Set", "10-Piece eco-friendly induction pot and pan set.", 6499.00, 40, 3, "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500"),
            ("System Design & Distributed Systems Book", "Hardcover reference for scalable architecture.", 1299.00, 100, 4, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"),
            ("Pro Yoga & Fitness Mat", "Extra thick non-slip eco-TPE exercise mat.", 1499.00, 60, 5, "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=500")
        ]
        cursor.executemany("INSERT INTO products (name, description, price, stock_quantity, category_id, image_url) VALUES (?, ?, ?, ?, ?, ?)", products)

        # Seed initial order and payment for analytics
        cursor.execute("INSERT INTO orders (user_id, total_amount, status, shipping_address) VALUES (2, 14999.00, 'completed', '124 Main St, City')", ())
        order_id = cursor.lastrowid
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, 1, 1, 14999.00, 14999.00)", (order_id,))
        cursor.execute("INSERT INTO payments (order_id, payment_method, transaction_id, amount, status) VALUES (?, 'Credit Card', 'TXN_SEED_999', 14999.00, 'completed')", (order_id,))

        conn.commit()

    conn.close()


if db_pool is None:
    try:
        init_sqlite_db()
    except Exception as sq_err:
        print(f"SQLite Init Note: {sq_err}")


def get_db_connection():
    if db_pool is not None:
        return db_pool.get_connection()
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    conn = get_db_connection()
    is_sqlite = db_pool is None

    if is_sqlite:
        cursor = conn.cursor()
        sql = query.replace('%s', '?')
        sql = sql.replace('NOW()', 'CURRENT_TIMESTAMP')
        sql = sql.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
    else:
        cursor = conn.cursor(dictionary=True)
        sql = query

    try:
        cursor.execute(sql, params or ())

        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            return last_id

        if fetchone:
            row = cursor.fetchone()
            if is_sqlite and row:
                return dict(row)
            return row

        if fetchall:
            rows = cursor.fetchall()
            if is_sqlite and rows:
                return [dict(r) for r in rows]
            return rows

        return None

    except Exception as e:
        if commit:
            conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()


def execute_transaction(queries):
    conn = get_db_connection()
    is_sqlite = db_pool is None

    if is_sqlite:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(dictionary=True)

    try:
        for query, params in queries:
            sql = query.replace('%s', '?') if is_sqlite else query
            cursor.execute(sql, params or ())
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

