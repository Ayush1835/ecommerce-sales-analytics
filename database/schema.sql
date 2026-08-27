-- ============================================================================
-- E-COMMERCE SALES & CUSTOMER ANALYTICS PLATFORM
-- Database Schema Definition
-- ============================================================================
--
-- Description : Complete relational schema for an e-commerce platform that
--               supports product catalog management, shopping carts, order
--               processing, payments, and customer analytics.
--
-- Engine      : InnoDB (transactional, supports foreign keys)
-- Charset     : utf8mb4 (full Unicode support including emojis)
-- Collation   : utf8mb4_unicode_ci
--
-- Tables (8)  : users, categories, products, cart, cart_items,
--               orders, order_items, payments
--
-- Author      : Auto-generated schema
-- Created     : 2026-08-27
-- ============================================================================


-- ============================================================================
-- DATABASE SETUP
-- ============================================================================
-- Drop the database if it already exists to ensure a clean slate,
-- then create it fresh with utf8mb4 encoding for full Unicode support.
-- ============================================================================

DROP DATABASE IF EXISTS ecommerce_db;

CREATE DATABASE ecommerce_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ecommerce_db;


-- ============================================================================
-- TABLE 1: users
-- ============================================================================
-- Stores all registered users of the platform (both customers and admins).
-- Every user has a unique email address used for authentication.
-- The password_hash column stores bcrypt/argon2 hashed passwords — never
-- store plaintext passwords.
--
-- Indexes:
--   idx_users_email  — Speeds up email lookups during login/authentication.
--   idx_users_role   — Enables fast filtering of customers vs admin users.
-- ============================================================================

CREATE TABLE users (
    id            INT           AUTO_INCREMENT PRIMARY KEY
                                COMMENT 'Unique identifier for each user',

    name          VARCHAR(100)  NOT NULL
                                COMMENT 'Full name of the user',

    email         VARCHAR(100)  NOT NULL UNIQUE
                                COMMENT 'Email address used for login; must be unique',

    password_hash VARCHAR(255)  NOT NULL
                                COMMENT 'Hashed password (bcrypt/argon2); never store plaintext',

    role          ENUM('customer', 'admin')
                                DEFAULT 'customer'
                                COMMENT 'User role: customer (default) or admin',

    phone         VARCHAR(15)
                                COMMENT 'Optional phone number with country code',

    address       TEXT
                                COMMENT 'Default shipping/billing address',

    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
                                COMMENT 'Account creation timestamp',

    updated_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                COMMENT 'Last profile update timestamp',

    -- ----- Indexes -----
    -- Index on email for fast lookups during login and authentication queries
    INDEX idx_users_email (email),

    -- Index on role to efficiently filter customers vs admins in admin panels
    INDEX idx_users_role (role)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Registered users of the e-commerce platform (customers and admins)';


-- ============================================================================
-- TABLE 2: categories
-- ============================================================================
-- Product categories for organizing the catalog (e.g., Electronics, Clothing).
-- Each category has a unique name. Products reference this table via FK.
-- ============================================================================

CREATE TABLE categories (
    id          INT           AUTO_INCREMENT PRIMARY KEY
                              COMMENT 'Unique identifier for each category',

    name        VARCHAR(100)  NOT NULL UNIQUE
                              COMMENT 'Category name; must be unique (e.g., Electronics, Clothing)',

    description TEXT
                              COMMENT 'Optional description of the category',

    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
                              COMMENT 'Timestamp when the category was created'

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Product categories for organizing the catalog';


-- ============================================================================
-- TABLE 3: products
-- ============================================================================
-- Central product catalog. Each product belongs to exactly one category.
-- Pricing, stock levels, and ratings are tracked here.
--
-- Foreign Keys:
--   category_id -> categories(id)
--     ON DELETE RESTRICT  — Prevent deleting a category that still has products.
--     ON UPDATE CASCADE   — If a category ID changes, propagate the update.
--
-- Indexes:
--   idx_products_category  — Optimizes JOINs with categories and category filtering.
--   idx_products_price     — Speeds up price range queries and sorting by price.
--   idx_products_active    — Quickly filters active vs inactive products.
--   idx_products_name      — Supports product search-by-name queries.
--
-- Check Constraints:
--   chk_products_price  — Price must be greater than zero.
--   chk_products_stock  — Stock cannot be negative.
--   chk_products_rating — Rating must be between 0.0 and 5.0.
-- ============================================================================

CREATE TABLE products (
    id          INT            AUTO_INCREMENT PRIMARY KEY
                               COMMENT 'Unique identifier for each product',

    category_id INT            NOT NULL
                               COMMENT 'FK to categories table; every product must belong to a category',

    name        VARCHAR(200)   NOT NULL
                               COMMENT 'Product name displayed to customers',

    description TEXT
                               COMMENT 'Detailed product description',

    price       DECIMAL(10, 2) NOT NULL
                               COMMENT 'Current selling price in the platform currency',

    stock       INT            NOT NULL DEFAULT 0
                               COMMENT 'Available inventory count; decremented on purchase',

    image_url   VARCHAR(500)
                               COMMENT 'URL to the product image (stored in CDN/object storage)',

    rating      DECIMAL(2, 1)  DEFAULT 0.0
                               COMMENT 'Average customer rating from 0.0 to 5.0',

    is_active   BOOLEAN        DEFAULT TRUE
                               COMMENT 'Soft-delete flag; FALSE hides the product from the storefront',

    created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
                               COMMENT 'Timestamp when the product was added to the catalog',

    updated_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                               COMMENT 'Timestamp of the last product update',

    -- ----- Indexes -----
    -- Index on category_id for JOIN queries and filtering products by category
    INDEX idx_products_category (category_id),

    -- Index on price for sorting (low-to-high, high-to-low) and range filtering
    INDEX idx_products_price (price),

    -- Index on is_active to quickly filter active products on the storefront
    INDEX idx_products_active (is_active),

    -- Index on name for product search queries (LIKE 'keyword%')
    INDEX idx_products_name (name),

    -- ----- Foreign Keys -----
    -- Prevent deletion of a category that still contains products (RESTRICT).
    -- If a category's ID is updated, cascade the change to all its products.
    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- ----- Check Constraints -----
    -- Price must be strictly positive (no free or negative-priced products)
    CONSTRAINT chk_products_price
        CHECK (price > 0),

    -- Stock cannot go negative
    CONSTRAINT chk_products_stock
        CHECK (stock >= 0),

    -- Rating must be within the valid 0.0 – 5.0 range
    CONSTRAINT chk_products_rating
        CHECK (rating >= 0 AND rating <= 5)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Product catalog with pricing, stock, and rating information';


-- ============================================================================
-- TABLE 4: cart
-- ============================================================================
-- Represents a shopping cart. Each user has at most one cart, enforced by
-- a UNIQUE constraint on user_id. The cart is created when the user first
-- adds an item and persists across sessions.
--
-- Foreign Keys:
--   user_id -> users(id)
--     ON DELETE CASCADE  — If a user account is deleted, remove their cart.
--     ON UPDATE CASCADE  — If a user ID changes, propagate the update.
-- ============================================================================

CREATE TABLE cart (
    id         INT       AUTO_INCREMENT PRIMARY KEY
                         COMMENT 'Unique identifier for each cart',

    user_id    INT       NOT NULL UNIQUE
                         COMMENT 'FK to users table; UNIQUE ensures one cart per user',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         COMMENT 'Timestamp when the cart was created',

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                         COMMENT 'Timestamp of the last cart modification',

    -- ----- Foreign Keys -----
    -- Deleting a user cascades to delete their cart automatically.
    CONSTRAINT fk_cart_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Shopping carts — one per user, enforced by UNIQUE constraint on user_id';


-- ============================================================================
-- TABLE 5: cart_items
-- ============================================================================
-- Individual line items within a shopping cart. Each row represents one
-- product in a specific cart with a given quantity.
--
-- Foreign Keys:
--   cart_id    -> cart(id)     ON DELETE CASCADE  ON UPDATE CASCADE
--   product_id -> products(id) ON DELETE CASCADE  ON UPDATE CASCADE
--
-- Unique Key:
--   uq_cart_product — Prevents the same product from appearing twice in
--                     one cart. Instead, the quantity column should be updated.
--
-- Indexes:
--   idx_cart_items_cart    — Efficiently retrieve all items belonging to a cart.
--   idx_cart_items_product — Find which carts contain a specific product.
--
-- Check Constraints:
--   chk_cart_items_qty — Quantity must be at least 1.
-- ============================================================================

CREATE TABLE cart_items (
    id         INT       AUTO_INCREMENT PRIMARY KEY
                         COMMENT 'Unique identifier for each cart item',

    cart_id    INT       NOT NULL
                         COMMENT 'FK to cart table; identifies which cart this item belongs to',

    product_id INT       NOT NULL
                         COMMENT 'FK to products table; identifies the product in the cart',

    quantity   INT       NOT NULL DEFAULT 1
                         COMMENT 'Number of units of this product in the cart',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         COMMENT 'Timestamp when the item was added to the cart',

    -- ----- Unique Key -----
    -- Prevent duplicate product entries within the same cart;
    -- if a user adds the same product again, update the quantity instead.
    UNIQUE KEY uq_cart_product (cart_id, product_id),

    -- ----- Indexes -----
    -- Index on cart_id to efficiently retrieve all items in a user's cart
    INDEX idx_cart_items_cart (cart_id),

    -- Index on product_id to check which carts contain a particular product
    INDEX idx_cart_items_product (product_id),

    -- ----- Foreign Keys -----
    -- Deleting a cart cascades to remove all its items.
    CONSTRAINT fk_cart_items_cart
        FOREIGN KEY (cart_id) REFERENCES cart(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- Deleting a product cascades to remove it from all carts.
    CONSTRAINT fk_cart_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- ----- Check Constraints -----
    -- Quantity must be at least 1 (no zero or negative quantities)
    CONSTRAINT chk_cart_items_qty
        CHECK (quantity > 0)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Individual items within a shopping cart with quantity tracking';


-- ============================================================================
-- TABLE 6: orders
-- ============================================================================
-- Stores completed and in-progress orders. An order is created when a
-- customer checks out their cart. The total_amount is the sum of all
-- order_items (quantity × price).
--
-- Foreign Keys:
--   user_id -> users(id)
--     ON DELETE RESTRICT — Cannot delete a user who has order history.
--     ON UPDATE CASCADE  — Propagate user ID changes.
--
-- Indexes:
--   idx_orders_user   — Retrieve a customer's order history quickly.
--   idx_orders_status — Filter orders by status (e.g., show all pending).
--   idx_orders_date   — Sort/filter orders by date for analytics dashboards.
--
-- Check Constraints:
--   chk_orders_total — Total amount cannot be negative.
-- ============================================================================

CREATE TABLE orders (
    id               INT            AUTO_INCREMENT PRIMARY KEY
                                    COMMENT 'Unique identifier for each order',

    user_id          INT            NOT NULL
                                    COMMENT 'FK to users table; the customer who placed the order',

    total_amount     DECIMAL(10, 2) NOT NULL
                                    COMMENT 'Total order value (sum of order_items quantity × price)',

    order_status     ENUM('Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled')
                                    DEFAULT 'Pending'
                                    COMMENT 'Current status of the order in the fulfillment pipeline',

    shipping_address TEXT           NOT NULL
                                    COMMENT 'Delivery address snapshot at the time of order placement',

    order_date       TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
                                    COMMENT 'Timestamp when the order was placed',

    updated_at       TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                    COMMENT 'Timestamp of the last order status update',

    -- ----- Indexes -----
    -- Index on user_id for fetching a customer's order history
    INDEX idx_orders_user (user_id),

    -- Index on order_status for filtering orders by fulfillment status
    INDEX idx_orders_status (order_status),

    -- Index on order_date for date-range analytics and chronological sorting
    INDEX idx_orders_date (order_date),

    -- ----- Foreign Keys -----
    -- RESTRICT prevents deleting users who have placed orders (preserve history).
    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- ----- Check Constraints -----
    -- Total amount cannot be negative
    CONSTRAINT chk_orders_total
        CHECK (total_amount >= 0)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Customer orders with status tracking and shipping information';


-- ============================================================================
-- TABLE 7: order_items
-- ============================================================================
-- Line items within an order. Each row captures the product, quantity,
-- and the price AT THE TIME OF PURCHASE. This is critical because product
-- prices can change after the order is placed.
--
-- Foreign Keys:
--   order_id   -> orders(id)   ON DELETE CASCADE   ON UPDATE CASCADE
--   product_id -> products(id) ON DELETE RESTRICT  ON UPDATE CASCADE
--
-- Indexes:
--   idx_order_items_order   — Retrieve all items belonging to an order.
--   idx_order_items_product — Analytics: find all orders that contain a product.
--
-- Check Constraints:
--   chk_order_items_qty   — Quantity must be at least 1.
--   chk_order_items_price — Price snapshot cannot be negative.
-- ============================================================================

CREATE TABLE order_items (
    id         INT            AUTO_INCREMENT PRIMARY KEY
                              COMMENT 'Unique identifier for each order line item',

    order_id   INT            NOT NULL
                              COMMENT 'FK to orders table; identifies the parent order',

    product_id INT            NOT NULL
                              COMMENT 'FK to products table; identifies the purchased product',

    quantity   INT            NOT NULL
                              COMMENT 'Number of units purchased',

    price      DECIMAL(10, 2) NOT NULL
                              COMMENT 'Price per unit at the time of purchase (historical snapshot)',

    -- ----- Indexes -----
    -- Index on order_id to efficiently retrieve all items within an order
    INDEX idx_order_items_order (order_id),

    -- Index on product_id for analytics — find all orders containing a product
    INDEX idx_order_items_product (product_id),

    -- ----- Foreign Keys -----
    -- Deleting an order cascades to remove all its line items.
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- RESTRICT prevents deleting a product that has been ordered (preserve history).
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    -- ----- Check Constraints -----
    -- Quantity must be at least 1
    CONSTRAINT chk_order_items_qty
        CHECK (quantity > 0),

    -- Price snapshot cannot be negative
    CONSTRAINT chk_order_items_price
        CHECK (price >= 0)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Individual line items within an order with historical price snapshots';


-- ============================================================================
-- TABLE 8: payments
-- ============================================================================
-- Payment records linked to orders. Each order has at most one payment
-- record, enforced by the UNIQUE constraint on order_id.
--
-- Supported payment methods: Cash on Delivery, Card, UPI.
-- Payment lifecycle: Pending → Completed / Failed → Refunded.
--
-- Foreign Keys:
--   order_id -> orders(id)
--     ON DELETE CASCADE — If an order is deleted, remove its payment record.
--     ON UPDATE CASCADE — Propagate order ID changes.
--
-- Indexes:
--   idx_payments_status — Filter payments by status (e.g., find all failed).
-- ============================================================================

CREATE TABLE payments (
    id             INT          AUTO_INCREMENT PRIMARY KEY
                                COMMENT 'Unique identifier for each payment record',

    order_id       INT          NOT NULL UNIQUE
                                COMMENT 'FK to orders table; UNIQUE ensures one payment per order',

    payment_method ENUM('Cash on Delivery', 'Card', 'UPI')
                                NOT NULL
                                COMMENT 'Method used for payment',

    payment_status ENUM('Pending', 'Completed', 'Failed', 'Refunded')
                                DEFAULT 'Pending'
                                COMMENT 'Current payment status in the payment lifecycle',

    transaction_id VARCHAR(100)
                                COMMENT 'External payment gateway transaction reference ID',

    payment_date   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                                COMMENT 'Timestamp when the payment was initiated',

    -- ----- Indexes -----
    -- Index on payment_status for filtering payments by their current status
    INDEX idx_payments_status (payment_status),

    -- ----- Foreign Keys -----
    -- Deleting an order cascades to remove its payment record.
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Payment records with method, status, and transaction tracking';


-- ============================================================================
-- ============================================================================
--
--                    ANALYTICS QUERIES (REFERENCE EXAMPLES)
--
-- The following 10 queries demonstrate common analytics operations on this
-- schema. They are provided as comments for reference and documentation
-- purposes — they are NOT executed as part of the schema creation.
--
-- ============================================================================
-- ============================================================================


-- ----------------------------------------------------------------------------
-- QUERY 1: Total Revenue
-- ----------------------------------------------------------------------------
-- Calculates the total revenue from all delivered orders.
-- Only delivered orders are counted to exclude cancelled/pending orders.
-- ----------------------------------------------------------------------------
/*
SELECT
    SUM(total_amount) AS total_revenue
FROM orders
WHERE order_status = 'Delivered';
*/


-- ----------------------------------------------------------------------------
-- QUERY 2: Monthly Revenue
-- ----------------------------------------------------------------------------
-- Breaks down revenue by month and year for trend analysis.
-- Uses DATE_FORMAT to extract year-month from the order date.
-- ----------------------------------------------------------------------------
/*
SELECT
    DATE_FORMAT(order_date, '%Y-%m')  AS month,
    SUM(total_amount)                 AS monthly_revenue
FROM orders
WHERE order_status = 'Delivered'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month DESC;
*/


-- ----------------------------------------------------------------------------
-- QUERY 3: Top-Selling Products (by Quantity)
-- ----------------------------------------------------------------------------
-- Identifies the most popular products based on total units sold.
-- Joins order_items with products to get product names.
-- ----------------------------------------------------------------------------
/*
SELECT
    p.id                   AS product_id,
    p.name                 AS product_name,
    SUM(oi.quantity)       AS total_quantity_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.id
JOIN orders o   ON oi.order_id  = o.id
WHERE o.order_status = 'Delivered'
GROUP BY p.id, p.name
ORDER BY total_quantity_sold DESC
LIMIT 10;
*/


-- ----------------------------------------------------------------------------
-- QUERY 4: Top Customers (by Spending)
-- ----------------------------------------------------------------------------
-- Ranks customers by their total spending across all delivered orders.
-- Useful for identifying VIP customers for loyalty programs.
-- ----------------------------------------------------------------------------
/*
SELECT
    u.id                   AS customer_id,
    u.name                 AS customer_name,
    u.email                AS customer_email,
    SUM(o.total_amount)    AS total_spent,
    COUNT(o.id)            AS total_orders
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.order_status = 'Delivered'
GROUP BY u.id, u.name, u.email
ORDER BY total_spent DESC
LIMIT 10;
*/


-- ----------------------------------------------------------------------------
-- QUERY 5: Sales by Category
-- ----------------------------------------------------------------------------
-- Aggregates revenue and units sold by product category.
-- Helps identify which categories drive the most business.
-- ----------------------------------------------------------------------------
/*
SELECT
    c.id                          AS category_id,
    c.name                        AS category_name,
    SUM(oi.quantity * oi.price)   AS category_revenue,
    SUM(oi.quantity)              AS total_units_sold
FROM order_items oi
JOIN products p    ON oi.product_id  = p.id
JOIN categories c  ON p.category_id  = c.id
JOIN orders o      ON oi.order_id    = o.id
WHERE o.order_status = 'Delivered'
GROUP BY c.id, c.name
ORDER BY category_revenue DESC;
*/


-- ----------------------------------------------------------------------------
-- QUERY 6: Average Order Value (AOV)
-- ----------------------------------------------------------------------------
-- Calculates the average amount spent per order.
-- A key metric for understanding purchasing behavior.
-- ----------------------------------------------------------------------------
/*
SELECT
    AVG(total_amount) AS average_order_value
FROM orders
WHERE order_status = 'Delivered';
*/


-- ----------------------------------------------------------------------------
-- QUERY 7: Low-Stock Products (Stock < 10)
-- ----------------------------------------------------------------------------
-- Identifies products that are running low on inventory.
-- Critical for supply chain management and restock alerts.
-- ----------------------------------------------------------------------------
/*
SELECT
    p.id           AS product_id,
    p.name         AS product_name,
    p.stock        AS current_stock,
    c.name         AS category_name
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE p.stock < 10
  AND p.is_active = TRUE
ORDER BY p.stock ASC;
*/


-- ----------------------------------------------------------------------------
-- QUERY 8: Customers Who Never Placed Orders
-- ----------------------------------------------------------------------------
-- Finds registered users who have never made a purchase.
-- Useful for targeting with promotional campaigns or emails.
-- ----------------------------------------------------------------------------
/*
SELECT
    u.id          AS customer_id,
    u.name        AS customer_name,
    u.email       AS customer_email,
    u.created_at  AS registered_on
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL
  AND u.role = 'customer'
ORDER BY u.created_at DESC;
*/


-- ----------------------------------------------------------------------------
-- QUERY 9: Products Never Purchased
-- ----------------------------------------------------------------------------
-- Identifies products that exist in the catalog but have never been ordered.
-- Helps evaluate product-market fit and identify underperforming listings.
-- ----------------------------------------------------------------------------
/*
SELECT
    p.id          AS product_id,
    p.name        AS product_name,
    p.price       AS price,
    c.name        AS category_name,
    p.created_at  AS listed_on
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
JOIN categories c        ON p.category_id = c.id
WHERE oi.id IS NULL
  AND p.is_active = TRUE
ORDER BY p.created_at ASC;
*/


-- ----------------------------------------------------------------------------
-- QUERY 10: Monthly Order Count
-- ----------------------------------------------------------------------------
-- Counts the number of orders placed each month.
-- Useful for tracking growth and identifying seasonal trends.
-- ----------------------------------------------------------------------------
/*
SELECT
    DATE_FORMAT(order_date, '%Y-%m')  AS month,
    COUNT(id)                         AS total_orders
FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month DESC;
*/


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
