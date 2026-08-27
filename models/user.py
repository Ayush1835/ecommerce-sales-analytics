# ==================================================
# User Model — Database Operations
# ==================================================
# All user-related database queries in one place.
# Uses parameterized queries for SQL injection prevention.
# ==================================================

from models.db import execute_query


def get_user_by_email(email):
    """Fetch a user by email (used during login)."""
    return execute_query(
        "SELECT * FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )


def get_user_by_id(user_id):
    """Fetch a user by ID (excludes password_hash for safety)."""
    return execute_query(
        """SELECT id, name, email, role, phone, address, created_at, updated_at
           FROM users WHERE id = %s""",
        (user_id,),
        fetchone=True
    )


def create_user(name, email, password_hash, phone=None, address=None):
    """
    Create a new customer account.
    Returns the new user's ID.
    """
    return execute_query(
        """INSERT INTO users (name, email, password_hash, role, phone, address)
           VALUES (%s, %s, %s, 'customer', %s, %s)""",
        (name, email, password_hash, phone, address),
        commit=True
    )


def email_exists(email):
    """Check if an email is already registered."""
    result = execute_query(
        "SELECT COUNT(*) AS count FROM users WHERE email = %s",
        (email,),
        fetchone=True
    )
    return result['count'] > 0


def update_user_profile(user_id, name, phone, address):
    """Update a user's profile information."""
    return execute_query(
        "UPDATE users SET name = %s, phone = %s, address = %s WHERE id = %s",
        (name, phone, address, user_id),
        commit=True
    )


def update_user_password(user_id, password_hash):
    """Update a user's password."""
    return execute_query(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (password_hash, user_id),
        commit=True
    )


def get_all_customers():
    """Fetch all customer users for admin panel."""
    return execute_query(
        """SELECT u.id, u.name, u.email, u.phone, u.address, u.created_at,
                  COUNT(o.id) AS order_count,
                  COALESCE(SUM(o.total_amount), 0) AS total_spent
           FROM users u
           LEFT JOIN orders o ON u.id = o.user_id AND o.order_status != 'Cancelled'
           WHERE u.role = 'customer'
           GROUP BY u.id, u.name, u.email, u.phone, u.address, u.created_at
           ORDER BY u.created_at DESC""",
        fetchall=True
    )


def get_customer_count():
    """Get total number of customers."""
    result = execute_query(
        "SELECT COUNT(*) AS count FROM users WHERE role = 'customer'",
        fetchone=True
    )
    return result['count']
