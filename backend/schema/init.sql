-- Docker entrypoint init script for ImobiManager PostgreSQL.
-- The dev database (imobimanager) is created automatically via the
-- POSTGRES_DB environment variable in docker-compose.yml. This script
-- creates the dedicated test database.
CREATE DATABASE imobimanager_test;