# ==================================================
# Cart Routes — Blueprint
# ==================================================
# Customer-facing shopping cart blueprint.
# Handles viewing cart, adding products, updating
# quantities, removing items, and clearing cart.
# ==================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.decorators import login_required
from models.cart import (
    get_cart_details, add_to_cart, update_cart_item_quantity,
    remove_from_cart, clear_cart, get_cart_count
)

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def update_session_cart_count():
    """Helper to update cart count in session for navbar badge."""
    if 'user' in session:
        session['cart_count'] = get_cart_count(session['user']['id'])


@cart_bp.route('/')
@login_required
def view_cart():
    """Display user's shopping cart with items and order summary."""
    user_id = session['user']['id']
    items, subtotal, total_count = get_cart_details(user_id)
    update_session_cart_count()

    return render_template('cart/cart.html',
                           items=items,
                           subtotal=subtotal,
                           total_count=total_count)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    """Add a product to cart."""
    user_id = session['user']['id']
    quantity = request.form.get('quantity', 1, type=int)

    if quantity < 1:
        quantity = 1

    success, message = add_to_cart(user_id, product_id, quantity)
    update_session_cart_count()

    if success:
        flash(message, 'success')
    else:
        flash(message, 'warning')

    # Redirect to referrer page or cart page
    next_page = request.referrer or url_for('products.product_list')
    return redirect(next_page)


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update(item_id):
    """Update item quantity in cart."""
    user_id = session['user']['id']
    quantity = request.form.get('quantity', 1, type=int)

    success, message = update_cart_item_quantity(user_id, item_id, quantity)
    update_session_cart_count()

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove(item_id):
    """Remove item from cart."""
    user_id = session['user']['id']
    success, message = remove_from_cart(user_id, item_id)
    update_session_cart_count()

    flash(message, 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear():
    """Clear all items from user's cart."""
    user_id = session['user']['id']
    success, message = clear_cart(user_id)
    update_session_cart_count()

    flash(message, 'info')
    return redirect(url_for('cart.view_cart'))
