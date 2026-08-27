# ==================================================
# Data Analytics Service — Pandas & NumPy
# ==================================================
# Connects to MySQL, extracts data into Pandas DataFrames,
# performs statistical analysis using NumPy, calculates MoM growth,
# customer segmentation, and exports downloadable CSV reports.
# ==================================================

import os
import pandas as pd
import numpy as np
from models.db import get_db_connection


def get_monthly_revenue_analytics():
    """
    Extract monthly sales data using Pandas.
    Calculates monthly revenue, order count, Average Order Value (AOV),
    and Month-over-Month (MoM) revenue growth rates using NumPy/Pandas.
    """
    conn = get_db_connection()
    try:
        query = """
            SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
                   COUNT(id) AS order_count,
                   SUM(total_amount) AS total_revenue
            FROM orders
            WHERE order_status != 'Cancelled'
            GROUP BY DATE_FORMAT(order_date, '%Y-%m')
            ORDER BY month ASC
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return {
            'months': [], 'revenue': [], 'orders': [], 'aov': [],
            'growth_rate': [], 'total_revenue': 0, 'total_orders': 0, 'avg_aov': 0
        }

    # Data cleaning & type conversion
    df['total_revenue'] = df['total_revenue'].astype(float)
    df['order_count'] = df['order_count'].astype(int)

    # Calculate Average Order Value (AOV)
    df['aov'] = np.round(df['total_revenue'] / df['order_count'], 2)

    # Calculate Month-over-Month (MoM) Revenue Growth Rate % using Pandas pct_change
    df['mom_growth'] = np.round(df['total_revenue'].pct_change() * 100, 2)
    df['mom_growth'] = df['mom_growth'].fillna(0.0)

    # Summary Statistical Metrics using NumPy
    total_rev = np.sum(df['total_revenue'])
    total_orders = np.sum(df['order_count'])
    avg_aov = np.mean(df['aov'])

    latest_growth = float(df['mom_growth'].iloc[-1]) if not df.empty and len(df) > 1 else 0.0

    return {
        'months': df['month'].tolist(),
        'revenue': df['total_revenue'].tolist(),
        'orders': df['order_count'].tolist(),
        'aov': df['aov'].tolist(),
        'growth_rate': df['mom_growth'].tolist(),
        'latest_growth_rate': latest_growth,
        'total_revenue': float(total_rev),
        'total_orders': int(total_orders),
        'avg_aov': float(np.round(avg_aov, 2)),
        'dataframe': df
    }


def get_category_sales_analytics():
    """
    Extract sales breakdown by product category using Pandas.
    Calculates category revenue share percentage.
    """
    conn = get_db_connection()
    try:
        query = """
            SELECT c.name AS category_name,
                   COUNT(DISTINCT o.id) AS total_orders,
                   SUM(oi.quantity) AS items_sold,
                   SUM(oi.price * oi.quantity) AS total_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.order_status != 'Cancelled'
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return {'categories': [], 'revenue': [], 'percentages': [], 'items_sold': [], 'dataframe': df}

    df['total_revenue'] = df['total_revenue'].astype(float)
    df['items_sold'] = df['items_sold'].astype(int)

    # Revenue Share Percentage using Pandas
    total_rev = df['total_revenue'].sum()
    df['revenue_pct'] = np.round((df['total_revenue'] / total_rev) * 100, 1)

    return {
        'categories': df['category_name'].tolist(),
        'revenue': df['total_revenue'].tolist(),
        'percentages': df['revenue_pct'].tolist(),
        'items_sold': df['items_sold'].tolist(),
        'dataframe': df
    }


def get_customer_spending_segmentation():
    """
    Perform customer spending segmentation and statistical analysis using NumPy/Pandas.
    Segments customers into VIP High Spenders, Regular Spenders, and Occasional Spenders.
    Computes statistical metrics: Mean, Median, Standard Deviation, Min, Max.
    """
    conn = get_db_connection()
    try:
        query = """
            SELECT u.id AS user_id, u.name, u.email,
                   COUNT(o.id) AS order_count,
                   COALESCE(SUM(o.total_amount), 0) AS total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id AND o.order_status != 'Cancelled'
            WHERE u.role = 'customer'
            GROUP BY u.id, u.name, u.email
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return {
            'segments': {}, 'stats': {}, 'dataframe': df
        }

    df['total_spent'] = df['total_spent'].astype(float)
    spending = df[df['total_spent'] > 0]['total_spent'].values

    if len(spending) == 0:
        return {'segments': {}, 'stats': {}, 'dataframe': df}

    # Statistical Summary using NumPy
    stats = {
        'count': len(spending),
        'mean_spend': float(np.round(np.mean(spending), 2)),
        'median_spend': float(np.round(np.median(spending), 2)),
        'std_dev': float(np.round(np.std(spending), 2)),
        'min_spend': float(np.round(np.min(spending), 2)),
        'max_spend': float(np.round(np.max(spending), 2))
    }

    # Customer Segmentation via Quantiles / Rules
    q75 = np.percentile(spending, 75)
    q25 = np.percentile(spending, 25)

    def segment_user(spent):
        if spent >= q75:
            return 'VIP High Spender'
        elif spent >= q25:
            return 'Regular Spender'
        elif spent > 0:
            return 'Occasional Spender'
        else:
            return 'No Orders'

    df['segment'] = df['total_spent'].apply(segment_user)
    segment_counts = df['segment'].value_counts().to_dict()

    return {
        'segments': segment_counts,
        'stats': stats,
        'q75': float(np.round(q75, 2)),
        'q25': float(np.round(q25, 2)),
        'dataframe': df
    }


def get_payment_method_analytics():
    """Extract sales distribution across payment methods using Pandas."""
    conn = get_db_connection()
    try:
        query = """
            SELECT p.payment_method,
                   COUNT(o.id) AS order_count,
                   COALESCE(SUM(o.total_amount), 0) AS total_revenue
            FROM payments p
            JOIN orders o ON p.order_id = o.id
            WHERE o.order_status != 'Cancelled'
            GROUP BY p.payment_method
            ORDER BY total_revenue DESC
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return {'methods': [], 'revenue': [], 'orders': [], 'dataframe': df}

    df['total_revenue'] = df['total_revenue'].astype(float)
    df['order_count'] = df['order_count'].astype(int)

    return {
        'methods': df['payment_method'].tolist(),
        'revenue': df['total_revenue'].tolist(),
        'orders': df['order_count'].tolist(),
        'dataframe': df
    }


def get_top_products_analytics(limit=10):
    """Extract top selling products using Pandas."""
    conn = get_db_connection()
    try:
        query = """
            SELECT p.name AS product_name,
                   c.name AS category_name,
                   p.price,
                   p.stock,
                   SUM(oi.quantity) AS units_sold,
                   SUM(oi.price * oi.quantity) AS total_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.order_status != 'Cancelled'
            GROUP BY p.id, p.name, c.name, p.price, p.stock
            ORDER BY units_sold DESC
            LIMIT %s
        """
        df = pd.read_sql(query, conn, params=(limit,))
    finally:
        conn.close()

    if df.empty:
        return {'products': [], 'units': [], 'revenue': [], 'dataframe': df}

    df['units_sold'] = df['units_sold'].astype(int)
    df['total_revenue'] = df['total_revenue'].astype(float)

    return {
        'products': df['product_name'].tolist(),
        'units': df['units_sold'].tolist(),
        'revenue': df['total_revenue'].tolist(),
        'dataframe': df
    }


def export_report_to_csv(report_type):
    """
    Export analytics report to a CSV file stream using Pandas.
    Formats column headers nicely for business intelligence presentation.
    Returns (BytesIO_buffer, filename).
    """
    import io

    if report_type == 'sales_summary':
        res = get_monthly_revenue_analytics()
        df = res['dataframe'].copy()
        if not df.empty:
            df.rename(columns={
                'month': 'Month',
                'order_count': 'Total Orders',
                'total_revenue': 'Total Revenue (INR)',
                'aov': 'Average Order Value (INR)',
                'mom_growth': 'MoM Growth Rate (%)'
            }, inplace=True)
    elif report_type == 'category_breakdown':
        res = get_category_sales_analytics()
        df = res['dataframe'].copy()
        if not df.empty:
            df.rename(columns={
                'category_name': 'Category Name',
                'total_orders': 'Total Orders',
                'items_sold': 'Units Sold',
                'total_revenue': 'Total Revenue (INR)',
                'revenue_pct': 'Revenue Share (%)'
            }, inplace=True)
    elif report_type == 'customer_segments':
        res = get_customer_spending_segmentation()
        df = res['dataframe'].copy()
        if not df.empty:
            df.rename(columns={
                'user_id': 'Customer ID',
                'name': 'Customer Name',
                'email': 'Email Address',
                'order_count': 'Total Orders',
                'total_spent': 'Total Spend (INR)',
                'segment': 'Customer Segment'
            }, inplace=True)
    elif report_type == 'top_products':
        res = get_top_products_analytics(limit=50)
        df = res['dataframe'].copy()
        if not df.empty:
            df.rename(columns={
                'product_name': 'Product Name',
                'category_name': 'Category',
                'price': 'Unit Price (INR)',
                'stock': 'Current Stock',
                'units_sold': 'Units Sold',
                'total_revenue': 'Total Revenue (INR)'
            }, inplace=True)
    elif report_type == 'payment_methods':
        res = get_payment_method_analytics()
        df = res['dataframe'].copy()
        if not df.empty:
            df.rename(columns={
                'payment_method': 'Payment Gateway',
                'order_count': 'Total Transactions',
                'total_revenue': 'Total Revenue (INR)'
            }, inplace=True)
    else:
        raise ValueError(f"Unknown report type: '{report_type}'")

    filename = f"{report_type}_report.csv"
    
    # Save CSV to memory buffer
    csv_buffer = io.BytesIO()
    csv_text = df.to_csv(index=False)
    csv_buffer.write(csv_text.encode('utf-8'))
    csv_buffer.seek(0)
    
    return csv_buffer, filename
