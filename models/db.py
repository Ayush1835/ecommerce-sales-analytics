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
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'app_v8.db')


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

        # Seed Admins & 17 Indian Customers
        users_list = [
            ('Rajesh Kumar', 'admin@ecommerce.com', pass_123, 'admin', '9876543200', 'Connaught Place, New Delhi 110001'),
            ('Priya Sharma', 'priya.admin@ecommerce.com', pass_123, 'admin', '9876543201', 'Bandra West, Mumbai 400050'),
            ('Amit Patel', 'amit.patel@example.com', pass_123, 'customer', '9876543210', 'Navrangpura, Ahmedabad, Gujarat 380009'),
            ('Sneha Reddy', 'sneha.reddy@example.com', pass_123, 'customer', '9876543211', 'Banjara Hills, Hyderabad, Telangana 500034'),
            ('Vikram Singh', 'vikram.singh@example.com', pass_123, 'customer', '9876543212', 'Sector 17, Chandigarh, Punjab 160017'),
            ('Neha Gupta', 'neha.gupta@example.com', pass_123, 'customer', '9876543213', 'Indiranagar, Bengaluru, Karnataka 560038'),
            ('Arjun Nair', 'arjun.nair@example.com', pass_123, 'customer', '9876543214', 'Kaloor, Kochi, Kerala 682017'),
            ('Ananya Chatterjee', 'ananya.c@example.com', pass_123, 'customer', '9876543215', 'Salt Lake, Kolkata, West Bengal 700091'),
            ('Rohan Verma', 'rohan.verma@example.com', pass_123, 'customer', '9876543216', 'Connaught Place, New Delhi 110001'),
            ('Kavya Joshi', 'kavya.joshi@example.com', pass_123, 'customer', '9876543217', 'Kothrud, Pune, Maharashtra 411038'),
            ('Siddharth Rao', 'siddharth.rao@example.com', pass_123, 'customer', '9876543218', 'T. Nagar, Chennai, Tamil Nadu 600017'),
            ('Riya Shah', 'riya.shah@example.com', pass_123, 'customer', '9876543219', 'Marine Drive, Mumbai, Maharashtra 400020'),
            ('Aditya Malhotra', 'aditya.m@example.com', pass_123, 'customer', '9876543220', 'Civil Lines, Jaipur, Rajasthan 302006'),
            ('Pooja Deshmukh', 'pooja.d@example.com', pass_123, 'customer', '9876543221', 'Viman Nagar, Pune, Maharashtra 411014')
        ]
        cursor.executemany("INSERT INTO users (name, email, password_hash, role, phone, address) VALUES (?, ?, ?, ?, ?, ?)", users_list)

        categories = [
            ('Electronics', 'Gadgets, devices, and electronic appliances'),
            ('Fashion - Men', 'Apparel, footwear, and accessories for men'),
            ('Fashion - Women', 'Apparel, footwear, and accessories for women'),
            ('Home & Kitchen', 'Furniture, cookware, decor, and home essentials'),
            ('Books', 'Fiction, non-fiction, academic, and self-help books'),
            ('Sports & Fitness', 'Fitness gear, sports equipment, and activewear'),
            ('Beauty & Personal Care', 'Skincare, haircare, cosmetics, and grooming'),
            ('Grocery & Gourmet', 'Daily essentials, snacks, beverages, and organic foods'),
            ('Toys & Games', 'Board games, action figures, and educational toys'),
            ('Automotive', 'Car accessories, bike care, and vehicle electronics'),
            ('Mobile Accessories', 'Cases, chargers, screen protectors, and power banks'),
            ('Stationery & Office', 'Notebooks, pens, desk organizers, and office supplies')
        ]
        cursor.executemany("INSERT INTO categories (name, description) VALUES (?, ?)", categories)

        products = [
            # 1. Electronics
            (1, 'Smartphone X Pro 256GB', '6.7-inch AMOLED display, 108MP camera, 5000mAh battery', 49999.00, 45, 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500', 4.7, 1),
            (1, 'Wireless Noise-Canceling Headphones', 'Active noise cancellation, 30-hour battery life', 14999.00, 30, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500', 4.5, 1),
            (1, 'Ultra-Slim 15.6" Laptop', 'Intel i7 13th Gen, 16GB RAM, 512GB SSD', 68999.00, 20, 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500', 4.6, 1),
            (1, 'Smartwatch Series 5', 'Heart rate monitor, GPS, AMOLED display', 8999.00, 60, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500', 4.3, 1),
            (1, '4K Ultra HD Smart TV 55"', 'Dolby Vision, HDR10+, Android TV with voice remote', 42999.00, 15, 'https://images.unsplash.com/photo-1593784991095-a205069470b6?w=500', 4.8, 1),

            # 2. Fashion - Men
            (2, 'Classic Fit Cotton Polo T-Shirt', '100% breathable pique cotton, ribbed collar', 899.00, 100, 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500', 4.2, 1),
            (2, 'Slim Fit Stretch Denim Jeans', 'Comfortable stretch fabric, dark indigo wash', 1899.00, 80, 'https://images.unsplash.com/photo-1542272604-780c96856592?w=500', 4.4, 1),
            (2, 'Casual Canvas Sneakers', 'Durable canvas upper, cushioned footbed', 1499.00, 50, 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=500', 4.1, 1),
            (2, 'Formal Leather Dress Shoes', 'Genuine leather, handcrafted oxford design', 3499.00, 35, 'https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=500', 4.5, 1),
            (2, 'Windproof Bomber Jacket', 'Lightweight polyester fabric with zip pockets', 2499.00, 40, 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=500', 4.3, 1),

            # 3. Fashion - Women
            (3, 'Floral Print Anarkali Kurta', 'Rayon fabric, embroidered neckline, includes dupatta', 1599.00, 90, 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500', 4.6, 1),
            (3, 'High-Waist Skinny Jeans', 'Super stretch denim, five-pocket style', 1799.00, 75, 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500', 4.3, 1),
            (3, 'Structured Leather Tote Bag', 'Spacious compartment with zipper closure', 2299.00, 45, 'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500', 4.7, 1),
            (3, 'Block Heel Sandals', 'Comfortable 2-inch block heel, ankle strap', 1299.00, 60, 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=500', 4.2, 1),
            (3, 'Chiffon Evening Maxi Dress', 'Elegant A-line silhouette, ruffled sleeves', 2799.00, 30, 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500', 4.5, 1),

            # 4. Home & Kitchen
            (4, 'Non-Stick Cookware Set (3-Piece)', 'Teflon coated fry pan, kadai with lid, tawa', 1999.00, 50, 'https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=500', 4.4, 1),
            (4, 'Ergonomic Mesh Office Chair', 'Adjustable lumbar support, tilt mechanism', 6499.00, 25, 'https://images.unsplash.com/photo-1580481072645-022f9a6d8310?w=500', 4.5, 1),
            (4, 'Stainless Steel Electric Kettle 1.5L', 'Auto shut-off, boil-dry protection, 1500W', 999.00, 85, 'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=500', 4.3, 1),
            (4, 'Cotton Queen Size Bed Sheet Set', '300 TC 100% cotton, includes 2 pillow covers', 1199.00, 70, 'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=500', 4.2, 1),
            (4, 'Air Fryer 4.2L Digital', '8 preset modes, 360-degree rapid air heating', 5999.00, 30, 'https://images.unsplash.com/photo-1585515320310-259814833e62?w=500', 4.7, 1),

            # 5. Books
            (5, 'Atomic Habits by James Clear', 'An easy & proven way to build good habits & break bad ones', 499.00, 120, 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500', 4.9, 1),
            (5, 'The Psychology of Money', 'Timeless lessons on wealth, greed, and happiness', 399.00, 150, 'https://images.unsplash.com/photo-1592496001020-d31bd830651f?w=500', 4.8, 1),
            (5, 'Ikigai: The Japanese Secret', 'Discover your purpose and live longer, happier', 350.00, 110, 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=500', 4.6, 1),
            (5, 'Rich Dad Poor Dad', 'What the rich teach their kids about money', 420.00, 95, 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500', 4.7, 1),
            (5, 'Deep Work by Cal Newport', 'Rules for focused success in a distracted world', 450.00, 80, 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=500', 4.5, 1),

            # 6. Sports & Fitness
            (6, 'Yoga Mat 6mm Eco-Friendly TPE', 'Non-slip surface, includes carrying strap', 799.00, 90, 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=500', 4.4, 1),
            (6, 'Adjustable Dumbbell Set 20kg', 'Chrome-plated weight plates with star lock collars', 3499.00, 35, 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=500', 4.6, 1),
            (6, 'Resistance Bands Loop Set (5 Levels)', '100% natural latex for stretching & strength', 499.00, 130, 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=500', 4.3, 1),
            (6, 'Badminton Racket Twin Pack', 'Aluminum frame, includes 3 nylon shuttlecocks', 1199.00, 60, 'https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?w=500', 4.2, 1),
            (6, 'Sipper Water Bottle 1L Stainless Steel', 'Insulated vacuum flask keeps water cold 24h', 699.00, 85, 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500', 4.5, 1),

            # 7. Beauty & Personal Care
            (7, 'Vitamin C Face Serum 30ml', 'Brightening serum with hyaluronic acid', 599.00, 110, 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500', 4.6, 1),
            (7, 'Organic Argan Oil Shampoo 300ml', 'Sulfate-free, restores shine and repair damage', 449.00, 95, 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=500', 4.3, 1),
            (7, 'Matte Liquid Lipstick Set (4 Pcs)', 'Long-lasting, waterproof, transfer-proof formula', 899.00, 70, 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500', 4.4, 1),
            (7, 'Electric Beard Trimmer for Men', 'Self-sharpening stainless blades, 60-min runtime', 1299.00, 55, 'https://images.unsplash.com/photo-1621607512214-68297480165e?w=500', 4.5, 1),
            (7, 'Sunscreen Gel SPF 50 PA++++', 'Non-greasy, zero white cast, broad spectrum', 399.00, 140, 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500', 4.7, 1),

            # 8. Grocery & Gourmet
            (8, 'Organic Green Tea 100 Tea Bags', 'Antioxidant-rich whole leaf green tea', 349.00, 160, 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500', 4.5, 1),
            (8, 'Raw Unfiltered Honey 500g', '100% pure honey with natural enzymes', 299.00, 120, 'https://images.unsplash.com/photo-1587049352847-4a222e784d38?w=500', 4.6, 1),
            (8, 'California Almonds 500g Pack', 'Premium quality, crunchy and nutritious', 499.00, 100, 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=500', 4.7, 1),
            (8, 'Extra Virgin Olive Oil 1L', 'Cold-pressed, ideal for salads and cooking', 899.00, 65, 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500', 4.4, 1),
            (8, 'Dark Chocolate 70% Cocoa 100g', 'Rich gourmet Belgian dark chocolate bar', 199.00, 180, 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=500', 4.8, 1),

            # 9. Toys & Games
            (9, 'Monopoly Classic Board Game', 'Fast-dealing property trading board game for family', 999.00, 45, 'https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=500', 4.7, 1),
            (9, 'Rubik Cube 3x3 Speed Cube', 'Smooth stickerless speed cube for brain exercise', 299.00, 150, 'https://images.unsplash.com/photo-1591994843349-f415893b3a6b?w=500', 4.5, 1),
            (9, 'Building Blocks Set 500 Pieces', 'Compatible classic brick set for creative play', 1499.00, 40, 'https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=500', 4.6, 1),
            (9, 'Remote Control Stunt Car', '360-degree rotating double-sided flip car', 1199.00, 50, 'https://images.unsplash.com/photo-1594787318286-3d835c1d207f?w=500', 4.3, 1),
            (9, 'Wooden Chess Set Foldable', 'Handcrafted magnetic chess board with storage', 899.00, 60, 'https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=500', 4.8, 1),

            # 10. Automotive
            (10, 'High-Pressure Car Washer Pump', '1800W motor, 120 bar pressure nozzle', 4999.00, 20, 'https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?w=500', 4.4, 1),
            (10, 'Car Dashboard Phone Mount', '360-degree rotation, strong suction cup', 399.00, 110, 'https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=500', 4.2, 1),
            (10, 'Microfiber Cloth Pack of 4', '800 GSM plush car detailing drying towels', 499.00, 140, 'https://images.unsplash.com/photo-1607860108855-64acf2078ed9?w=500', 4.6, 1),
            (10, 'Digital Tyre Inflator Portable', '12V DC auto cutoff air compressor with LED', 1899.00, 35, 'https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=500', 4.5, 1),
            (10, 'Car Vacuum Cleaner High Power', '12V 120W wet & dry car hand vacuum', 1199.00, 55, 'https://images.unsplash.com/photo-1558317374-067fb5f30001?w=500', 4.3, 1),

            # 11. Mobile Accessories
            (11, 'Fast Charging Power Bank 20000mAh', '22.5W two-way fast charge, triple output', 1699.00, 75, 'https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=500', 4.5, 1),
            (11, 'Braided Type-C to Type-C Cable 2m', '100W PD fast charging, 10000+ bend lifespan', 399.00, 160, 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500', 4.4, 1),
            (11, 'Magnetic Wireless Charger 15W', 'MagSafe compatible for iPhone and Android', 999.00, 50, 'https://images.unsplash.com/photo-1622445268465-843d6135815a?w=500', 4.3, 1),
            (11, 'Bluetooth Selfie Stick Tripod', 'Detachable wireless remote, extendable 100cm', 599.00, 90, 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500', 4.2, 1),
            (11, 'Universal Waterproof Phone Pouch', 'IPX8 certified pouch with neck strap', 249.00, 200, 'https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=500', 4.6, 1),

            # 12. Stationery & Office
            (12, 'Executive Leather Journal Notebook', '200 thick unruled pages, ribbon bookmark', 599.00, 80, 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500', 4.6, 1),
            (12, 'Gel Pen Pack of 10 (Blue & Black)', 'Smooth 0.5mm tip, quick-dry smudge-proof ink', 199.00, 220, 'https://images.unsplash.com/photo-1585336261026-8f57857820f2?w=500', 4.5, 1),
            (12, 'Mesh Desk Organizer 6-Tier', 'Pencil holder, document tray, sticky note', 799.00, 45, 'https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=500', 4.4, 1),
            (12, 'Ergonomic Mouse Pad with Wrist Rest', 'Memory foam gel support, non-slip base', 349.00, 110, 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500', 4.3, 1),
            (12, 'Highlighter Marker Pen Set (6 Colors)', 'Chisel tip pastel color highlighters', 249.00, 130, 'https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=500', 4.7, 1)
        ]
        cursor.executemany("INSERT INTO products (category_id, name, description, price, stock, image_url, rating, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", products)

        # Seed 120+ historical orders & payments across 365 days yielding 2M+ revenue
        cursor.execute("SELECT id, address FROM users WHERE role = 'customer'")
        cust_records = cursor.fetchall()
        cursor.execute("SELECT id, price FROM products")
        prod_records = cursor.fetchall()

        if cust_records and prod_records:
            now = datetime.now()
            order_statuses = ['Delivered', 'Delivered', 'Delivered', 'Shipped', 'Confirmed', 'Pending', 'Cancelled']
            payment_methods = ['UPI', 'Card', 'Cash on Delivery']

            for c_id, address in cust_records:
                num_orders = random.randint(6, 12)
                for _ in range(num_orders):
                    days_ago = random.randint(1, 365)
                    order_date_str = (now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime('%Y-%m-%d %H:%M:%S')
                    status = random.choice(order_statuses)
                    num_items = random.randint(1, 5)
                    chosen_prods = random.sample(prod_records, num_items)

                    total_amt = 0
                    items_to_insert = []
                    for p_id, p_price in chosen_prods:
                        qty = random.randint(1, 3)
                        p_val = float(p_price)
                        total_amt += (p_val * qty)
                        items_to_insert.append((p_id, qty, p_val))

                    cursor.execute(
                        "INSERT INTO orders (user_id, total_amount, order_status, shipping_address, order_date) VALUES (?, ?, ?, ?, ?)",
                        (c_id, round(total_amt, 2), status, address or "Main Street, City", order_date_str)
                    )
                    o_id = cursor.lastrowid

                    for p_id, qty, p_val in items_to_insert:
                        cursor.execute(
                            "INSERT INTO order_items (order_id, product_id, quantity, price, unit_price, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                            (o_id, p_id, qty, p_val, p_val, p_val * qty)
                        )

                    pm = random.choice(payment_methods)
                    p_status = 'Completed' if status == 'Delivered' else ('Refunded' if status == 'Cancelled' else 'Pending')
                    txn_id = f"TXN{''.join(random.choices('0123456789', k=10))}"
                    cursor.execute(
                        "INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, payment_date, amount) VALUES (?, ?, ?, ?, ?, ?)",
                        (o_id, pm, p_status, txn_id, order_date_str, round(total_amt, 2))
                    )

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

