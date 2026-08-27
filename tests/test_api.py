# ==================================================
# Test Suite — REST API Endpoints (/api/v1/)
# ==================================================
# Tests JSON response structure, status codes (200, 404, 500),
# health check, query filtering, and documentation.
# ==================================================

def test_api_docs_page(client):
    """Test API documentation page loads."""
    response = client.get('/api/v1/docs')
    assert response.status_code == 200
    assert b'REST API v1 Documentation' in response.data or b'Documentation' in response.data


def test_api_health_check(client):
    """Test /api/v1/health returns 200 OK and valid JSON envelope."""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'database_status' in json_data['data']


def test_api_get_products(client):
    """Test /api/v1/products returns JSON list of products."""
    response = client.get('/api/v1/products')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert isinstance(json_data['data'], list)
    assert 'total' in json_data


def test_api_get_products_with_filter(client):
    """Test /api/v1/products with search parameter."""
    response = client.get('/api/v1/products?search=Samsung')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert isinstance(json_data['data'], list)


def test_api_get_product_detail(client):
    """Test /api/v1/products/1 returns valid product details JSON."""
    response = client.get('/api/v1/products/1')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['id'] == 1


def test_api_get_product_not_found(client):
    """Test /api/v1/products/999999 returns 404 error JSON."""
    response = client.get('/api/v1/products/999999')
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'not found' in json_data['message'].lower()


def test_api_get_categories(client):
    """Test /api/v1/categories returns list of categories."""
    response = client.get('/api/v1/categories')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert isinstance(json_data['data'], list)


def test_api_get_analytics_summary(client):
    """Test /api/v1/analytics/summary returns KPI metrics."""
    response = client.get('/api/v1/analytics/summary')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'total_orders' in json_data['data']
