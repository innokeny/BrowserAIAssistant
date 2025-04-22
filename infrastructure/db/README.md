# Database Integration

This directory contains the database integration for the Browser AI Assistant. The system uses a two-tier storage approach:

1. **PostgreSQL** - Primary database for persistent storage of user data, quotas, and request history
2. **Redis** - In-memory cache for frequently accessed data and metrics

## Setup

### Using Docker Compose

The easiest way to set up the database is using Docker Compose:

```bash
cd infrastructure/db
docker-compose up -d
```

This will start:
- PostgreSQL on port 5433
- Redis on port 6379
- pgAdmin on port 8080 (for database management)

### Manual Setup

If you prefer to set up the databases manually:

#### PostgreSQL

1. Install PostgreSQL 15 or later
2. Create a database named `pg_db`
3. Create a user `postgres` with password `postgres`
4. Update the connection settings in `db_connection.py` if needed

#### Redis

1. Install Redis 7 or later
2. Start the Redis server
3. Update the connection settings in `db_connection.py` if needed

## Database Schema

The database consists of the following tables:

### Users

Stores user information:
- `id` - Primary key
- `name` - User's name
- `email` - User's email (unique)
- `created_at` - When the user was created
- `updated_at` - When the user was last updated

### Quotas

Stores resource usage quotas:
- `id` - Primary key
- `user_id` - Foreign key to users table
- `resource_type` - Type of resource (e.g., "stt", "tts", "llm")
- `limit` - Maximum allowed usage
- `current_usage` - Current usage count
- `reset_date` - When the quota resets
- `created_at` - When the quota was created
- `updated_at` - When the quota was last updated

### Request History

Stores history of API requests:
- `id` - Primary key
- `user_id` - Foreign key to users table
- `request_type` - Type of request (e.g., "stt", "tts", "llm")
- `request_data` - Input data (truncated if needed)
- `response_data` - Response data (truncated if needed)
- `status` - Status of the request (e.g., "success", "error")
- `error_message` - Error message if status is "error"
- `processing_time` - Processing time in milliseconds
- `created_at` - When the request was made

## Usage

### Initializing the Database

The database is automatically initialized when the application starts. You can also initialize it manually:

```bash
python infrastructure/db/init_db.py
```

### Repository Pattern

The database access is implemented using the repository pattern:

- `UserRepositoryImpl` - Handles user data
- `QuotaRepositoryImpl` - Handles quota data
- `RequestHistoryRepositoryImpl` - Handles request history

### Resource Manager

The `ResourceManager` class provides a high-level interface for:

- Checking resource quotas
- Tracking resource usage
- Creating default quotas for new users

## Environment Variables

The following environment variables can be used to configure the database connection:

### PostgreSQL

- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_PASSWORD` - Database password (default: postgres)
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_PORT` - Database port (default: 5433)
- `POSTGRES_DB` - Database name (default: pg_db)

### Redis

- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_DB` - Redis database number (default: 0) 