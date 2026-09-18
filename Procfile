web: gunicorn dashboard_server:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 300 --graceful-timeout 30 --keep-alive 5
