import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import type { DbPool } from '../src/db.js';
import { migrate } from '../src/migrator.js';
import { connectTestPool, databaseUrl } from './db-test-helpers.js';

describe.skipIf(!databaseUrl)('chat schema migrations', () => {
  let pool: DbPool;
  beforeAll(async () => { pool = await connectTestPool(); });
  afterAll(async () => { await pool?.end(); });

  it('applies each version once and is safe on restart', async () => {
    await migrate(pool);
    await migrate(pool);
    const result = await pool.query('SELECT count(*)::int AS total FROM schema_migrations WHERE version = $1', ['001_chat_schema']);
    expect(result.rows[0].total).toBe(1);
  });
});
