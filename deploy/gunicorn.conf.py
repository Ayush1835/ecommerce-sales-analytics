# ==================================================
# Gunicorn Production Configuration
# ==================================================
# Configures worker processes, threads, timeouts,
# and logging for Gunicorn WSGI server.
# ==================================================

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
# Formula: (2 * CPU cores) + 1
workers = int(os.environ.get('WEB_CONCURRENCY', (multiprocessing.cpu_count() * 2) + 1))
worker_class = 'gthread'
threads = 2
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'shopanalytica_gunicorn'
