# ==================================================
# Test Suite — Authentication & Authorization
# ==================================================
# Tests registration, login, logout, profile updates,
# and decorator authorization protections.
# ==================================================

def test_login_page_loads(client):
    """Test that login page returns status 200."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_register_page_loads(client):
    """Test that register page returns status 200."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data


def test_valid_login(client):
    """Test successful customer login."""
    response = client.post('/auth/login', data={
        'email': 'amit.patel@example.com',
        'password': 'Password@123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back' in response.data or b'ShopAnalytica' in response.data


def test_invalid_login_password(client):
    """Test login failure with wrong password."""
    response = client.post('/auth/login', data={
        'email': 'amit.patel@example.com',
        'password': 'WrongPassword999'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_nonexistent_user_login(client):
    """Test login failure with non-existent email."""
    response = client.post('/auth/login', data={
        'email': 'nobody_exists_12345@example.com',
        'password': 'Password@123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_logout(customer_session):
    """Test logout clears session."""
    response = customer_session.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data or b'Sign In' in response.data


def test_profile_requires_login(client):
    """Test that profile page redirects unauthenticated users."""
    response = client.get('/auth/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_authenticated_profile_view(customer_session):
    """Test viewing profile when logged in."""
    response = customer_session.get('/auth/profile')
    assert response.status_code == 200
    assert b'Amit Patel' in response.data
    assert b'amit.patel@example.com' in response.data


def test_admin_route_protection_for_customer(customer_session):
    """Test that customers cannot access admin routes."""
    response = customer_session.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Access denied' in response.data


def test_admin_route_access_for_admin(admin_session):
    """Test that admins can access admin dashboard."""
    response = admin_session.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data
