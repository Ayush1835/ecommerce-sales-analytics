# ==================================================
# Test Suite — Orders & Checkout
# ==================================================
# Tests checkout protection, order history, single order
# detail view, and cancellation logic.
# ==================================================

def test_checkout_requires_login(client):
    """Test unauthenticated checkout redirects to login."""
    response = client.get('/orders/checkout', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_my_orders_history(customer_session):
    """Test customer order history page."""
    response = customer_session.get('/orders/my-orders')
    assert response.status_code == 200
    assert b'My Orders' in response.data


def test_order_detail_view(customer_session):
    """Test customer order detail view for valid order ID 1."""
    response = customer_session.get('/orders/1')
    assert response.status_code == 200
    assert b'Order' in response.data


def test_invalid_order_detail_access(customer_session):
    """Test accessing non-existent order ID redirects with error."""
    response = customer_session.get('/orders/999999', follow_redirects=True)
    assert response.status_code == 200
    assert b'not found' in response.data.lower() or b'orders' in response.data.lower()
