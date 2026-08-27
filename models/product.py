# ==================================================
# Product Model — Database Operations
# ==================================================
# Handles all product-related database queries including
# filtered search with pagination for the storefront.
# ==================================================

import math
from models.db import execute_query, get_db_connection


def get_all_products(active_only=False):
    """Fetch all products with category name via JOIN."""
    query = """SELECT p.*, c.name AS category_name
               FROM products p
               JOIN categories c ON p.category_id = c.id"""
    if active_only:
        query += " WHERE p.is_active = TRUE"
    query += " ORDER BY p.created_at DESC"
    return execute_query(query, fetchall=True)


def get_product_by_id(product_id):
    """Fetch a single product with its category name."""
    return execute_query(
        """SELECT p.*, c.name AS category_name
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.id = %s""",
        (product_id,),
        fetchone=True
    )


def create_product(category_id, name, description, price, stock,
                    image_url=None, rating=0.0):
    """Create a new product. Returns the new product ID."""
    return execute_query(
        """INSERT INTO products
           (category_id, name, description, price, stock, image_url, rating, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)""",
        (category_id, name, description, price, stock, image_url, rating),
        commit=True
    )


def update_product(product_id, category_id, name, description,
                    price, stock, image_url, is_active):
    """Update all fields of an existing product."""
    return execute_query(
        """UPDATE products
           SET category_id = %s, name = %s, description = %s,
               price = %s, stock = %s, image_url = %s, is_active = %s
           WHERE id = %s""",
        (category_id, name, description, price, stock, image_url,
         is_active, product_id),
        commit=True
    )


def deactivate_product(product_id):
    """Soft-delete: set is_active = FALSE."""
    return execute_query(
        "UPDATE products SET is_active = FALSE WHERE id = %s",
        (product_id,),
        commit=True
    )


def activate_product(product_id):
    """Reactivate a deactivated product."""
    return execute_query(
        "UPDATE products SET is_active = TRUE WHERE id = %s",
        (product_id,),
        commit=True
    )


def update_stock(product_id, new_stock):
    """Update stock quantity for a product."""
    return execute_query(
        "UPDATE products SET stock = %s WHERE id = %s",
        (new_stock, product_id),
        commit=True
    )


def get_products_filtered(category_id=None, min_price=None, max_price=None,
                           search=None, in_stock_only=False,
                           sort_by='newest', page=1, per_page=12):
    """
    Fetch products with dynamic filtering, searching, sorting, and pagination.
    Returns (products_list, total_count).

    Demonstrates: WHERE, LIKE, ORDER BY, LIMIT, OFFSET, COUNT, JOIN
    """
    base = """FROM products p
              JOIN categories c ON p.category_id = c.id
              WHERE p.is_active = TRUE"""
    params = []

    # Dynamic filters
    if category_id:
        base += " AND p.category_id = %s"
        params.append(int(category_id))

    if min_price is not None:
        base += " AND p.price >= %s"
        params.append(float(min_price))

    if max_price is not None:
        base += " AND p.price <= %s"
        params.append(float(max_price))

    if search:
        base += " AND (p.name LIKE %s OR p.description LIKE %s OR c.name LIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])

    if in_stock_only:
        base += " AND p.stock > 0"

    # Count total matching products (for pagination)
    count_query = f"SELECT COUNT(*) AS total {base}"
    total = execute_query(count_query, tuple(params), fetchone=True)['total']

    # Sorting
    sort_map = {
        'newest': 'p.created_at DESC',
        'price_low': 'p.price ASC',
        'price_high': 'p.price DESC',
        'rating': 'p.rating DESC',
        'name_asc': 'p.name ASC'
    }
    order = sort_map.get(sort_by, 'p.created_at DESC')

    # Paginated query
    data_query = f"SELECT p.*, c.name AS category_name {base} ORDER BY {order} LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    products = execute_query(data_query, tuple(params), fetchall=True)
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return products, total, total_pages


def get_featured_products(limit=8):
    """Fetch top-rated active products for the homepage."""
    return execute_query(
        """SELECT p.*, c.name AS category_name
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.is_active = TRUE AND p.stock > 0
           ORDER BY p.rating DESC, p.created_at DESC
           LIMIT %s""",
        (limit,),
        fetchall=True
    )


def get_low_stock_products(threshold=10):
    """Fetch products with stock below the threshold."""
    return execute_query(
        """SELECT p.*, c.name AS category_name
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.stock < %s AND p.stock > 0 AND p.is_active = TRUE
           ORDER BY p.stock ASC""",
        (threshold,),
        fetchall=True
    )


def get_out_of_stock_products():
    """Fetch products with zero stock."""
    return execute_query(
        """SELECT p.*, c.name AS category_name
           FROM products p
           JOIN categories c ON p.category_id = c.id
           WHERE p.stock = 0 AND p.is_active = TRUE
           ORDER BY p.name""",
        fetchall=True
    )


def get_product_count(active_only=True):
    """Get total product count."""
    query = "SELECT COUNT(*) AS count FROM products"
    if active_only:
        query += " WHERE is_active = TRUE"
    return execute_query(query, fetchone=True)['count']


def get_price_range():
    """Get min and max prices for the filter UI."""
    return execute_query(
        """SELECT MIN(price) AS min_price, MAX(price) AS max_price
           FROM products WHERE is_active = TRUE""",
        fetchone=True
    )
