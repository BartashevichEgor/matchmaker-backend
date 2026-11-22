import { createBackendClient } from './backend-client.js';
import { loadConfig } from './config.js';
import type { Config } from './config.js';
import { createPool } from './db.js';
import { migrate } from './migrator.js';
import { createServer } from './server.js';
import type { FastifyInstance } from 'fastify';

async function main() {
  let config: Config;
  try { config = loadConfig(); } catch { console.error('Invalid chat service configuration'); process.exitCode = 1; return; }
  const pool = createPool(config.CHAT_DATABASE_URL);
  let app: FastifyInstance | undefined;
  try {
    await migrate(pool);
    app = await createServer(config, pool, createBackendClient(config.MATCHMAKER_API_URL, config.CHAT_INTERNAL_TIMEOUT_MS));
    await app.listen({ host: '0.0.0.0', port: config.CHAT_PORT });
  } catch {
    console.error('Chat service failed to start');
    process.exitCode = 1;
    await app?.close().catch(() => undefined);
    await pool.end().catch(() => undefined);
    return;
  }

  const shutdown = async () => {
    await app.close();
    await pool.end();
  };
  process.once('SIGINT', () => { void shutdown(); });
  process.once('SIGTERM', () => { void shutdown(); });
}

void main();
