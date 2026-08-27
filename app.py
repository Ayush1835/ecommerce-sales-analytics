# ==================================================
# ShopAnalytica — Flask Application Entry Point
# ==================================================
# Uses the application factory pattern for clean
# configuration and testability.
# ==================================================

import os
from flask import Flask, render_template, session
from config import config


def create_app(config_name=None):
    """
    Flask application factory.

    Args:
        config_name: Configuration profile ('development' or 'production').
                     Defaults to FLASK_ENV environment variable.

    Returns:
        Flask app instance, fully configured with routes and error handlers.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # --------------------------------------------------
    # Security Middleware — inject security headers
    # --------------------------------------------------
    from utils.security import add_security_headers
    app.after_request(add_security_headers)

    # --------------------------------------------------
    # Context Processor — inject user data into all templates
    # --------------------------------------------------
    @app.context_processor
    def inject_globals():
        """Make current user info and cart count available in every template."""
        user = session.get('user')
        cart_count = 0
        if user and user.get('role') == 'customer':
            if 'cart_count' in session:
                cart_count = session['cart_count']
            else:
                try:
                    from models.cart import get_cart_count
                    cart_count = get_cart_count(user['id'])
                    session['cart_count'] = cart_count
                except Exception:
                    cart_count = 0

        return dict(
            current_user=user,
            cart_count=cart_count
        )

    # --------------------------------------------------
    # Homepage Route
    # --------------------------------------------------
    @app.route('/')
    def index():
        """
        Render the homepage with live database statistics.
        This verifies that Flask ↔ MySQL connection works.
        """
        from models.db import execute_query

        stats = {}
        categories = []

        try:
            # Fetch platform statistics from the database
            stats['products'] = execute_query(
                "SELECT COUNT(*) AS count FROM products WHERE is_active = TRUE",
                fetchone=True
            )['count']

            stats['categories'] = execute_query(
                "SELECT COUNT(*) AS count FROM categories",
                fetchone=True
            )['count']

            stats['orders'] = execute_query(
                "SELECT COUNT(*) AS count FROM orders",
                fetchone=True
            )['count']

            stats['customers'] = execute_query(
                "SELECT COUNT(*) AS count FROM users WHERE role = 'customer'",
                fetchone=True
            )['count']

            stats['delivered'] = execute_query(
                "SELECT COUNT(*) AS count FROM orders WHERE order_status = 'Delivered'",
                fetchone=True
            )['count']

            revenue_result = execute_query(
                "SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders WHERE order_status = 'Delivered'",
                fetchone=True
            )
            stats['revenue'] = float(revenue_result['total'])

            # Fetch categories with product counts
            categories = execute_query(
                """SELECT c.id, c.name,
                          COUNT(p.id) AS product_count
                   FROM categories c
                   LEFT JOIN products p ON c.id = p.category_id AND p.is_active = TRUE
                   GROUP BY c.id, c.name
                   ORDER BY c.name""",
                fetchall=True
            )

        except Exception as e:
            # If DB is not available, show empty stats
            app.logger.error(f"Database error on homepage: {e}")
            stats = {
                'products': 0, 'categories': 0, 'orders': 0,
                'customers': 0, 'delivered': 0, 'revenue': 0
            }

        return render_template('index.html', stats=stats, categories=categories)

    # --------------------------------------------------
    # Error Handlers
    # --------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # --------------------------------------------------
    # Register Blueprints
    # --------------------------------------------------
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.products import products_bp
    app.register_blueprint(products_bp)

    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from routes.cart import cart_bp
    app.register_blueprint(cart_bp)

    from routes.orders import orders_bp
    app.register_blueprint(orders_bp)

    from routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp)

    from routes.api import api_bp
    app.register_blueprint(api_bp)

    return app


# --------------------------------------------------
# Run the application
# --------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
