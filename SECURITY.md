# Application Security & Hardening Architecture

This document provides a technical overview of the security measures implemented in the **ShopAnalytica E-Commerce Platform**.

---

## 1. Authentication & Password Security

- **Password Hashing Algorithm**: `Werkzeug.security.generate_password_hash` using **scrypt**.
  - High CPU/memory difficulty factor to render GPU brute-force attacks impractical.
  - Unique random salt generated per user; plain-text passwords are never stored, logged, or transmitted.
- **Session Protection**:
  - `SESSION_COOKIE_HTTPONLY = True`: Blocks JavaScript access to session cookies (`document.cookie`), preventing session theft via XSS.
  - `SESSION_COOKIE_SAMESITE = 'Lax'`: Mitigates Cross-Site Request Forgery (CSRF) by ensuring session cookies are not attached to cross-site requests.
  - `PERMANENT_SESSION_LIFETIME = 3600`: Idle sessions automatically expire after 1 hour.
  - Session data stores only non-sensitive identifiers (`user_id`, `name`, `email`, `role`). Never stores hashes or tokens.

---

## 2. SQL Injection Prevention

- **Parameterized Queries**: Every SQL query across `models/`, `routes/`, and `seed_data.py` uses MySQL `%s` placeholders.
- User input is passed as parameter tuples to `cursor.execute(query, params)`, delegating escaping directly to the `mysql-connector-python` driver binary protocol.
- No string concatenation (`+` or `%` formatting) is used in SQL statements anywhere in the codebase.

---

## 3. HTTP Security Headers Middleware

Attached to Flask's `@app.after_request` middleware hook in `utils/security.py`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Blocks MIME-type sniffing by enforcing declared Content-Types |
| `X-Frame-Options` | `SAMEORIGIN` | Prevents Clickjacking and UI redressing attacks via `<iframe>` embedding |
| `X-XSS-Protection` | `1; mode=block` | Enables browser XSS auditor to block rendered pages when attacks are detected |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits sensitive URL leaks in referrer headers |
| `Content-Security-Policy` | `default-src 'self' ...` | Restricts executable scripts and styles to trusted CDNs (Bootstrap, Chart.js, Google Fonts) |

---

## 4. Role-Based Access Control (RBAC)

- **Route Decorators**:
  - `@login_required`: Restricts protected routes to authenticated users, preserving intended URL in `next` parameter.
  - `@admin_required`: Restricts sensitive endpoints (`/admin/*`, `/analytics/*`) to users where `role == 'admin'`. Non-admins are blocked with a `403/404` or redirected with a `danger` flash message.
- **Database Constraints**: `users.role` uses `ENUM('customer', 'admin')` at the schema level.

---

## 5. Input Sanitization & XSS Defense

- **Jinja2 Auto-Escaping**: All template variables `{{ variable }}` are automatically escaped by Jinja2 by default.
- **Input Escaping**: `utils.security.sanitize_input()` uses `html.escape()` for user-submitted form data.
- **Image Source Sanitization**: All product image tags include fallback `onerror` event handlers pointing to clean local placeholders.

---

## 6. Financial Transaction & Inventory Safeguards

- **ACID Transactions**: Checkout (`create_order_checkout`) and cancellation (`cancel_order`) execute inside `BEGIN TRANSACTION` blocks with explicit `commit()` and `rollback()` handling.
- **Stock Guardrails**: Pre-checkout stock validation prevents double-selling out-of-stock items under concurrent operations.
- **Immutable Price Snapshots**: Historical item prices are frozen in `order_items.price` at purchase time to prevent retroactive financial alteration.
