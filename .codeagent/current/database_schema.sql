-- Project database schema
-- This file is the source of truth for the running database.
-- It must reflect tables, columns, indexes, and constraints exactly.
-- Any schema change requires updating this file.

-- Current State: No persistent database schema
-- The Music Tools API currently uses Redis for temporary task storage only
-- All file processing is stateless with automatic cleanup

-- Redis Usage:
-- - Background task queuing (Celery)
-- - Temporary task status tracking
-- - No persistent data storage required

-- Future Database Considerations:
-- - User authentication tables (if API auth is implemented)
-- - Processing history logs (optional)
-- - Usage statistics tracking (optional)
-- - File metadata caching (optional)

-- TODO: Add database schema when persistent storage is implemented
