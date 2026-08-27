# ==================================================
# Test Suite — Product Catalog & Browsing
# ==================================================
# Tests homepage, product catalog listing, search,
# filtering, detail view, and admin product management.
# ==================================================

def test_homepage_loads(client):
    """Test homepage loads successfully with live DB stats."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'ShopAnalytica' in response.data


def test_products_list_loads(client):
    """Test catalog products list page loads."""
    response = client.get('/products/')
    assert response.status_code == 200
    assert b'Products' in response.data or b'Shop by Category' in response.data


def test_product_search_filter(client):
    """Test product search query parameter."""
    response = client.get('/products/?search=Samsung')
    assert response.status_code == 200
    assert b'Samsung' in response.data or b'products' in response.data


def test_product_category_filter(client):
    """Test filtering products by category ID."""
    response = client.get('/products/?category=1')
    assert response.status_code == 200


def test_product_detail_page(client):
    """Test product detail page for valid product ID 1."""
    response = client.get('/products/1')
    assert response.status_code == 200
    assert b'Add to Cart' in response.data or b'Product' in response.data


def test_invalid_product_detail(client):
    """Test product detail page for non-existent product ID."""
    response = client.get('/products/999999', follow_redirects=True)
    assert response.status_code == 200
    assert b'Product not found' in response.data


def test_admin_products_list(admin_session):
    """Test admin product management page."""
    response = admin_session.get('/admin/products')
    assert response.status_code == 200
    assert b'Product Management' in response.data


def test_admin_add_product_page(admin_session):
    """Test admin add product page loads."""
    response = admin_session.get('/admin/products/add')
    assert response.status_code == 200
    assert b'Add New Product' in response.data
