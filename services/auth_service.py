# ==================================================
# Authentication Service — Business Logic
# ==================================================
# Handles password hashing and input validation
# separate from route handlers.
# ==================================================

import re
from werkzeug.security import generate_password_hash, check_password_hash


def validate_registration(name, email, password, confirm_password):
    """
    Validate registration form fields.
    Returns a list of error messages (empty list = valid).
    """
    errors = []

    # Name validation
    if not name or len(name.strip()) < 2:
        errors.append('Name must be at least 2 characters long.')
    elif len(name.strip()) > 100:
        errors.append('Name cannot exceed 100 characters.')

    # Email validation
    if not email:
        errors.append('Email address is required.')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Please enter a valid email address.')

    # Password validation
    if not password:
        errors.append('Password is required.')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters long.')

    # Confirm password
    if password != confirm_password:
        errors.append('Passwords do not match.')

    return errors


def validate_login(email, password):
    """
    Validate login form fields.
    Returns a list of error messages (empty list = valid).
    """
    errors = []

    if not email:
        errors.append('Email address is required.')

    if not password:
        errors.append('Password is required.')

    return errors


def validate_profile_update(name, phone):
    """
    Validate profile update fields.
    Returns a list of error messages (empty list = valid).
    """
    errors = []

    if not name or len(name.strip()) < 2:
        errors.append('Name must be at least 2 characters long.')

    if phone and not re.match(r'^[6-9]\d{9}$', phone):
        errors.append('Please enter a valid 10-digit Indian phone number.')

    return errors


def hash_password(password):
    """Generate a secure hash of the password using scrypt."""
    return generate_password_hash(password)


def verify_password(stored_hash, password):
    """Verify a password against its stored hash."""
    return check_password_hash(stored_hash, password)
