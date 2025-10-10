# Workers Directory

This directory contains background workers for processing applications and other automated tasks.

## Available Workers

### Simulated Application Worker (`simulated_apply_worker.py`)

A worker that processes applications with status "pending" and simulates the application process.

**Features:**
- Connects to Supabase to fetch pending applications
- Creates simulated application results with metadata
- Updates application status to "applied"
- Stores application artifacts in the database

**Usage:**
```bash
# Run worker once to process all pending applications
python workers/simulated_apply_worker.py run_once
```

**Output:**
- Processes applications and updates their status
- Returns JSON with processing statistics
- Logs detailed information about each operation

**Future Extensions:**
- **Playwright Integration**: Automate form filling on job boards
- **API Integration**: Connect to official job board APIs (with user consent)
- **Retry Logic**: Handle failed applications with exponential backoff
- **Rate Limiting**: Respect job board rate limits
- **Scheduling**: Run on a cron schedule instead of manual invocation

## Testing

Use the test script to verify worker functionality:

```bash
# Run comprehensive test suite
python test_simulated_worker.py
```

The test script will:
1. Create test applications with "pending" status
2. Run the worker to process them
3. Verify the results were updated correctly
4. Optionally clean up test data

## Environment Requirements

Make sure you have the following environment variables set in your `.env` file:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Database Schema

The workers expect the following database structure:

- **`applications`** table with columns:
  - `id` (UUID, primary key)
  - `user_id` (UUID, foreign key to users)
  - `job_id` (UUID, foreign key to jobs)
  - `status` (TEXT, with check constraint)
  - `artifacts` (JSONB, for storing application results)
  - `attempt_meta` (JSONB, for metadata)
  - `created_at`, `updated_at` (TIMESTAMPTZ)

- **`jobs`** table with job postings
- **`users`** table with user profiles

## Adding New Workers

When adding new workers:

1. Create a new Python file in this directory
2. Follow the same pattern as `simulated_apply_worker.py`
3. Include proper error handling and logging
4. Add CLI interface with argparse
5. Create corresponding test script
6. Update this README

## Production Considerations

For production deployment:

- Use a process manager like `systemd` or `supervisord`
- Set up proper logging with log rotation
- Monitor worker health and performance
- Implement proper error alerting
- Consider using a message queue (Redis, RabbitMQ) for scalability
- Add metrics and monitoring
