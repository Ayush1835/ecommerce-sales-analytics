# ==================================================
# Analytics Routes — Blueprint
# ==================================================
# Admin-facing sales & customer analytics blueprint.
# Connects Pandas/NumPy analytics services to Chart.js
# visualizations and CSV export endpoints.
# ==================================================

from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from utils.decorators import admin_required
from services.analytics_service import (
    get_monthly_revenue_analytics,
    get_category_sales_analytics,
    get_customer_spending_segmentation,
    get_payment_method_analytics,
    get_top_products_analytics,
    export_report_to_csv
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/overview')
@admin_required
def overview():
    """
    Main Analytics Overview Page.
    Fetches processed analytics datasets powered by Pandas and NumPy,
    and passes JSON-friendly structures to Chart.js charts in templates.
    """
    monthly = get_monthly_revenue_analytics()
    category = get_category_sales_analytics()
    customer = get_customer_spending_segmentation()
    payment = get_payment_method_analytics()
    products = get_top_products_analytics(limit=8)

    return render_template('analytics/overview.html',
                           monthly=monthly,
                           category=category,
                           customer=customer,
                           payment=payment,
                           products=products)


@analytics_bp.route('/export/<report_type>')
@admin_required
def export_csv(report_type):
    """
    Export analytics data to a CSV file.
    Uses Pandas to write CSV reports and streams them directly as a file download.
    """
    try:
        csv_buffer, filename = export_report_to_csv(report_type)
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    except Exception as e:
        flash(f"Failed to generate CSV report: {str(e)}", 'danger')
        return redirect(url_for('analytics.overview'))
