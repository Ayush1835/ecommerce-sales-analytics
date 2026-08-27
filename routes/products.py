# ==================================================
# Product Routes — Customer-Facing Blueprint
# ==================================================
# Handles product browsing, searching, filtering,
# sorting, and product detail pages.
# ==================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.product import get_products_filtered, get_product_by_id, get_price_range
from models.category import get_all_categories

products_bp = Blueprint('products', __name__, url_prefix='/products')


@products_bp.route('/')
def product_list():
    """
    Display products with filtering, searching, sorting, and pagination.

    Query parameters:
        category  — Filter by category ID
        min_price — Minimum price filter
        max_price — Maximum price filter
        search    — Search by name or description (LIKE query)
        sort      — Sort order (newest, price_low, price_high, rating, name_asc)
        in_stock  — Show only in-stock products
        page      — Page number for pagination
    """
    # Collect filter parameters from URL query string
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'newest')
    in_stock_only = request.args.get('in_stock') == '1'
    page = request.args.get('page', 1, type=int)

    # Ensure valid page number
    if page < 1:
        page = 1

    # Fetch filtered products with pagination
    products, total, total_pages = get_products_filtered(
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        page=page,
        per_page=12
    )

    # Fetch all categories for the filter sidebar
    categories = get_all_categories()

    # Get price range for the filter UI
    price_range = get_price_range()

    return render_template('products/products.html',
                           products=products,
                           categories=categories,
                           total=total,
                           page=page,
                           total_pages=total_pages,
                           price_range=price_range,
                           # Pass current filter values back to template
                           current_category=category_id,
                           current_min_price=min_price,
                           current_max_price=max_price,
                           current_search=search,
                           current_sort=sort_by,
                           current_in_stock=in_stock_only)


@products_bp.route('/<int:product_id>')
def product_detail(product_id):
    """Display a single product with details and related products."""
    product = get_product_by_id(product_id)

    if not product or not product['is_active']:
        flash('Product not found or is no longer available.', 'warning')
        return redirect(url_for('products.product_list'))

    # Get related products from the same category
    related, _, _ = get_products_filtered(
        category_id=product['category_id'],
        per_page=5
    )
    # Exclude the current product from related list
    related_products = [p for p in related if p['id'] != product_id][:4]

    return render_template('products/product_detail.html',
                           product=product,
                           related_products=related_products)
