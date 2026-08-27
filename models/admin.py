# ==================================================
# Admin Model — Analytics Summary Queries
# ==================================================
# Provides high-level dashboard metrics, KPI stats,
# recent activity, and low-stock alerts for admins.
# ==================================================

from models.db import execute_query


def get_admin_dashboard_stats():
    """
    Fetch overall platform metrics for the admin dashboard.
    Returns a dictionary of key performance indicators (KPIs).
    """
    stats = {}

    # Total Revenue (from Delivered orders)
    revenue_res = execute_query(
        "SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders WHERE order_status = 'Delivered'",
        fetchone=True
    )
    stats['total_revenue'] = float(revenue_res['total'])

    # Total Orders count
    orders_res = execute_query(
        "SELECT COUNT(*) AS count FROM orders",
        fetchone=True
    )
    stats['total_orders'] = orders_res['count']

    # Pending Orders count
    pending_res = execute_query(
        "SELECT COUNT(*) AS count FROM orders WHERE order_status = 'Pending'",
        fetchone=True
    )
    stats['pending_orders'] = pending_res['count']

    # Delivered Orders count
    delivered_res = execute_query(
        "SELECT COUNT(*) AS count FROM orders WHERE order_status = 'Delivered'",
        fetchone=True
    )
    stats['delivered_orders'] = delivered_res['count']

    # Customer count
    cust_res = execute_query(
        "SELECT COUNT(*) AS count FROM users WHERE role = 'customer'",
        fetchone=True
    )
    stats['total_customers'] = cust_res['count']

    # Active product count
    prod_res = execute_query(
        "SELECT COUNT(*) AS count FROM products WHERE is_active = TRUE",
        fetchone=True
    )
    stats['active_products'] = prod_res['count']

    # Low stock alert count (stock < 10)
    low_stock_res = execute_query(
        "SELECT COUNT(*) AS count FROM products WHERE stock < 10 AND is_active = TRUE",
        fetchone=True
    )
    stats['low_stock_count'] = low_stock_res['count']

    # Out of stock count
    out_stock_res = execute_query(
        "SELECT COUNT(*) AS count FROM products WHERE stock = 0 AND is_active = TRUE",
        fetchone=True
    )
    stats['out_of_stock_count'] = out_stock_res['count']

    return stats


def get_recent_orders_summary(limit=8):
    """Fetch the most recent orders for the dashboard widget."""
    return execute_query(
        """SELECT o.id AS order_id, o.total_amount, o.order_status, o.order_date,
                  u.name AS customer_name, u.email AS customer_email,
                  p.payment_method, p.payment_status
           FROM orders o
           JOIN users u ON o.user_id = u.id
           LEFT JOIN payments p ON o.id = p.order_id
           ORDER BY o.order_date DESC
           LIMIT %s""",
        (limit,),
        fetchall=True
    )


def get_top_selling_products_summary(limit=5):
    """Fetch top products by quantity sold."""
    return execute_query(
        """SELECT p.id, p.name, p.price, p.image_url, c.name AS category_name,
                  SUM(oi.quantity) AS total_sold,
                  SUM(oi.price * oi.quantity) AS total_revenue
           FROM order_items oi
           JOIN products p ON oi.product_id = p.id
           JOIN categories c ON p.category_id = c.id
           JOIN orders o ON oi.order_id = o.id
           WHERE o.order_status != 'Cancelled'
           GROUP BY p.id, p.name, p.price, p.image_url, c.name
           ORDER BY total_sold DESC
           LIMIT %s""",
        (limit,),
        fetchall=True
    )
