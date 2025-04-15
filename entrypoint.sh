#!/bin/sh

TASKS_DIR=src/tasks

alembic upgrade head

python3 $TASKS_DIR/import_sites.py
python3 $TASKS_DIR/import_pages.py
python3 $TASKS_DIR/fetch_files.py
python3 $TASKS_DIR/import_files.py

# exec "$@"