import pg from 'pg';

const { Pool } = pg;
export type DbPool = pg.Pool;

export function createPool(connectionString: string) {
  return new Pool({ connectionString, max: 10, connectionTimeoutMillis: 5000, idleTimeoutMillis: 30000 });
}
