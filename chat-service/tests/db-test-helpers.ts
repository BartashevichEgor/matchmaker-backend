import type { DbPool } from '../src/db.js';
import { createPool } from '../src/db.js';
import { migrate } from '../src/migrator.js';

export const databaseUrl = process.env.CHAT_TEST_DATABASE_URL;
export const connectTestPool = async (): Promise<DbPool> => {
  if (!databaseUrl) throw new Error('CHAT_TEST_DATABASE_URL is required');
  if (new URL(databaseUrl).pathname !== '/matchmaker_chat_test') {
    throw new Error('CHAT_TEST_DATABASE_URL must point to the isolated matchmaker_chat_test database');
  }
  const pool = createPool(databaseUrl);
  await migrate(pool);
  return pool;
};

export async function clearTestData(pool: DbPool) {
  await pool.query('TRUNCATE conversation CASCADE');
}
