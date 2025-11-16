@echo off
celery -A balm worker --pool=gevent --concurrency=10 --loglevel=info