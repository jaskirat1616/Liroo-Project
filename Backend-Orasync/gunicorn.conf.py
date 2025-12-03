# Gunicorn configuration for Cloud Run
bind = "0.0.0.0:8080"
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 3600
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False 