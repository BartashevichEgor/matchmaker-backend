import type { Pool } from 'pg';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { BackendError } from '../src/backend-client.js';
import { loadConfig } from '../src/config.js';
import { createServer } from '../src/server.js';

const config = loadConfig({ CHAT_DATABASE_URL: 'postgresql://chat:pw@localhost/chat', MATCHMAKER_API_URL: 'http://localhost:8000' });
const authorized = {
  id: 42, project_id: 9, candidate_id: 7, room_key: 'match:42', created_at: '2026-11-15T12:00:00Z', allowed: true,
  current_user_id: 7, project_owner_id: 3, expires_at: null,
  project: { id: 9, title: 'API Platform', owner_id: 3, kind: 'project' },
  candidate: { user_id: 7, display_name: 'Ada', headline: 'Developer', avatar_url: null },
};

describe('health and REST authorization', () => {
  let app: Awaited<ReturnType<typeof createServer>> | undefined;
  afterEach(async () => { await app?.close(); app = undefined; });

  it('reports both dependencies and returns 503 when one is unavailable', async () => {
    const pool = { query: vi.fn().mockResolvedValue({ rows: [] }) } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(false), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({ method: 'GET', url: '/health' });
    expect(response.statusCode).toBe(503);
    expect(response.json()).toEqual({ status: 'degraded', dependencies: { database: true, matchmaker_api: false } });
  });

  it('allows browser preflight only for the configured web origin', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const allowed = await app.inject({
      method: 'OPTIONS',
      url: '/chat/conversations',
      headers: { origin: 'http://localhost:5173', 'access-control-request-method': 'GET', 'access-control-request-headers': 'authorization' },
    });
    const denied = await app.inject({
      method: 'OPTIONS',
      url: '/chat/conversations',
      headers: { origin: 'https://untrusted.example', 'access-control-request-method': 'GET', 'access-control-request-headers': 'authorization' },
    });
    expect(allowed.headers['access-control-allow-origin']).toBe('http://localhost:5173');
    expect(denied.headers['access-control-allow-origin']).toBeUndefined();
  });

  it('does not call FastAPI or the database when bearer auth is missing', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({ method: 'GET', url: '/chat/conversations/match:42/messages' });
    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: 'unauthorized' });
    expect(backend.getChatAccess).not.toHaveBeenCalled();
    expect(pool.query).not.toHaveBeenCalled();
  });

  it('rejects malformed message bodies without creating a conversation', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({
      method: 'POST',
      url: '/chat/conversations/match:42/messages',
      headers: { authorization: 'Bearer valid-token' },
      payload: { client_message_id: 'c-1', body: '   ' },
    });
    expect(response.statusCode).toBe(422);
    expect(backend.getChatAccess).not.toHaveBeenCalled();
    expect(pool.query).not.toHaveBeenCalled();
  });

  it('returns forbidden when FastAPI denies a guessed match ID', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockRejectedValue(new BackendError(403)), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({
      method: 'GET',
      url: '/chat/conversations/match:42/messages',
      headers: { authorization: 'Bearer outsider-token' },
    });
    expect(response.statusCode).toBe(403);
    expect(pool.query).not.toHaveBeenCalled();
  });

  it('returns cursor history and unread count for the authorized participant only', async () => {
    const message = { id: '1', conversation_id: 'match:42', sender_user_id: '3', client_message_id: 'owner-1', body: 'Hi', created_at: new Date('2026-11-15T12:00:00Z') };
    const pool = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('INSERT INTO conversation')) return { rows: [{ id: 'match:42', match_id: 42, created_at: new Date() }] };
        if (sql.includes('SELECT id, conversation_id, sender_user_id, client_message_id, body')) return { rows: [message] };
        if (sql.includes('count(*)')) return { rows: [{ unread_count: 1 }] };
        return { rows: [] };
      }),
    } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockResolvedValue(authorized), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({
      method: 'GET',
      url: '/chat/conversations/match:42/messages?limit=10',
      headers: { authorization: 'Bearer candidate-token' },
    });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({
      conversation_id: 'match:42',
      messages: [{ id: '1', sender_user_id: 3, body: 'Hi' }],
      next_cursor: null,
      unread_count: 1,
    });
    expect(backend.getChatAccess).toHaveBeenCalledWith(42, 'candidate-token');
  });

  it('persists a REST message and acknowledges an idempotent retry', async () => {
    const persisted = { id: '2', conversation_id: 'match:42', sender_user_id: '7', client_message_id: 'c-1', body: 'Hello', created_at: new Date() };
    let inserted = false;
    const pool = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('INSERT INTO conversation')) return { rows: [{ id: 'match:42', match_id: 42, created_at: new Date() }] };
        if (sql.includes('INSERT INTO message')) {
          if (inserted) return { rows: [] };
          inserted = true;
          return { rows: [persisted] };
        }
        if (sql.includes('WHERE sender_user_id = $1 AND client_message_id = $2')) return { rows: [persisted] };
        if (sql.includes('count(*)')) return { rows: [{ unread_count: 0 }] };
        return { rows: [] };
      }),
    } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockResolvedValue(authorized), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({
      method: 'POST',
      url: '/chat/conversations/match:42/messages',
      headers: { authorization: 'Bearer candidate-token' },
      payload: { client_message_id: 'c-1', body: 'Hello' },
    });
    expect(response.statusCode).toBe(201);
    expect(response.json()).toMatchObject({ message: { id: '2', sender_user_id: 7, body: 'Hello' }, duplicate: false, unread_count: 0 });
    const retry = await app.inject({
      method: 'POST',
      url: '/chat/conversations/match:42/messages',
      headers: { authorization: 'Bearer candidate-token' },
      payload: { client_message_id: 'c-1', body: 'Hello' },
    });
    expect(retry.statusCode).toBe(200);
    expect(retry.json()).toMatchObject({ message: { id: '2' }, duplicate: true });
  });

  it('marks only the current participant read and returns their updated unread count', async () => {
    const pool = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('INSERT INTO conversation')) return { rows: [{ id: 'match:42', match_id: 42, created_at: new Date() }] };
        if (sql.includes('count(*)')) return { rows: [{ unread_count: 0 }] };
        return { rows: [] };
      }),
      connect: vi.fn().mockResolvedValue({
        query: vi.fn(async (sql: string) => sql.startsWith('SELECT id FROM message') ? { rows: [{ id: '4' }] } : { rows: [] }),
        release: vi.fn(),
      }),
    } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockResolvedValue(authorized), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const response = await app.inject({
      method: 'POST',
      url: '/chat/conversations/match:42/read',
      headers: { authorization: 'Bearer candidate-token' },
    });
    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ conversation_id: 'match:42', unread_count: 0 });
  });
});
