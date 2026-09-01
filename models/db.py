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
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'app_v4.db')


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
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        image_url TEXT,
        rating REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cart_id) REFERENCES cart(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        order_status TEXT NOT NULL DEFAULT 'Pending',
        shipping_address TEXT NOT NULL,
        order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        payment_status TEXT NOT NULL DEFAULT 'Completed',
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)
    conn.commit()

    # Seed Default Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from werkzeug.security import generate_password_hash
        pass_123 = generate_password_hash("Password@123")

        # Seed Rajesh Kumar as Admin and Indian Customers
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Rajesh Kumar', 'admin@ecommerce.com', ?, 'admin', '9876543200', 'Connaught Place, New Delhi')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Priya Sharma', 'priya.admin@ecommerce.com', ?, 'admin', '9876543201', 'Bandra West, Mumbai')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Amit Patel', 'amit.patel@example.com', ?, 'customer', '9876543210', 'Navrangpura, Ahmedabad')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Sneha Reddy', 'sneha.reddy@example.com', ?, 'customer', '9876543211', 'Banjara Hills, Hyderabad')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Vikram Singh', 'vikram.singh@example.com', ?, 'customer', '9876543212', 'Sector 17, Chandigarh')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Neha Gupta', 'neha.gupta@example.com', ?, 'customer', '9876543213', 'Indiranagar, Bengaluru')", (pass_123,))
        cursor.execute("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES ('Arjun Nair', 'arjun.nair@example.com', ?, 'customer', '9876543214', 'Kaloor, Kochi')", (pass_123,))

        categories = [
            ("Electronics", "Gadgets, devices, and electronic appliances"),
            ("Fashion - Men", "Apparel, footwear, and accessories for men"),
            ("Fashion - Women", "Apparel, footwear, and accessories for women"),
            ("Home & Kitchen", "Furniture, cookware, decor, and home essentials"),
            ("Books", "Fiction, non-fiction, academic, and self-help books"),
            ("Sports & Fitness", "Fitness gear, sports equipment, and activewear")
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

        products = [
            (1, "Smartphone X Pro 256GB", "6.7-inch AMOLED display, 108MP camera, 5000mAh battery", 49999.00, 45, "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500", 4.7, 1),
            (1, "Wireless Noise-Canceling Headphones", "Active noise cancellation, 30-hour battery life", 14999.00, 30, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500", 4.5, 1),
            (1, "Ultra-Slim 15.6\" Laptop", "Intel i7 13th Gen, 16GB RAM, 512GB SSD", 68999.00, 20, "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500", 4.6, 1),
            (2, "Classic Fit Cotton Polo T-Shirt", "100% breathable pique cotton, ribbed collar", 899.00, 100, "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500", 4.2, 1),
            (2, "Slim Fit Stretch Denim Jeans", "Comfortable stretch fabric, dark indigo wash", 1899.00, 80, "https://images.unsplash.com/photo-1542272604-780c96856592?w=500", 4.4, 1),
            (3, "Floral Print Anarkali Kurta", "Rayon fabric, embroidered neckline, includes dupatta", 1599.00, 90, "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500", 4.6, 1),
            (4, "Non-Stick Cookware Set (3-Piece)", "Teflon coated fry pan, kadai with lid, tawa", 1999.00, 50, "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500", 4.4, 1),
            (5, "Atomic Habits by James Clear", "An easy & proven way to build good habits & break bad ones", 499.00, 120, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500", 4.9, 1),
            (6, "Pro Yoga & Fitness Mat", "Extra thick non-slip eco-TPE exercise mat", 1499.00, 60, "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=500", 4.6, 1)
        ]
        cursor.executemany("INSERT INTO products (category_id, name, description, price, stock, image_url, rating, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", products)

        # Seed sample orders and payments for analytics
        orders_data = [
            (3, 49999.00, 'Delivered', 'Navrangpura, Ahmedabad', '2026-08-10 10:30:00'),
            (4, 14999.00, 'Delivered', 'Banjara Hills, Hyderabad', '2026-08-12 14:20:00'),
            (5, 1899.00, 'Confirmed', 'Sector 17, Chandigarh', '2026-08-15 09:15:00'),
            (6, 1999.00, 'Pending', 'Indiranagar, Bengaluru', '2026-08-20 16:45:00'),
            (7, 499.00, 'Delivered', 'Kaloor, Kochi', '2026-08-25 11:00:00')
        ]

        for u_id, amt, status, addr, dt in orders_data:
            cursor.execute("INSERT INTO orders (user_id, total_amount, order_status, shipping_address, order_date) VALUES (?, ?, ?, ?, ?)", (u_id, amt, status, addr, dt))
            o_id = cursor.lastrowid
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, 1, 1, ?, ?)", (o_id, amt, amt))
            cursor.execute("INSERT INTO payments (order_id, payment_method, transaction_id, amount, payment_status, payment_date) VALUES (?, 'UPI', ?, ?, 'Completed', ?)", (o_id, f"TXN_SEED_{o_id}88", amt, dt))

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

