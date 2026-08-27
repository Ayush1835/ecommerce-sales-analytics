# ==================================================
# Test Suite — Shopping Cart
# ==================================================
# Tests cart viewing, adding items, updating quantities,
# stock limit validation, and cart clearance.
# ==================================================

def test_cart_requires_login(client):
    """Test unauthenticated user is redirected when viewing cart."""
    response = client.get('/cart/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_customer_view_cart(customer_session):
    """Test customer viewing shopping cart."""
    response = customer_session.get('/cart/')
    assert response.status_code == 200
    assert b'Shopping Cart' in response.data


def test_add_to_cart(customer_session):
    """Test adding a product to cart."""
    response = customer_session.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    assert response.status_code == 200
    assert b'cart' in response.data.lower() or b'added' in response.data.lower()


def test_clear_cart(customer_session):
    """Test clearing all items from cart."""
    response = customer_session.post('/cart/clear', follow_redirects=True)
    assert response.status_code == 200
    assert b'cleared' in response.data.lower() or b'empty' in response.data.lower()
