# ==================================================
# Cart Model — Database Operations
# ==================================================
# Handles cart creation, item management, quantity
# updates, and stock validation for customer users.
# ==================================================

from models.db import execute_query, get_db_connection
from models.product import get_product_by_id


def get_or_create_cart(user_id):
    """
    Get user's cart ID, or create one if it doesn't exist.
    Enforces one cart per user via UNIQUE constraint on user_id.
    """
    cart = execute_query(
        "SELECT id FROM cart WHERE user_id = %s",
        (user_id,),
        fetchone=True
    )

    if cart:
        return cart['id']

    # Create new cart
    cart_id = execute_query(
        "INSERT INTO cart (user_id) VALUES (%s)",
        (user_id,),
        commit=True
    )
    return cart_id


def get_cart_details(user_id):
    """
    Fetch full cart details for a user.
    Returns (items_list, subtotal_amount, total_item_count).
    Each item includes product details, current price, line total, and available stock.
    """
    cart_id = get_or_create_cart(user_id)

    items = execute_query(
        """SELECT ci.id AS item_id, ci.quantity, ci.created_at,
                  p.id AS product_id, p.name AS product_name,
                  p.price, p.stock, p.image_url, p.is_active,
                  c.name AS category_name,
                  (p.price * ci.quantity) AS line_total
           FROM cart_items ci
           JOIN products p ON ci.product_id = p.id
           JOIN categories c ON p.category_id = c.id
           WHERE ci.cart_id = %s
           ORDER BY ci.created_at DESC""",
        (cart_id,),
        fetchall=True
    )

    subtotal = sum(float(item['line_total']) for item in items)
    total_count = sum(item['quantity'] for item in items)

    return items, subtotal, total_count


def add_to_cart(user_id, product_id, quantity=1):
    """
    Add a product to the user's cart.
    If product already exists in cart, increments quantity up to available stock.
    Returns (success_boolean, message).
    """
    # 1. Validate product exists and is active
    product = get_product_by_id(product_id)
    if not product or not product['is_active']:
        return False, "Product is not available."

    if product['stock'] <= 0:
        return False, f"Sorry, '{product['name']}' is out of stock."

    cart_id = get_or_create_cart(user_id)

    # 2. Check if item already in cart
    existing_item = execute_query(
        "SELECT id, quantity FROM cart_items WHERE cart_id = %s AND product_id = %s",
        (cart_id, product_id),
        fetchone=True
    )

    if existing_item:
        new_qty = existing_item['quantity'] + quantity
        if new_qty > product['stock']:
            return False, f"Cannot add more. Only {product['stock']} units of '{product['name']}' available in stock (you already have {existing_item['quantity']} in cart)."

        execute_query(
            "UPDATE cart_items SET quantity = %s WHERE id = %s",
            (new_qty, existing_item['id']),
            commit=True
        )
        return True, f"Updated '{product['name']}' quantity to {new_qty} in cart."

    else:
        if quantity > product['stock']:
            return False, f"Cannot add {quantity} units. Only {product['stock']} available in stock."

        execute_query(
            "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (%s, %s, %s)",
            (cart_id, product_id, quantity),
            commit=True
        )
        return True, f"Added '{product['name']}' to your cart!"


def update_cart_item_quantity(user_id, item_id, quantity):
    """
    Update quantity of an item in cart.
    If quantity <= 0, removes the item.
    Validates against product stock.
    Returns (success_boolean, message).
    """
    if quantity <= 0:
        return remove_from_cart(user_id, item_id)

    # Verify item belongs to user's cart
    cart_id = get_or_create_cart(user_id)
    item = execute_query(
        """SELECT ci.id, ci.quantity, p.name, p.stock
           FROM cart_items ci
           JOIN products p ON ci.product_id = p.id
           WHERE ci.id = %s AND ci.cart_id = %s""",
        (item_id, cart_id),
        fetchone=True
    )

    if not item:
        return False, "Item not found in your cart."

    if quantity > item['stock']:
        return False, f"Cannot set quantity to {quantity}. Only {item['stock']} units of '{item['name']}' available."

    execute_query(
        "UPDATE cart_items SET quantity = %s WHERE id = %s",
        (quantity, item_id),
        commit=True
    )
    return True, f"Updated quantity for '{item['name']}'."


def remove_from_cart(user_id, item_id):
    """Remove a single item from the cart."""
    cart_id = get_or_create_cart(user_id)
    execute_query(
        "DELETE FROM cart_items WHERE id = %s AND cart_id = %s",
        (item_id, cart_id),
        commit=True
    )
    return True, "Item removed from cart."


def clear_cart(user_id):
    """Clear all items from user's cart."""
    cart_id = get_or_create_cart(user_id)
    execute_query(
        "DELETE FROM cart_items WHERE cart_id = %s",
        (cart_id,),
        commit=True
    )
    return True, "Cart cleared."


def get_cart_count(user_id):
    """Get total quantity of items in user's cart (for badge)."""
    if not user_id:
        return 0
    cart_id = get_or_create_cart(user_id)
    result = execute_query(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM cart_items WHERE cart_id = %s",
        (cart_id,),
        fetchone=True
    )
    return int(result['total'])
