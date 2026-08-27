# ==================================================
# WSGI Production Application Entry Point
# ==================================================
# Entry point for production WSGI servers like Gunicorn,
# Waitress, uWSGI, or Nginx + uWSGI.
# ==================================================

import os
from app import create_app

# Load production configuration by default
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == '__main__':
    # Fallback development server execution
    app.run(host='0.0.0.0', port=5000)
