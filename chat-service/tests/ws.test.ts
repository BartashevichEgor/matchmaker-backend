import WebSocket from 'ws';
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

function event(socket: WebSocket) {
  return new Promise<any>((resolve, reject) => {
    socket.once('message', (data) => resolve(JSON.parse(data.toString())));
    socket.once('error', reject);
  });
}

describe('authenticated chat WebSocket', () => {
  let app: Awaited<ReturnType<typeof createServer>> | undefined;
  let sockets: WebSocket[] = [];
  afterEach(async () => {
    sockets.forEach((socket) => socket.terminate());
    sockets = [];
    await app?.close();
    app = undefined;
  });

  it('authenticates in the first message, rechecks sends and reconnects, and acknowledges persisted messages', async () => {
    const pool = {
      query: vi.fn(async (sql: string) => {
        if (sql.includes('INSERT INTO conversation')) return { rows: [{ id: 'match:42', match_id: 42, created_at: new Date() }] };
        if (sql.includes('INSERT INTO message')) return { rows: [{ id: '1', conversation_id: 'match:42', sender_user_id: '7', client_message_id: 'c-1', body: 'Hello', created_at: new Date() }] };
        if (sql.includes('count(*)')) return { rows: [{ unread_count: 0 }] };
        return { rows: [] };
      }),
    } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockResolvedValue(authorized), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    const socket = new WebSocket(address.replace('http', 'ws') + '/chat/ws');
    sockets.push(socket);
    await new Promise<void>((resolve) => socket.once('open', resolve));
    const authenticated = event(socket);
    socket.send(JSON.stringify({ type: 'authenticate', access_token: 'access-secret', match_id: 42 }));
    expect(await authenticated).toEqual({ type: 'authenticated', conversation_id: 'match:42' });

    const ack = event(socket);
    socket.send(JSON.stringify({ type: 'send', client_message_id: 'c-1', body: 'Hello' }));
    expect(await ack).toMatchObject({ type: 'message_ack', duplicate: false, message: { body: 'Hello' } });
    expect(backend.getChatAccess).toHaveBeenCalledTimes(2);

    socket.close();
    const reconnected = new WebSocket(address.replace('http', 'ws') + '/chat/ws');
    sockets.push(reconnected);
    await new Promise<void>((resolve) => reconnected.once('open', resolve));
    const reauthenticated = event(reconnected);
    reconnected.send(JSON.stringify({ type: 'authenticate', access_token: 'access-secret', match_id: 42 }));
    expect(await reauthenticated).toEqual({ type: 'authenticated', conversation_id: 'match:42' });
    expect(backend.getChatAccess).toHaveBeenCalledTimes(3);
  });

  it('rejects an unauthorized match without exposing FastAPI details', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn().mockRejectedValue(new BackendError(403)), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    const socket = new WebSocket(address.replace('http', 'ws') + '/chat/ws');
    sockets.push(socket);
    await new Promise<void>((resolve) => socket.once('open', resolve));
    const rejected = event(socket);
    socket.send(JSON.stringify({ type: 'authenticate', access_token: 'access-secret', match_id: 42 }));
    expect(await rejected).toEqual({ type: 'error', code: 'forbidden' });
    expect(pool.query).not.toHaveBeenCalled();
  });

  it('stops sending when FastAPI expires access between socket authentication and a message', async () => {
    const pool = {
      query: vi.fn(async (sql: string) => sql.includes('INSERT INTO conversation')
        ? { rows: [{ id: 'match:42', match_id: 42, created_at: new Date() }] }
        : { rows: [] }),
    } as unknown as Pool;
    const backend = {
      health: vi.fn().mockResolvedValue(true),
      getChatAccess: vi.fn().mockResolvedValueOnce(authorized).mockRejectedValueOnce(new BackendError(401)),
      listMatches: vi.fn(),
    };
    app = await createServer(config, pool, backend as never);
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    const socket = new WebSocket(address.replace('http', 'ws') + '/chat/ws');
    sockets.push(socket);
    await new Promise<void>((resolve) => socket.once('open', resolve));
    const authenticated = event(socket);
    socket.send(JSON.stringify({ type: 'authenticate', access_token: 'access-secret', match_id: 42 }));
    await authenticated;
    const denied = event(socket);
    socket.send(JSON.stringify({ type: 'send', client_message_id: 'c-1', body: 'too late' }));
    expect(await denied).toEqual({ type: 'error', code: 'unauthorized' });
    expect(pool.query).toHaveBeenCalledTimes(1);
  });

  it('rejects browser WebSocket origins outside the configured allowlist', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    const socket = new WebSocket(address.replace('http', 'ws') + '/chat/ws', { headers: { Origin: 'https://untrusted.example' } });
    sockets.push(socket);
    const status = await new Promise<number>((resolve, reject) => {
      socket.once('unexpected-response', (_request, response) => resolve(response.statusCode ?? 0));
      socket.once('error', reject);
    });
    expect(status).toBe(403);
    expect(backend.getChatAccess).not.toHaveBeenCalled();
    expect(pool.query).not.toHaveBeenCalled();
  });

  it('closes sockets that do not authenticate within the bounded handshake period', async () => {
    const pool = { query: vi.fn() } as unknown as Pool;
    const backend = { health: vi.fn().mockResolvedValue(true), getChatAccess: vi.fn(), listMatches: vi.fn() };
    app = await createServer(config, pool, backend as never);
    const address = await app.listen({ host: '127.0.0.1', port: 0 });
    const socket = new WebSocket(address.replace('http', 'ws') + '/chat/ws');
    sockets.push(socket);
    await new Promise<void>((resolve) => socket.once('open', resolve));
    expect(await event(socket)).toEqual({ type: 'error', code: 'unauthorized' });
    expect(backend.getChatAccess).not.toHaveBeenCalled();
    expect(pool.query).not.toHaveBeenCalled();
  }, 7000);
});
