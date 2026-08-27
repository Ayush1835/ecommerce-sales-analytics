import os
import sys
import random
from datetime import datetime, timedelta
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db_connection():
    host = os.environ.get('DB_HOST', 'localhost')
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'ecommerce_db')

    # First ensure database exists
    try:
        conn = mysql.connector.connect(host=host, user=user, password=password)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database creation note: {e}")

    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        sys.exit(1)

def ensure_tables_exist(cursor):
    print("Ensuring database tables exist...")
    create_queries = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('customer', 'admin') NOT NULL DEFAULT 'customer',
            phone VARCHAR(20),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NOT NULL,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            image_url VARCHAR(500),
            rating DECIMAL(3,2) DEFAULT 0.00,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS cart_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cart_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE (cart_id, product_id),
            FOREIGN KEY (cart_id) REFERENCES cart(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL,
            order_status ENUM('Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
            shipping_address TEXT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",

        """CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL UNIQUE,
            payment_method ENUM('Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash on Delivery', 'Card') NOT NULL,
            payment_status ENUM('Pending', 'Completed', 'Failed', 'Refunded') NOT NULL DEFAULT 'Pending',
            transaction_id VARCHAR(100) UNIQUE,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
    ]

    for query in create_queries:
        cursor.execute(query)

def truncate_tables(cursor):
    print("Truncating existing tables...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = ['payments', 'order_items', 'orders', 'cart_items', 'cart', 'products', 'categories', 'users']
    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table};")
        except Exception:
            pass
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Tables truncated.")

def seed_users(cursor):
    print("Seeding users...")
    users = []
    
    # Admins
    admins = [
        ('Rajesh Kumar', 'admin@ecommerce.com', 'admin', None, None),
        ('Priya Sharma', 'priya.admin@ecommerce.com', 'admin', None, None)
    ]
    
    # Customers
    customer_data = [
        ('Amit Patel', 'amit.patel@example.com', '9876543210', 'Navrangpura, Ahmedabad, Gujarat 380009'),
        ('Sneha Reddy', 'sneha.reddy@example.com', '9876543211', 'Banjara Hills, Hyderabad, Telangana 500034'),
        ('Vikram Singh', 'vikram.singh@example.com', '9876543212', 'Sector 17, Chandigarh, Punjab 160017'),
        ('Neha Gupta', 'neha.gupta@example.com', '9876543213', 'Indiranagar, Bengaluru, Karnataka 560038'),
        ('Arjun Nair', 'arjun.nair@example.com', '9876543214', 'Kaloor, Kochi, Kerala 682017'),
        ('Ananya Chatterjee', 'ananya.c@example.com', '9876543215', 'Salt Lake, Kolkata, West Bengal 700091'),
        ('Rohan Verma', 'rohan.verma@example.com', '9876543216', 'Connaught Place, New Delhi 110001'),
        ('Kavya Joshi', 'kavya.joshi@example.com', '9876543217', 'Kothrud, Pune, Maharashtra 411038'),
        ('Siddharth Rao', 'siddharth.rao@example.com', '9876543218', 'T. Nagar, Chennai, Tamil Nadu 600017'),
        ('Riya Shah', 'riya.shah@example.com', '9876543219', 'Marine Drive, Mumbai, Maharashtra 400020'),
        ('Aditya Malhotra', 'aditya.m@example.com', '9876543220', 'Civil Lines, Jaipur, Rajasthan 302006'),
        ('Pooja Deshmukh', 'pooja.d@example.com', '9876543221', 'Viman Nagar, Pune, Maharashtra 411014'),
        ('Karan Mehta', 'karan.mehta@example.com', '9876543222', 'Alkapuri, Vadodara, Gujarat 390007'),
        ('Divya Iyer', 'divya.iyer@example.com', '9876543223', 'Mylapore, Chennai, Tamil Nadu 600004'),
        ('Manish Agarwal', 'manish.a@example.com', '9876543224', 'Hazratganj, Lucknow, Uttar Pradesh 226001'),
        ('Tarun Bansal', 'tarun.b@example.com', '9876543225', 'Model Town, Ludhiana, Punjab 141002'),
        ('Swati Kulkarni', 'swati.k@example.com', '9876543226', 'Sadashiv Peth, Pune, Maharashtra 411030'),
        ('Gaurav Saxena', 'gaurav.s@example.com', '9876543227', 'Arera Colony, Bhopal, Madhya Pradesh 462016'),
        ('Meera Nambiar', 'meera.n@example.com', '9876543228', 'Panampilly Nagar, Kochi, Kerala 682036'),
        ('Rahul Kapoor', 'rahul.k@example.com', '9876543229', 'Vasant Kunj, New Delhi 110070'),
        ('Shweta Mishra', 'shweta.m@example.com', '9876543230', 'Boring Road, Patna, Bihar 800001'),
        ('Abhishek Tripathi', 'abhishek.t@example.com', '9876543231', 'Lanka, Varanasi, Uttar Pradesh 221005')
    ]
    
    hashed_password = generate_password_hash('Password@123')
    
    for name, email, role, phone, address in admins:
        users.append((name, email, hashed_password, role, phone, address))
        
    for name, email, phone, address in customer_data:
        users.append((name, email, hashed_password, 'customer', phone, address))
        
    query = """
    INSERT INTO users (name, email, password_hash, role, phone, address)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.executemany(query, users)
    print(f"Seeded {len(users)} users.")

def seed_categories(cursor):
    print("Seeding categories...")
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
    query = "INSERT INTO categories (name, description) VALUES (%s, %s);"
    cursor.executemany(query, categories)
    print(f"Seeded {len(categories)} categories.")

def seed_products(cursor):
    print("Seeding products...")
    cursor.execute("SELECT id, name FROM categories;")
    cat_map = {name: id for id, name in cursor.fetchall()}
    
    products = [
        (cat_map['Electronics'], 'Smartphone X Pro 256GB', '6.7-inch AMOLED display, 108MP camera, 5000mAh battery', 49999.00, 45, 'https://picsum.photos/seed/phone1/400/400', 4.7),
        (cat_map['Electronics'], 'Wireless Noise Cancelling Headphones', 'Active noise cancellation, 30-hour battery life', 14999.00, 30, 'https://picsum.photos/seed/headphones/400/400', 4.5),
        (cat_map['Electronics'], 'Ultra-Slim 15.6" Laptop', 'Intel i7 13th Gen, 16GB RAM, 512GB SSD', 68999.00, 20, 'https://picsum.photos/seed/laptop/400/400', 4.6),
        (cat_map['Electronics'], 'Smartwatch Series 5', 'Heart rate monitor, GPS, AMOLED display, water resistant', 8999.00, 60, 'https://picsum.photos/seed/watch/400/400', 4.3),
        (cat_map['Electronics'], '4K Ultra HD Smart TV 55"', 'Dolby Vision, HDR10+, Android TV with voice remote', 42999.00, 15, 'https://picsum.photos/seed/tv/400/400', 4.8),
        
        (cat_map['Fashion - Men'], 'Classic Fit Cotton Polo T-Shirt', '100% breathable pique cotton, ribbed collar', 899.00, 100, 'https://picsum.photos/seed/polo/400/400', 4.2),
        (cat_map['Fashion - Men'], 'Slim Fit Stretch Denim Jeans', 'Comfortable stretch fabric, dark indigo wash', 1899.00, 80, 'https://picsum.photos/seed/jeans/400/400', 4.4),
        (cat_map['Fashion - Men'], 'Casual Canvas Sneakers', 'Durable canvas upper, cushioned footbed', 1499.00, 50, 'https://picsum.photos/seed/sneakers/400/400', 4.1),
        (cat_map['Fashion - Men'], 'Formal Leather Dress Shoes', 'Genuine leather, handcrafted oxford design', 3499.00, 35, 'https://picsum.photos/seed/formalshoes/400/400', 4.5),
        (cat_map['Fashion - Men'], 'Windproof Bomber Jacket', 'Lightweight polyester fabric with zip pockets', 2499.00, 40, 'https://picsum.photos/seed/jacket/400/400', 4.3),
        
        (cat_map['Fashion - Women'], 'Floral Print Anarkali Kurta', 'Rayon fabric, embroidered neckline, includes dupatta', 1599.00, 90, 'https://picsum.photos/seed/kurta/400/400', 4.6),
        (cat_map['Fashion - Women'], 'High-Waist Skinny Jeans', 'Super stretch denim, five-pocket style', 1799.00, 75, 'https://picsum.photos/seed/wjeans/400/400', 4.3),
        (cat_map['Fashion - Women'], 'Structured Leather Tote Bag', 'Spacious compartment with zipper closure', 2299.00, 45, 'https://picsum.photos/seed/totebag/400/400', 4.7),
        (cat_map['Fashion - Women'], 'Block Heel Sandals', 'Comfortable 2-inch block heel, ankle strap', 1299.00, 60, 'https://picsum.photos/seed/sandals/400/400', 4.2),
        (cat_map['Fashion - Women'], 'Chiffon Evening Maxi Dress', 'Elegant A-line silhouette, ruffled sleeves', 2799.00, 30, 'https://picsum.photos/seed/dress/400/400', 4.5),
        
        (cat_map['Home & Kitchen'], 'Non-Stick Cookware Set (3-Piece)', 'Teflon coated fry pan, kadai with lid, tawa', 1999.00, 50, 'https://picsum.photos/seed/cookware/400/400', 4.4),
        (cat_map['Home & Kitchen'], 'Ergonomic Mesh Office Chair', 'Adjustable lumbar support, tilt mechanism', 6499.00, 25, 'https://picsum.photos/seed/officechair/400/400', 4.5),
        (cat_map['Home & Kitchen'], 'Stainless Steel Electric Kettle 1.5L', 'Auto shut-off, boil-dry protection, 1500W', 999.00, 85, 'https://picsum.photos/seed/kettle/400/400', 4.3),
        (cat_map['Home & Kitchen'], 'Cotton Queen Size Bed Sheet Set', '300 TC 100% cotton, includes 2 pillow covers', 1199.00, 70, 'https://picsum.photos/seed/bedsheet/400/400', 4.2),
        (cat_map['Home & Kitchen'], 'Air Fryer 4.2L Digital', '8 preset modes, 360-degree rapid air heating', 5999.00, 30, 'https://picsum.photos/seed/airfryer/400/400', 4.7),
        
        (cat_map['Books'], 'Atomic Habits by James Clear', 'An easy & proven way to build good habits & break bad ones', 499.00, 120, 'https://picsum.photos/seed/atomichabits/400/400', 4.9),
        (cat_map['Books'], 'The Psychology of Money', 'Timeless lessons on wealth, greed, and happiness', 399.00, 150, 'https://picsum.photos/seed/money/400/400', 4.8),
        (cat_map['Books'], 'Ikigai: The Japanese Secret to a Long Life', 'Discover your purpose and live longer, happier', 350.00, 110, 'https://picsum.photos/seed/ikigai/400/400', 4.6),
        (cat_map['Books'], 'Rich Dad Poor Dad by Robert Kiyosaki', 'What the rich teach their kids about money', 420.00, 95, 'https://picsum.photos/seed/richdad/400/400', 4.7),
        (cat_map['Books'], 'Deep Work by Cal Newport', 'Rules for focused success in a distracted world', 450.00, 80, 'https://picsum.photos/seed/deepwork/400/400', 4.5),
        
        (cat_map['Sports & Fitness'], 'Yoga Mat 6mm Eco-Friendly TPE', 'Non-slip surface, includes carrying strap', 799.00, 90, 'https://picsum.photos/seed/yogamat/400/400', 4.4),
        (cat_map['Sports & Fitness'], 'Adjustable Dumbbell Set 20kg', 'Chrome-plated weight plates with star lock collars', 3499.00, 35, 'https://picsum.photos/seed/dumbbells/400/400', 4.6),
        (cat_map['Sports & Fitness'], 'Resistance Bands Loop Set (5 Levels)', '100% natural latex for stretching & strength training', 499.00, 130, 'https://picsum.photos/seed/bands/400/400', 4.3),
        (cat_map['Sports & Fitness'], 'Badminton Racket Twin Pack', 'Aluminum frame, includes 3 nylon shuttlecocks', 1199.00, 60, 'https://picsum.photos/seed/badminton/400/400', 4.2),
        (cat_map['Sports & Fitness'], 'Sipper Water Bottle 1L Stainless Steel', 'Insulated vacuum flask keeps water cold for 24h', 699.00, 85, 'https://picsum.photos/seed/waterbottle/400/400', 4.5),

        (cat_map['Beauty & Personal Care'], 'Vitamin C Face Serum 30ml', 'Brightening serum with hyaluronic acid & ferulic acid', 599.00, 110, 'https://picsum.photos/seed/faceserum/400/400', 4.6),
        (cat_map['Beauty & Personal Care'], 'Organic Argan Oil Shampoo 300ml', 'Sulfate-free, restores shine and repair damage', 449.00, 95, 'https://picsum.photos/seed/shampoo/400/400', 4.3),
        (cat_map['Beauty & Personal Care'], 'Matte Liquid Lipstick Set (4 Pcs)', 'Long-lasting, waterproof, transfer-proof formula', 899.00, 70, 'https://picsum.photos/seed/lipstick/400/400', 4.4),
        (cat_map['Beauty & Personal Care'], 'Electric Beard Trimmer for Men', 'Self-sharpening stainless steel blades, 60-min runtime', 1299.00, 55, 'https://picsum.photos/seed/trimmer/400/400', 4.5),
        (cat_map['Beauty & Personal Care'], 'Sunscreen Gel SPF 50 PA++++', 'Non-greasy, zero white cast, broad spectrum protection', 399.00, 140, 'https://picsum.photos/seed/sunscreen/400/400', 4.7),

        (cat_map['Grocery & Gourmet'], 'Organic Green Tea 100 Tea Bags', 'Antioxidant-rich whole leaf green tea', 349.00, 160, 'https://picsum.photos/seed/greentea/400/400', 4.5),
        (cat_map['Grocery & Gourmet'], 'Raw Unfiltered Honey 500g', '100% pure honey with natural enzymes', 299.00, 120, 'https://picsum.photos/seed/honey/400/400', 4.6),
        (cat_map['Grocery & Gourmet'], 'California Almonds 500g Pack', 'Premium quality, crunchy and nutritious', 499.00, 100, 'https://picsum.photos/seed/almonds/400/400', 4.7),
        (cat_map['Grocery & Gourmet'], 'Extra Virgin Olive Oil 1L', 'Cold-pressed, ideal for salads and cooking', 899.00, 65, 'https://picsum.photos/seed/oliveoil/400/400', 4.4),
        (cat_map['Grocery & Gourmet'], 'Dark Chocolate 70% Cocoa 100g', 'Rich gourmet Belgian dark chocolate bar', 199.00, 180, 'https://picsum.photos/seed/chocolate/400/400', 4.8),

        (cat_map['Toys & Games'], 'Monopoly Classic Board Game', 'Fast-dealing property trading board game for family', 999.00, 45, 'https://picsum.photos/seed/monopoly/400/400', 4.7),
        (cat_map['Toys & Games'], 'Rubik Cube 3x3 Speed Cube', 'Smooth stickerless speed cube for brain exercise', 299.00, 150, 'https://picsum.photos/seed/rubik/400/400', 4.5),
        (cat_map['Toys & Games'], 'Building Blocks Set 500 Pieces', 'Compatible classic brick set for creative play', 1499.00, 40, 'https://picsum.photos/seed/blocks/400/400', 4.6),
        (cat_map['Toys & Games'], 'Remote Control Stunt Car', '360-degree rotating double-sided flip car', 1199.00, 50, 'https://picsum.photos/seed/rccar/400/400', 4.3),
        (cat_map['Toys & Games'], 'Wooden Chess Set Foldable', 'Handcrafted magnetic chess board with storage slots', 899.00, 60, 'https://picsum.photos/seed/chess/400/400', 4.8),

        (cat_map['Automotive'], 'High-Pressure Car Washer Pump', '1800W motor, 120 bar pressure with adjustable spray nozzle', 4999.00, 20, 'https://picsum.photos/seed/carwasher/400/400', 4.4),
        (cat_map['Automotive'], 'Car Dashboard Phone Mount', '360-degree rotation, strong suction cup', 399.00, 110, 'https://picsum.photos/seed/phonemount/400/400', 4.2),
        (cat_map['Automotive'], 'Microfiber Cloth Pack of 4', '800 GSM plush car detailing drying towels', 499.00, 140, 'https://picsum.photos/seed/microfiber/400/400', 4.6),
        (cat_map['Automotive'], 'Digital Tyre Inflator Portable', '12V DC auto cutoff air compressor with LED light', 1899.00, 35, 'https://picsum.photos/seed/tyreinflator/400/400', 4.5),
        (cat_map['Automotive'], 'Car Vacuum Cleaner High Power', '12V 120W wet & dry car hand vacuum', 1199.00, 55, 'https://picsum.photos/seed/carvac/400/400', 4.3),

        (cat_map['Mobile Accessories'], 'Fast Charging Power Bank 20000mAh', '22.5W two-way fast charge, triple output ports', 1699.00, 75, 'https://picsum.photos/seed/powerbank/400/400', 4.5),
        (cat_map['Mobile Accessories'], 'Braided Type-C to Type-C Cable 2m', '100W PD fast charging, 10000+ bend lifespan', 399.00, 160, 'https://picsum.photos/seed/typeccable/400/400', 4.4),
        (cat_map['Mobile Accessories'], 'Magnetic Wireless Charger 15W', 'MagSafe compatible for iPhone and Android devices', 999.00, 50, 'https://picsum.photos/seed/wirelesscharger/400/400', 4.3),
        (cat_map['Mobile Accessories'], 'Bluetooth Selfie Stick Tripod', 'Detachable wireless remote, extendable 100cm', 599.00, 90, 'https://picsum.photos/seed/selfiestick/400/400', 4.2),
        (cat_map['Mobile Accessories'], 'Universal Waterproof Phone Pouch', 'IPX8 certified pouch with neck strap', 249.00, 200, 'https://picsum.photos/seed/waterproofpouch/400/400', 4.6),

        (cat_map['Stationery & Office'], 'Executive Leather Journal Notebook', '200 thick unruled pages, ribbon bookmark', 599.00, 80, 'https://picsum.photos/seed/notebook/400/400', 4.6),
        (cat_map['Stationery & Office'], 'Gel Pen Pack of 10 (Blue & Black)', 'Smooth 0.5mm tip, quick-dry smudge-proof ink', 199.00, 220, 'https://picsum.photos/seed/gelpens/400/400', 4.5),
        (cat_map['Stationery & Office'], 'Mesh Desk Organizer 6-Tier', 'Pencil holder, document tray, sticky note compartment', 799.00, 45, 'https://picsum.photos/seed/deskorganizer/400/400', 4.4),
        (cat_map['Stationery & Office'], 'Ergonomic Mouse Pad with Wrist Rest', 'Memory foam gel support, non-slip rubber base', 349.00, 110, 'https://picsum.photos/seed/mousepad/400/400', 4.3),
        (cat_map['Stationery & Office'], 'Highlighter Marker Pen Set (6 Colors)', 'Chisel tip pastel color highlighters', 249.00, 130, 'https://picsum.photos/seed/highlighters/400/400', 4.7)
    ]
    
    query = """
    INSERT INTO products (category_id, name, description, price, stock, image_url, rating)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    cursor.executemany(query, products)
    print(f"Seeded {len(products)} products.")

def seed_carts_and_items(cursor):
    print("Seeding carts and cart items...")
    cursor.execute("SELECT id FROM users WHERE role = 'customer';")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, price, stock FROM products WHERE is_active = TRUE;")
    products = cursor.fetchall()
    
    cart_count = 0
    item_count = 0
    
    for uid in customer_ids[:15]:
        cursor.execute("INSERT INTO cart (user_id) VALUES (%s);", (uid,))
        cart_id = cursor.lastrowid
        cart_count += 1
        
        num_items = random.randint(1, 4)
        chosen_products = random.sample(products, num_items)
        
        for pid, price, stock in chosen_products:
            qty = random.randint(1, min(3, max(1, stock)))
            cursor.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s);",
                (cart_id, pid, qty)
            )
            item_count += 1
            
    print(f"Seeded {cart_count} carts with {item_count} cart items.")

def seed_orders_items_payments(cursor):
    print("Seeding orders, order items, and payments...")
    cursor.execute("SELECT id, address FROM users WHERE role = 'customer';")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id, price, stock FROM products;")
    products = cursor.fetchall()
    
    order_statuses = ['Delivered', 'Delivered', 'Delivered', 'Shipped', 'Confirmed', 'Pending', 'Cancelled']
    payment_methods = ['UPI', 'Card', 'Cash on Delivery']
    
    order_count = 0
    order_item_count = 0
    payment_count = 0
    
    now = datetime.now()
    
    for uid, address in customers:
        num_orders = random.randint(3, 8)
        
        for _ in range(num_orders):
            days_ago = random.randint(1, 365)
            order_date = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            status = random.choice(order_statuses)
            
            num_items = random.randint(1, 5)
            chosen_products = random.sample(products, num_items)
            
            total_amount = 0
            order_items_data = []
            
            for pid, price, stock in chosen_products:
                qty = random.randint(1, 3)
                price_val = float(price)
                line_total = price_val * qty
                total_amount += line_total
                order_items_data.append((pid, qty, price_val))
                
            cursor.execute(
                """
                INSERT INTO orders (user_id, total_amount, order_status, shipping_address, order_date)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (uid, round(total_amount, 2), status, address or "Main Street, City", order_date)
            )
            order_id = cursor.lastrowid
            order_count += 1
            
            for pid, qty, price_val in order_items_data:
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (order_id, pid, qty, price_val)
                )
                order_item_count += 1
                
            pm = random.choice(payment_methods)
            if status == 'Delivered':
                p_status = 'Completed'
            elif status == 'Cancelled':
                p_status = 'Refunded' if pm != 'Cash on Delivery' else 'Failed'
            else:
                p_status = 'Completed' if pm in ['UPI', 'Card'] else 'Pending'
                
            txn_id = f"TXN{''.join(random.choices('0123456789', k=10))}"
            
            cursor.execute(
                """
                INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, payment_date)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (order_id, pm, p_status, txn_id, order_date)
            )
            payment_count += 1

    print(f"Seeded {order_count} orders, {order_item_count} order items, and {payment_count} payment records.")

def main():
    print("=" * 60)
    print("ShopAnalytica — Database Seeding Script")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        ensure_tables_exist(cursor)
        truncate_tables(cursor)
        seed_users(cursor)
        seed_categories(cursor)
        seed_products(cursor)
        seed_carts_and_items(cursor)
        seed_orders_items_payments(cursor)
        
        conn.commit()
        print("=" * 60)
        print("Database seeding completed successfully!")
        print("=" * 60)
    except Exception as e:
        conn.rollback()
        print(f"\nError occurred: {e}")
        print("Transaction rolled back.")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
