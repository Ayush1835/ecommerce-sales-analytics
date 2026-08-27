# ==================================================
# Order Routes — Blueprint
# ==================================================
# Customer-facing order processing blueprint.
# Handles checkout, order placement, order confirmation,
# order history, and order cancellation.
# ==================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.decorators import login_required
from models.cart import get_cart_details
from models.order import (
    create_order_checkout, get_user_orders, get_order_by_id,
    get_order_items, cancel_order
)
from models.user import get_user_by_id

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout page and order placement handler."""
    user_id = session['user']['id']
    items, subtotal, total_count = get_cart_details(user_id)

    # Cart must not be empty
    if not items or total_count == 0:
        flash('Your cart is empty. Please add items before checking out.', 'warning')
        return redirect(url_for('cart.view_cart'))

    # Fetch user for default delivery address
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        address = request.form.get('shipping_address', '').strip()
        payment_method = request.form.get('payment_method', 'UPI').strip()

        if not address:
            flash('Please enter a delivery address.', 'danger')
            return render_template('orders/checkout.html',
                                   items=items, subtotal=subtotal,
                                   total_count=total_count, user=user)

        valid_methods = ['UPI', 'Card', 'COD', 'Cash on Delivery']
        if payment_method not in valid_methods:
            flash('Invalid payment method selected.', 'danger')
            return render_template('orders/checkout.html',
                                   items=items, subtotal=subtotal,
                                   total_count=total_count, user=user)

        # Execute checkout transaction
        order_id, error = create_order_checkout(user_id, address, payment_method)

        if error:
            flash(error, 'danger')
            return render_template('orders/checkout.html',
                                   items=items, subtotal=subtotal,
                                   total_count=total_count, user=user)

        # Clear cart count in session
        session['cart_count'] = 0

        flash('🎉 Order placed successfully!', 'success')
        return redirect(url_for('orders.confirmation', order_id=order_id))

    return render_template('orders/checkout.html',
                           items=items,
                           subtotal=subtotal,
                           total_count=total_count,
                           user=user)


@orders_bp.route('/confirmation/<int:order_id>')
@login_required
def confirmation(order_id):
    """Order confirmation receipt page."""
    user_id = session['user']['id']
    order = get_order_by_id(order_id, user_id=user_id)

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('index'))

    items = get_order_items(order_id)

    return render_template('orders/confirmation.html',
                           order=order,
                           items=items)


@orders_bp.route('/my-orders')
@login_required
def my_orders():
    """Customer order history page."""
    user_id = session['user']['id']
    orders_list = get_user_orders(user_id)

    return render_template('orders/history.html', orders=orders_list)


@orders_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    """View detailed breakdown of a single order."""
    user_id = session['user']['id']

    # Admins can view any order, customers can only view their own
    if session['user'].get('role') == 'admin':
        order = get_order_by_id(order_id)
    else:
        order = get_order_by_id(order_id, user_id=user_id)

    if not order:
        flash('Order not found or access denied.', 'danger')
        return redirect(url_for('orders.my_orders'))

    items = get_order_items(order_id)

    return render_template('orders/detail.html',
                           order=order,
                           items=items)


@orders_bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel(order_id):
    """Cancel an existing pending/confirmed order."""
    user_id = session['user']['id']
    success, message = cancel_order(order_id, user_id=user_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('orders.detail', order_id=order_id))
