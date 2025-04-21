#!/bin/sh

TASKS_DIR=src/tasks

# Wait for postgresql and vector db become available
python3 $TASKS_DIR/wait_dbs.py

# Run alembic migrations (postgresql)
alembic upgrade head

# Run all
#python3 $TASKS_DIR/import_sites.py
#python3 $TASKS_DIR/import_pages.py
#python3 $TASKS_DIR/fetch_files.py
#python3 $TASKS_DIR/import_files.py
python3 $TASKS_DIR/import_text_files.py

# exec "$@"