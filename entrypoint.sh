#!/bin/sh
set -e

python - <<'EOF'
import psycopg2, os, sys, time
url = os.environ.get("DATABASE_URL", "").replace("+psycopg2", "")
for _ in range(30):
    try:
        psycopg2.connect(url).close()
        print("Database is ready")
        sys.exit(0)
    except Exception as e:
        print(f"Waiting for database... {e}")
        time.sleep(1)
print("Database did not become ready in time")
sys.exit(1)
EOF

alembic upgrade head
exec gunicorn -w 2 -b 0.0.0.0:8000 --access-logfile - --error-logfile - --capture-output --log-level debug main:app
