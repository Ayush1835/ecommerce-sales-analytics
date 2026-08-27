# ==================================================
# Security Utilities & Response Headers Middleware
# ==================================================
# Implements security headers, response middleware,
# HTML input sanitization, and session security configuration.
# ==================================================

import html
from flask import request


def sanitize_input(text):
    """
    Sanitize user text input to prevent Cross-Site Scripting (XSS).
    Converts special HTML characters (<, >, &, ", ') to HTML entities.
    """
    if not text:
        return text
    return html.escape(text.strip())


def add_security_headers(response):
    """
    Flask after_request middleware handler that injects security headers
    into every outgoing HTTP response.

    Headers Applied:
    1. X-Content-Type-Options: nosniff (Prevents MIME-type sniffing attacks)
    2. X-Frame-Options: SAMEORIGIN (Prevents Clickjacking UI redressing attacks)
    3. X-XSS-Protection: 1; mode=block (Enables legacy browser XSS auditor)
    4. Referrer-Policy: strict-origin-when-cross-origin (Controls referrer info)
    5. Content-Security-Policy (CSP): Restricts scripts, styles, images to trusted CDNs
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Content Security Policy (CSP) allowing trusted CDNs (Bootstrap, Chart.js, Google Fonts, picsum)
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        "img-src 'self' data: https: http:; "
        "connect-src 'self';"
    )
    response.headers['Content-Security-Policy'] = csp

    return response
