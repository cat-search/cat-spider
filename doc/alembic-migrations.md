# Alembic migrations

Работа с алембик миграциями (ревизиями) БД Postgresql.

```shell
# Init alembic
alembic init -t generic  src/migrations
# Create a migration with name new_migration
alembic revision --autogenerate -m new_migration
# Debug: dry run migration
alembic upgrade head --sql
# Apply migrations from current to latest
alembic upgrade head
# List migrations
alembic history
```
