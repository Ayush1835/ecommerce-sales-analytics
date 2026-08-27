# ==================================================
# Route Decorators
# ==================================================
# Reusable decorators for authentication and
# authorization across all route blueprints.
# ==================================================

from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    """
    Decorator that ensures the user is logged in.
    Redirects to the login page if no active session exists.
    Preserves the original URL in the 'next' parameter so the user
    is redirected back after successful login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator that ensures the user is logged in AND has admin role.
    First checks for authentication, then checks for admin privileges.
    Non-admin users are redirected to the homepage with an error message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session['user'].get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
