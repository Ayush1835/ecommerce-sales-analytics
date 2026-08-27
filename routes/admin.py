# ==================================================
# Admin Routes — Blueprint
# ==================================================
# Admin panel for dashboard metrics, product management,
# category management, customer listing, and order status updates.
# All routes protected by @admin_required decorator.
# ==================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.decorators import admin_required
from models.admin import (
    get_admin_dashboard_stats, get_recent_orders_summary,
    get_top_selling_products_summary
)
from models.product import (
    get_all_products, get_product_by_id, create_product,
    update_product, deactivate_product, activate_product,
    get_low_stock_products
)
from models.category import (
    get_all_categories, get_category_by_id, create_category,
    update_category, delete_category, category_name_exists,
    get_categories_with_product_count
)
from models.user import get_all_customers, get_user_by_id
from models.order import (
    get_all_orders_admin, get_order_by_id,
    get_order_items, update_order_status
)
from mysql.connector import Error as MySQLError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==================================================
# DASHBOARD OVERVIEW
# ==================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard overview with KPI cards and recent activity."""
    stats = get_admin_dashboard_stats()
    recent_orders = get_recent_orders_summary(limit=8)
    top_products = get_top_selling_products_summary(limit=5)
    low_stock = get_low_stock_products(threshold=10)

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_orders=recent_orders,
                           top_products=top_products,
                           low_stock=low_stock)


# ==================================================
# ORDER MANAGEMENT
# ==================================================

@admin_bp.route('/orders')
@admin_required
def orders():
    """Admin order list with status filter and customer filter."""
    status_filter = request.args.get('status', '').strip()
    customer_id = request.args.get('customer_id', type=int)

    if status_filter not in ['Pending', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled']:
        status_filter = None

    order_list = get_all_orders_admin(status_filter=status_filter, customer_id=customer_id)
    filtered_customer = get_user_by_id(customer_id) if customer_id else None

    return render_template('admin/orders.html',
                           orders=order_list,
                           current_status=status_filter or 'All',
                           customer_id=customer_id,
                           filtered_customer=filtered_customer)


@admin_bp.route('/orders/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_status(order_id):
    """Update status of an order."""
    new_status = request.form.get('order_status', '').strip() or request.form.get('status', '').strip()
    success, message = update_order_status(order_id, new_status)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    next_url = request.referrer or url_for('admin.orders')
    return redirect(next_url)


@admin_bp.route('/orders/auto-advance-all', methods=['POST'])
@admin_required
def auto_advance_orders():
    """Auto-advance all active order lifecycles (Pending -> Confirmed -> Shipped -> Delivered)."""
    order_list = get_all_orders_admin()
    advanced_count = 0
    
    next_stage = {
        'Pending': 'Confirmed',
        'Confirmed': 'Shipped',
        'Shipped': 'Delivered'
    }
    
    for o in order_list:
        curr = o.get('order_status')
        if curr in next_stage:
            update_order_status(o['order_id'], next_stage[curr])
            advanced_count += 1
            
    flash(f'Automated Pipeline Execution Completed! Advanced {advanced_count} order(s) to their next lifecycle stage.', 'success')
    return redirect(url_for('admin.orders'))


# ==================================================
# PRODUCT MANAGEMENT
# ==================================================

@admin_bp.route('/products')
@admin_required
def products():
    """List all products with optional search filter."""
    search = request.args.get('search', '').strip()
    all_products = get_all_products()

    if search:
        all_products = [
            p for p in all_products
            if search.lower() in p['name'].lower()
            or search.lower() in (p.get('category_name', '') or '').lower()
        ]

    return render_template('admin/products.html',
                           products=all_products, search=search)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add a new product to the catalog."""
    categories = get_all_categories()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0')
        stock = request.form.get('stock', '0')
        image_url = request.form.get('image_url', '').strip()

        errors = []
        if not name:
            errors.append('Product name is required.')
        if not category_id:
            errors.append('Please select a category.')

        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Price must be greater than zero.')
        except ValueError:
            errors.append('Invalid price value.')
            price_val = 0

        try:
            stock_val = int(stock)
            if stock_val < 0:
                errors.append('Stock cannot be negative.')
        except ValueError:
            errors.append('Invalid stock value.')
            stock_val = 0

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/add_product.html',
                                   categories=categories,
                                   name=name, category_id=category_id,
                                   description=description, price=price,
                                   stock=stock, image_url=image_url)

        if not image_url:
            slug = name.lower().replace(' ', '-').replace("'", "")
            image_url = f'https://picsum.photos/seed/{slug}/400/400'

        create_product(
            category_id, name, description,
            price_val, stock_val, image_url
        )
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/add_product.html', categories=categories)


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit an existing product."""
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))

    categories = get_all_categories()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0')
        stock = request.form.get('stock', '0')
        image_url = request.form.get('image_url', '').strip()
        is_active = request.form.get('is_active') == 'on'

        errors = []
        if not name:
            errors.append('Product name is required.')
        if not category_id:
            errors.append('Please select a category.')

        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Price must be greater than zero.')
        except ValueError:
            errors.append('Invalid price value.')
            price_val = 0

        try:
            stock_val = int(stock)
            if stock_val < 0:
                errors.append('Stock cannot be negative.')
        except ValueError:
            errors.append('Invalid stock value.')
            stock_val = 0

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/edit_product.html',
                                   product=product, categories=categories)

        update_product(
            product_id, category_id, name, description,
            price_val, stock_val, image_url or product['image_url'],
            is_active
        )
        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/edit_product.html',
                           product=product, categories=categories)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Soft-delete (deactivate) a product."""
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
    else:
        deactivate_product(product_id)
        flash(f'Product "{product["name"]}" has been deactivated.', 'warning')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/activate/<int:product_id>', methods=['POST'])
@admin_required
def reactivate_product(product_id):
    """Reactivate a deactivated product."""
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
    else:
        activate_product(product_id)
        flash(f'Product "{product["name"]}" has been reactivated.', 'success')
    return redirect(url_for('admin.products'))


# ==================================================
# CATEGORY MANAGEMENT
# ==================================================

@admin_bp.route('/categories')
@admin_required
def categories():
    """List all categories with product counts."""
    cats = get_categories_with_product_count()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    """Add a new category."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories'))

    if category_name_exists(name):
        flash(f'Category "{name}" already exists.', 'danger')
        return redirect(url_for('admin.categories'))

    create_category(name, description or None)
    flash(f'Category "{name}" created successfully!', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/edit/<int:category_id>', methods=['POST'])
@admin_required
def edit_category(category_id):
    """Edit an existing category."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.categories'))

    if category_name_exists(name, exclude_id=category_id):
        flash(f'Category "{name}" already exists.', 'danger')
        return redirect(url_for('admin.categories'))

    update_category(category_id, name, description or None)
    flash(f'Category "{name}" updated successfully!', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_cat(category_id):
    """Delete a category (fails if products reference it)."""
    category = get_category_by_id(category_id)
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('admin.categories'))

    try:
        delete_category(category_id)
        flash(f'Category "{category["name"]}" deleted.', 'success')
    except MySQLError:
        flash(
            f'Cannot delete "{category["name"]}" — it still has products. '
            f'Remove or reassign its products first.',
            'danger'
        )
    return redirect(url_for('admin.categories'))


# ==================================================
# CUSTOMER MANAGEMENT
# ==================================================

@admin_bp.route('/customers')
@admin_required
def customers():
    """List all customers with order stats."""
    customer_list = get_all_customers()
    return render_template('admin/customers.html', customers=customer_list)
