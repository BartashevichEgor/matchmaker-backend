import Fastify, { type FastifyInstance, type RawServerDefault } from 'fastify';
import cors from '@fastify/cors';
import type { Config } from './config.js';
import type { createBackendClient } from './backend-client.js';
import type { DbPool } from './db.js';
import { registerConversationRoutes } from './routes/conversations.js';
import { registerWebSocket } from './ws.js';

type Backend = ReturnType<typeof createBackendClient>;

export async function createServer(config: Config, pool: DbPool, backend: Backend): Promise<FastifyInstance> {
  const app = Fastify<RawServerDefault>({
    logger: process.env.NODE_ENV === 'test' ? false : {
      redact: ['req.headers.authorization', 'req.headers.cookie'],
      serializers: { req: (request) => ({ method: request.method, url: (request.url ?? '').split('?')[0] ?? '' }) },
    },
    bodyLimit: 8192,
    requestTimeout: 15000,
    connectionTimeout: 10000,
  });

  await registerWebSocket(app, pool, backend, config.CHAT_ALLOWED_ORIGINS);
  await app.register(cors, {
    origin: config.CHAT_ALLOWED_ORIGINS,
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['authorization', 'content-type'],
    credentials: false,
    maxAge: 600,
  });
  app.setNotFoundHandler((_request, reply) => reply.code(404).send({ error: 'not_found' }));
  app.setErrorHandler((error, _request, reply) => {
    const statusCode = typeof error === 'object' && error !== null && 'statusCode' in error ? error.statusCode : undefined;
    if (typeof statusCode === 'number' && statusCode >= 400 && statusCode < 500) return reply.code(statusCode).send({ error: 'invalid_request' });
    return reply.code(500).send({ error: 'internal_error' });
  });
  app.get('/health', async (_request, reply) => {
    const dependencies = { database: false, matchmaker_api: false };
    try { await pool.query('SELECT 1'); dependencies.database = true; } catch { /* readiness reports dependency state */ }
    dependencies.matchmaker_api = await backend.health();
    const ok = dependencies.database && dependencies.matchmaker_api;
    return reply.code(ok ? 200 : 503).send({ status: ok ? 'ok' : 'degraded', dependencies });
  });

  registerConversationRoutes(app, pool, backend);
  return app;
}
