# ==================================================
# Order Model — Database Operations & Transactions
# ==================================================
# Handles atomic order checkout transactions, stock deduction,
# payment creation, order history queries, and order cancellation.
# ==================================================

import random
import string
from models.db import get_db_connection, execute_query


def generate_transaction_id():
    """Generate a realistic transaction ID e.g., TXN9842105432."""
    digits = ''.join(random.choices(string.digits, k=10))
    return f"TXN{digits}"


def create_order_checkout(user_id, shipping_address, payment_method):
    """
    Execute an ATOMIC database transaction to place an order.

    Steps:
    1. Get cart items and validate cart is not empty.
    2. Validate stock for every item in cart.
    3. Calculate total amount.
    4. INSERT INTO orders (user_id, total_amount, shipping_address, order_status).
    5. INSERT INTO order_items (snapshot of product_id, quantity, price).
    6. UPDATE products SET stock = stock - quantity (deduct stock).
    7. INSERT INTO payments (order_id, payment_method, payment_status, transaction_id).
    8. DELETE FROM cart_items (clear cart).
    9. COMMIT transaction (rollback on any error).

    Returns: (order_id, None) on success, or (None, error_message) on failure.
    """
    from models.db import db_pool
    is_sqlite = db_pool is None
    conn = get_db_connection()

    if is_sqlite:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(dictionary=True)

    def run_sql(q, p=()):
        if is_sqlite:
            q = q.replace('%s', '?')
        cursor.execute(q, p)

    try:
        if not is_sqlite:
            conn.autocommit = False

        # 1. Fetch cart items
        run_sql(
            """SELECT ci.product_id, ci.quantity, p.name, p.price, p.stock, p.is_active
               FROM cart c
               JOIN cart_items ci ON c.id = ci.cart_id
               JOIN products p ON ci.product_id = p.id
               WHERE c.user_id = %s""",
            (user_id,)
        )
        cart_items = cursor.fetchall()
        if is_sqlite and cart_items:
            cart_items = [dict(r) for r in cart_items]

        if not cart_items:
            conn.rollback()
            return None, "Your cart is empty. Add products before checking out."

        # 2. Validate stock and product status
        total_amount = 0
        for item in cart_items:
            if not item['is_active']:
                conn.rollback()
                return None, f"Product '{item['name']}' is no longer available."
            if item['quantity'] > item['stock']:
                conn.rollback()
                return None, f"Insufficient stock for '{item['name']}'. Only {item['stock']} available."

            line_total = float(item['price']) * item['quantity']
            total_amount += line_total

        # 3. Create Order
        initial_order_status = 'Confirmed' if payment_method in ['Card', 'UPI'] else 'Pending'

        run_sql(
            """INSERT INTO orders (user_id, total_amount, order_status, shipping_address)
               VALUES (%s, %s, %s, %s)""",
            (user_id, total_amount, initial_order_status, shipping_address)
        )
        order_id = cursor.lastrowid

        # 4. Insert Order Items & Deduct Stock
        for item in cart_items:
            p_val = float(item['price'])
            run_sql(
                """INSERT INTO order_items (order_id, product_id, quantity, price, unit_price, subtotal)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (order_id, item['product_id'], item['quantity'], p_val, p_val, p_val * item['quantity'])
            )

            # Deduct stock
            run_sql(
                """UPDATE products SET stock = stock - %s WHERE id = %s""",
                (item['quantity'], item['product_id'])
            )

        # 5. Create Payment record
        payment_status = 'Completed' if payment_method in ['Card', 'UPI'] else 'Pending'
        transaction_id = generate_transaction_id()

        run_sql(
            """INSERT INTO payments (order_id, payment_method, payment_status, transaction_id, amount)
               VALUES (%s, %s, %s, %s, %s)""",
            (order_id, payment_method, payment_status, transaction_id, round(total_amount, 2))
        )

        # 6. Clear user's cart items
        run_sql(
            """DELETE FROM cart_items WHERE cart_id IN (SELECT id FROM cart WHERE user_id = %s)""",
            (user_id,)
        )

        # 7. Commit Transaction
        conn.commit()
        return order_id, None

    except Exception as e:
        conn.rollback()
        return None, f"Order placement failed: {str(e)}"

    finally:
        cursor.close()
        conn.close()


def get_user_orders(user_id):
    """
    Fetch all orders for a specific customer.
    Includes item count, payment method, payment status.
    Ordered by order_date DESC.
    """
    return execute_query(
        """SELECT o.id AS order_id, o.total_amount, o.order_status, o.shipping_address, o.order_date,
                  p.payment_method, p.payment_status, p.transaction_id,
                  COUNT(oi.id) AS item_count
           FROM orders o
           LEFT JOIN payments p ON o.id = p.order_id
           LEFT JOIN order_items oi ON o.id = oi.order_id
           WHERE o.user_id = %s
           GROUP BY o.id, o.total_amount, o.order_status, o.shipping_address, o.order_date,
                    p.payment_method, p.payment_status, p.transaction_id
           ORDER BY o.order_date DESC""",
        (user_id,),
        fetchall=True
    )


def get_order_by_id(order_id, user_id=None):
    """
    Fetch a single order by ID.
    If user_id is provided, verifies that the order belongs to that user (security check).
    Returns dict with order details and payment info.
    """
    query = """SELECT o.id AS order_id, o.user_id, o.total_amount, o.order_status,
                      o.shipping_address, o.order_date, o.updated_at,
                      u.name AS customer_name, u.email AS customer_email, u.phone AS customer_phone,
                      p.payment_method, p.payment_status, p.transaction_id, p.payment_date
               FROM orders o
               JOIN users u ON o.user_id = u.id
               LEFT JOIN payments p ON o.id = p.order_id
               WHERE o.id = %s"""
    params = [order_id]

    if user_id:
        query += " AND o.user_id = %s"
        params.append(user_id)

    return execute_query(query, tuple(params), fetchone=True)


def get_order_items(order_id):
    """
    Fetch itemized breakdown of an order.
    Returns product details and stored historical prices.
    """
    return execute_query(
        """SELECT oi.id, oi.quantity, oi.price AS price, oi.price AS purchase_price,
                  (oi.price * oi.quantity) AS line_total,
                  p.id AS product_id, p.name AS product_name, p.image_url,
                  c.name AS category_name
           FROM order_items oi
           JOIN products p ON oi.product_id = p.id
           JOIN categories c ON p.category_id = c.id
           WHERE oi.order_id = %s""",
        (order_id,),
        fetchall=True
    )


def cancel_order(order_id, user_id=None):
    """
    Cancel an order if status is 'Pending' or 'Confirmed'.
    Restores product stock and updates payment status.
    Executes inside an atomic transaction.
    """
    from models.db import db_pool
    is_sqlite = db_pool is None
    conn = get_db_connection()

    if is_sqlite:
        cursor = conn.cursor()
    else:
        cursor = conn.cursor(dictionary=True)

    def run_sql(q, p=()):
        if is_sqlite:
            q = q.replace('%s', '?')
        cursor.execute(q, p)

    try:
        if not is_sqlite:
            conn.autocommit = False

        # 1. Fetch order
        query = "SELECT id, order_status FROM orders WHERE id = %s"
        params = [order_id]
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)

        run_sql(query, tuple(params))
        order = cursor.fetchone()
        if is_sqlite and order:
            order = dict(order)

        if not order:
            conn.rollback()
            return False, "Order not found."

        if order['order_status'] not in ['Pending', 'Confirmed']:
            conn.rollback()
            return False, f"Order cannot be cancelled because it is already '{order['order_status']}'."

        # 2. Fetch order items to restore stock
        run_sql("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        if is_sqlite and items:
            items = [dict(r) for r in items]

        for item in items:
            run_sql(
                "UPDATE products SET stock = stock + %s WHERE id = %s",
                (item['quantity'], item['product_id'])
            )

        # 3. Update order status to 'Cancelled'
        run_sql(
            "UPDATE orders SET order_status = 'Cancelled' WHERE id = %s",
            (order_id,)
        )

        # 4. Update payment status to 'Refunded' or 'Failed'
        run_sql(
            """UPDATE payments
               SET payment_status = CASE
                   WHEN payment_status = 'Completed' THEN 'Refunded'
                   ELSE 'Failed'
               END
               WHERE order_id = %s""",
            (order_id,)
        )

        conn.commit()
        return True, "Order has been cancelled and stock has been restored."

    except Exception as e:
        conn.rollback()
        return False, f"Cancellation failed: {str(e)}"

    finally:
        cursor.close()
        conn.close()


def update_order_status(order_id, new_status):
    """
    Admin function to update order status.
    Valid statuses: 'Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled'.
    If changing to Cancelled, stock is restored.
    """
    valid_statuses = ['Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return False, "Invalid status value."

    if new_status == 'Cancelled':
        return cancel_order(order_id)

    # Normal status update
    execute_query(
        "UPDATE orders SET order_status = %s WHERE id = %s",
        (new_status, order_id),
        commit=True
    )

    # If delivered, mark payment completed if pending (e.g. COD)
    if new_status == 'Delivered':
        execute_query(
            "UPDATE payments SET payment_status = 'Completed' WHERE order_id = %s AND payment_status = 'Pending'",
            (order_id,),
            commit=True
        )

    return True, f"Order status updated to '{new_status}'."


def get_all_orders_admin(status_filter=None, customer_id=None):
    """Fetch all orders for admin management panel, optionally filtered by status and customer_id."""
    query = """SELECT o.id AS order_id, o.user_id, o.total_amount, o.order_status, o.order_date,
                      u.name AS customer_name, u.email AS customer_email,
                      p.payment_method, p.payment_status,
                      COUNT(oi.id) AS item_count
               FROM orders o
               JOIN users u ON o.user_id = u.id
               LEFT JOIN payments p ON o.id = p.order_id
               LEFT JOIN order_items oi ON o.id = oi.order_id"""

    conditions = []
    params = []
    if status_filter:
        conditions.append("o.order_status = %s")
        params.append(status_filter)
    if customer_id:
        conditions.append("o.user_id = %s")
        params.append(customer_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """ GROUP BY o.id, o.user_id, o.total_amount, o.order_status, o.order_date,
                          u.name, u.email, p.payment_method, p.payment_status
                 ORDER BY o.order_date DESC"""

    return execute_query(query, tuple(params), fetchall=True)
