import { readFile } from 'node:fs/promises';
import type { DbPool } from './db.js';

const migration = { version: '001_chat_schema', file: new URL('./migrations/001_chat_schema.sql', import.meta.url) };

export async function migrate(pool: DbPool) {
  const client = await pool.connect();
  try {
    await client.query('SELECT pg_advisory_lock(741928105)');
    await client.query('CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())');
    const { rows } = await client.query('SELECT version FROM schema_migrations WHERE version = $1', [migration.version]);
    if (rows.length) return;

    const sql = await readFile(migration.file, 'utf8');
    await client.query('BEGIN');
    try {
      await client.query(sql);
      await client.query('INSERT INTO schema_migrations(version) VALUES ($1)', [migration.version]);
      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    }
  } finally {
    try { await client.query('SELECT pg_advisory_unlock(741928105)'); } finally { client.release(); }
  }
}
