# server/start.sh
#!/bin/bash
#exec gunicorn -k eventlet -w 1 app:app --bind 0.0.0.0:$PORT
exec gunicorn \
    --worker-class sync \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --bind 0.0.0.0:$PORT \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app