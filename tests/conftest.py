# ==================================================
# Pytest Configuration & Test Fixtures
# ==================================================
# Provides reusable fixtures for Flask test client,
# mock sessions, customer login, and admin login.
# ==================================================

import os
import sys
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture
def app():
    """Create Flask application instance configured for testing."""
    test_app = create_app('development')
    test_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    return test_app


@pytest.fixture
def client(app):
    """Flask test client for issuing HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI runner for command testing."""
    return app.test_cli_runner()


@pytest.fixture
def customer_session(client):
    """Helper fixture to log in as a customer user."""
    with client.session_transaction() as sess:
        sess['user'] = {
            'id': 3,
            'name': 'Amit Patel',
            'email': 'amit.patel@example.com',
            'role': 'customer'
        }
        sess['cart_count'] = 2
    return client


@pytest.fixture
def admin_session(client):
    """Helper fixture to log in as an admin user."""
    with client.session_transaction() as sess:
        sess['user'] = {
            'id': 1,
            'name': 'Rajesh Kumar',
            'email': 'admin@ecommerce.com',
            'role': 'admin'
        }
    return client
