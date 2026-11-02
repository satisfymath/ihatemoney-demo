#!/bin/sh
# Runs once, when the database volume is first created (PostgreSQL's docker-entrypoint-initdb.d).
# A role that can only read: for an observer that must never write to the application's data.
set -e

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
CREATE ROLE unbidden_ro LOGIN PASSWORD '${UNBIDDEN_RO_PASSWORD}';
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO unbidden_ro;
GRANT USAGE ON SCHEMA public TO unbidden_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO unbidden_ro;
-- Tables the application creates later (its migrations run as $POSTGRES_USER) are readable too.
ALTER DEFAULT PRIVILEGES FOR ROLE "$POSTGRES_USER" IN SCHEMA public GRANT SELECT ON TABLES TO unbidden_ro;
EOF
