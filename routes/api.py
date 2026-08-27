# ==================================================
# REST API Blueprint — /api/v1/
# ==================================================
# Provides programmatic JSON REST API endpoints for
# products, categories, analytics summaries, and health checks.
# Adheres to standard REST conventions, JSON envelopes, and status codes.
# ==================================================

from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from models.product import (
    get_products_filtered, get_product_by_id, get_all_products
)
from models.category import (
    get_all_categories, get_category_by_id, get_categories_with_product_count
)
from models.admin import get_admin_dashboard_stats
from services.analytics_service import (
    get_monthly_revenue_analytics, get_category_sales_analytics
)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def json_response(status="success", data=None, message=None, code=200, **kwargs):
    """
    Standard JSON response helper.

    Response format:
    {
        "status": "success" | "error",
        "message": "...",
        "data": { ... } | [ ... ],
        ... (additional fields like total, count, timestamp)
    }
    """
    payload = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data

    for key, value in kwargs.items():
        payload[key] = value

    return jsonify(payload), code


# --------------------------------------------------
# API Documentation UI
# --------------------------------------------------
@api_bp.route('/docs')
def docs():
    """Render interactive API Documentation page."""
    return render_template('api_docs.html')


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------
@api_bp.route('/health')
def health_check():
    """Health check endpoint to verify API and database connectivity."""
    try:
        stats = get_admin_dashboard_stats()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return json_response(
        status="success" if db_status == "healthy" else "error",
        data={
            "api_version": "v1",
            "service": "ShopAnalytica REST API",
            "database_status": db_status
        },
        code=200 if db_status == "healthy" else 500
    )


# --------------------------------------------------
# Products Endpoints
# --------------------------------------------------
@api_bp.route('/products', methods=['GET'])
def get_products():
    """
    GET /api/v1/products
    Fetch list of active products with optional query parameter filtering.

    Query Params:
        category (int): Category ID filter
        search (str): Search term for name or description
        min_price (float): Minimum price
        max_price (float): Maximum price
        page (int): Page number (default: 1)
        per_page (int): Results per page (default: 12, max: 50)
        sort (str): Sort order (newest, price_low, price_high, rating, name_asc)
    """
    try:
        category_id = request.args.get('category', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'newest')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 50)

        products, total, total_pages = get_products_filtered(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
            sort_by=sort_by,
            page=page,
            per_page=per_page
        )

        return json_response(
            status="success",
            data=products,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Failed to fetch products: {str(e)}",
            code=500
        )


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_detail(product_id):
    """
    GET /api/v1/products/<product_id>
    Fetch details for a single product.
    """
    try:
        product = get_product_by_id(product_id)

        if not product or not product['is_active']:
            return json_response(
                status="error",
                message=f"Product with ID {product_id} not found.",
                code=404
            )

        return json_response(
            status="success",
            data=product,
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Error fetching product: {str(e)}",
            code=500
        )


# --------------------------------------------------
# Categories Endpoints
# --------------------------------------------------
@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    GET /api/v1/categories
    Fetch all product categories with product counts.
    """
    try:
        categories = get_categories_with_product_count()
        return json_response(
            status="success",
            data=categories,
            total=len(categories),
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Failed to fetch categories: {str(e)}",
            code=500
        )


@api_bp.route('/categories/<int:category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """
    GET /api/v1/categories/<category_id>/products
    Fetch all active products belonging to a specific category.
    """
    try:
        category = get_category_by_id(category_id)
        if not category:
            return json_response(
                status="error",
                message=f"Category with ID {category_id} not found.",
                code=404
            )

        products, total, total_pages = get_products_filtered(
            category_id=category_id,
            per_page=50
        )

        return json_response(
            status="success",
            category=category,
            data=products,
            total=total,
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Error fetching category products: {str(e)}",
            code=500
        )


# --------------------------------------------------
# Analytics & Summary Endpoints
# --------------------------------------------------
@api_bp.route('/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """
    GET /api/v1/analytics/summary
    Fetch overall platform KPI metrics summary.
    """
    try:
        stats = get_admin_dashboard_stats()
        return json_response(
            status="success",
            data=stats,
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Error fetching analytics summary: {str(e)}",
            code=500
        )


@api_bp.route('/analytics/monthly-sales', methods=['GET'])
def get_monthly_sales_api():
    """
    GET /api/v1/analytics/monthly-sales
    Fetch monthly sales revenue and order counts time series data.
    """
    try:
        analytics = get_monthly_revenue_analytics()
        data = {
            "months": analytics['months'],
            "revenue": analytics['revenue'],
            "orders": analytics['orders'],
            "aov": analytics['aov'],
            "mom_growth_pct": analytics['growth_rate'],
            "total_revenue": analytics['total_revenue'],
            "total_orders": analytics['total_orders']
        }
        return json_response(
            status="success",
            data=data,
            code=200
        )
    except Exception as e:
        return json_response(
            status="error",
            message=f"Error fetching monthly sales: {str(e)}",
            code=500
        )


# --------------------------------------------------
# 404 & 405 API Error Handlers
# --------------------------------------------------
@api_bp.app_errorhandler(404)
def api_not_found(e):
    if request.path.startswith('/api/'):
        return json_response(
            status="error",
            message="Endpoint not found. Check the URL path.",
            code=404
        )
    return e


@api_bp.app_errorhandler(405)
def api_method_not_allowed(e):
    if request.path.startswith('/api/'):
        return json_response(
            status="error",
            message="HTTP method not allowed for this endpoint.",
            code=405
        )
    return e
