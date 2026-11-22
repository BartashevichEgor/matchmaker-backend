import { spawn, type ChildProcess } from 'node:child_process';
import { mkdtemp, readdir, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createServer as createTcpServer } from 'node:net';
import { setTimeout as delay } from 'node:timers/promises';
import WebSocket from 'ws';
import { afterAll, describe, expect, it } from 'vitest';
import { createBackendClient } from '../src/backend-client.js';
import { loadConfig } from '../src/config.js';
import { createPool } from '../src/db.js';
import { migrate } from '../src/migrator.js';
import { createServer } from '../src/server.js';

const apiDatabaseUrl = process.env.MATCHMAKER_API_DATABASE_URL;
const chatDatabaseUrl = process.env.CHAT_TEST_DATABASE_URL;

describe.skipIf(!apiDatabaseUrl || !chatDatabaseUrl)('matching-to-chat end-to-end', () => {
  let apiProcess: ChildProcess | undefined;
  let app: Awaited<ReturnType<typeof createServer>> | undefined;
  let pool: ReturnType<typeof createPool> | undefined;
  const sockets: WebSocket[] = [];

  afterAll(async () => {
    sockets.forEach((socket) => socket.terminate());
    await app?.close();
    await pool?.end();
    apiProcess?.kill();
  });

  it('creates a mutual match, allows its two users to exchange messages, and denies an outsider', async () => {
    const outbox = await mkdtemp(join(tmpdir(), 'matchmaker-e2e-'));
    const apiPort = await freePort();
    apiProcess = spawn(process.env.PYTHON ?? 'python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(apiPort)], {
      cwd: resolve('..', 'core-api'),
      env: {
        ...process.env,
        ENVIRONMENT: 'test',
        DATABASE_URL: apiDatabaseUrl,
        JWT_SECRET: process.env.JWT_SECRET ?? 'test-only-secret-not-for-any-real-deployment-12345',
        MAIL_MODE: 'outbox',
        OUTBOX_DIR: outbox,
        REDIS_URL: '',
      },
      stdio: 'ignore',
    });
    const apiUrl = `http://127.0.0.1:${apiPort}`;
    try {
      await waitForApi(apiUrl, apiProcess);
      const candidate = await createAccount(apiUrl, outbox, 'developer');
      const owner = await createAccount(apiUrl, outbox, 'project');
      const outsider = await createAccount(apiUrl, outbox, 'developer');
      const headers = (token: string) => ({ authorization: `Bearer ${token}` });

      const skills = await request<any[]>(apiUrl, '/api/v1/skills');
      const roles = await request<any[]>(apiUrl, '/api/v1/roles');
      const skillId = skills.find((item) => item.name === 'Python')?.id;
      const roleId = roles.find((item) => item.name === 'Backend')?.id;
      expect(skillId).toBeTruthy();
      expect(roleId).toBeTruthy();
      await request(apiUrl, '/api/v1/profiles/me', {
        method: 'PATCH', headers: headers(candidate.accessToken), body: JSON.stringify({ visibility: 'published' }),
      });
      await request(apiUrl, '/api/v1/profiles/me/skills', {
        method: 'PUT', headers: headers(candidate.accessToken), body: JSON.stringify({ skills: [{ skill_id: skillId, level: 5 }] }),
      });
      const project = await request<any>(apiUrl, '/api/v1/projects', {
        method: 'POST', headers: headers(owner.accessToken),
        body: JSON.stringify({
          title: `Chat E2E ${Date.now()}`, description: 'Project created for the matching-to-chat integration test.',
          skills: [{ skill_id: skillId, weight: 5 }], role_ids: [roleId], visibility: 'published',
        }),
      });

      const firstLike = await request<any>(apiUrl, `/api/v1/projects/${project.id}/my-swipe`, {
        method: 'PUT', headers: headers(candidate.accessToken), body: JSON.stringify({ decision: 'like' }),
      });
      expect(firstLike.match).toBeNull();
      const secondLike = await request<any>(apiUrl, `/api/v1/projects/${project.id}/candidates/${candidate.userId}/swipe`, {
        method: 'PUT', headers: headers(owner.accessToken), body: JSON.stringify({ decision: 'like' }),
      });
      expect(secondLike.match).toMatchObject({ candidate: { user_id: candidate.userId }, project: { owner_id: owner.userId } });
      const matchId = secondLike.match.id as number;
      const conversationId = `match:${matchId}`;

      const config = loadConfig({ CHAT_DATABASE_URL: chatDatabaseUrl!, MATCHMAKER_API_URL: apiUrl });
      pool = createPool(chatDatabaseUrl!);
      await migrate(pool);
      app = await createServer(config, pool, createBackendClient(apiUrl, config.CHAT_INTERNAL_TIMEOUT_MS));
      const chatUrl = await app.listen({ host: '127.0.0.1', port: 0 });
      const conversations = await request<any[]>(chatUrl, '/chat/conversations', { headers: headers(candidate.accessToken) });
      expect(conversations.map((item) => item.id)).toContain(conversationId);
      expect(await request<any[]>(chatUrl, '/chat/conversations', { headers: headers(owner.accessToken) })).toHaveLength(1);
      const outsiderResponse = await fetch(`${chatUrl}/chat/conversations/${conversationId}/messages`, { headers: headers(outsider.accessToken) });
      expect(outsiderResponse.status).toBe(403);

      const restMessage = await request<any>(chatUrl, `/chat/conversations/${conversationId}/messages`, {
        method: 'POST', headers: headers(candidate.accessToken),
        body: JSON.stringify({ client_message_id: `rest-${Date.now()}`, body: 'Привет, матч сработал!' }),
      });
      expect(restMessage.message.body).toBe('Привет, матч сработал!');
      const history = await request<any>(chatUrl, `/chat/conversations/${conversationId}/messages`, { headers: headers(owner.accessToken) });
      expect(history.messages.map((message: any) => message.body)).toContain('Привет, матч сработал!');
      expect(history.unread_count).toBe(1);

      const candidateSocket = await connectChat(chatUrl, candidate.accessToken, matchId, sockets);
      const ownerSocket = await connectChat(chatUrl, owner.accessToken, matchId, sockets);
      const receivedByOwner = nextEvent(ownerSocket, (event) => event.type === 'message' && event.message.body === 'Ответ из WebSocket');
      const candidateAck = nextEvent(candidateSocket, (event) => event.type === 'message_ack');
      candidateSocket.send(JSON.stringify({ type: 'send', client_message_id: `ws-${Date.now()}`, body: 'Ответ из WebSocket' }));
      expect((await candidateAck).message.body).toBe('Ответ из WebSocket');
      expect((await receivedByOwner).message.sender_user_id).toBe(candidate.userId);

      const receivedByCandidate = nextEvent(candidateSocket, (event) => event.type === 'message' && event.message.body === 'Да, переписка работает.');
      const ownerAck = nextEvent(ownerSocket, (event) => event.type === 'message_ack');
      ownerSocket.send(JSON.stringify({ type: 'send', client_message_id: `reply-${Date.now()}`, body: 'Да, переписка работает.' }));
      expect((await ownerAck).message.body).toBe('Да, переписка работает.');
      expect((await receivedByCandidate).message.sender_user_id).toBe(owner.userId);

      const finalHistory = await request<any>(chatUrl, `/chat/conversations/${conversationId}/messages`, { headers: headers(candidate.accessToken) });
      expect(finalHistory.messages.map((message: any) => message.body)).toEqual([
        'Привет, матч сработал!', 'Ответ из WebSocket', 'Да, переписка работает.',
      ]);
      expect(finalHistory.unread_count).toBe(1);
      const markedRead = await request<any>(chatUrl, `/chat/conversations/${conversationId}/read`, {
        method: 'POST', headers: headers(candidate.accessToken), body: '{}',
      });
      expect(markedRead.unread_count).toBe(0);
    } finally {
      apiProcess?.kill();
      apiProcess = undefined;
      await rm(outbox, { recursive: true, force: true });
    }
  }, 60000);
});

async function freePort() {
  const server = createTcpServer();
  await new Promise<void>((resolvePromise, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolvePromise));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Could not allocate an API port');
  await new Promise<void>((resolvePromise, reject) => server.close((error) => error ? reject(error) : resolvePromise()));
  return address.port;
}

async function waitForApi(apiUrl: string, process: ChildProcess) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (process.exitCode !== null) throw new Error(`FastAPI exited with code ${process.exitCode}`);
    try { if ((await fetch(apiUrl + '/health')).ok) return; } catch { /* server is starting */ }
    await delay(200);
  }
  throw new Error('FastAPI did not become healthy');
}

async function request<T = unknown>(baseUrl: string, path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has('content-type')) headers.set('content-type', 'application/json');
  const response = await fetch(baseUrl + path, { ...init, headers });
  const body = await response.json().catch(() => undefined);
  if (!response.ok) throw new Error(`${init.method ?? 'GET'} ${path} returned ${response.status}: ${JSON.stringify(body)}`);
  return body as T;
}

async function createAccount(apiUrl: string, outbox: string, mode: 'developer' | 'project') {
  const unique = `${mode}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  const email = `${unique}@example.com`;
  const password = 'ValidPassword123!';
  await request(apiUrl, '/api/v1/auth/register', {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ username: unique, email, password, password_confirm: password, mode }),
  });
  const files = await readdir(outbox);
  let code: string | undefined;
  for (const file of files) {
    const content = await readFile(join(outbox, file), 'utf8');
    if (content.includes(`To: ${email}\n`)) code = content.match(/Code: (\d{6})/)?.[1];
  }
  if (!code) throw new Error(`Verification email not found for ${email}`);
  await request(apiUrl, '/api/v1/auth/verify-email', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email, code }),
  });
  const tokens = await request<any>(apiUrl, '/api/v1/auth/login', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ email, password }),
  });
  const user = await request<any>(apiUrl, '/api/v1/users/me', { headers: { authorization: `Bearer ${tokens.access_token}` } });
  return { accessToken: tokens.access_token as string, userId: user.id as number };
}

async function connectChat(chatUrl: string, token: string, matchId: number, sockets: WebSocket[]) {
  const socket = new WebSocket(chatUrl.replace(/^http/, 'ws') + '/chat/ws');
  sockets.push(socket);
  await new Promise<void>((resolvePromise, reject) => {
    socket.once('open', resolvePromise);
    socket.once('error', reject);
  });
  const authenticated = nextEvent(socket, (event) => event.type === 'authenticated');
  socket.send(JSON.stringify({ type: 'authenticate', access_token: token, match_id: matchId }));
  expect(await authenticated).toMatchObject({ conversation_id: `match:${matchId}` });
  return socket;
}

function nextEvent(socket: WebSocket, accept: (event: any) => boolean) {
  return new Promise<any>((resolvePromise, reject) => {
    const onMessage = (data: WebSocket.RawData) => {
      let event: any;
      try { event = JSON.parse(data.toString()); } catch { return; }
      if (event.type === 'error') { cleanup(); reject(new Error(`Chat socket error: ${event.code}`)); }
      else if (accept(event)) { cleanup(); resolvePromise(event); }
    };
    const onError = (error: Error) => { cleanup(); reject(error); };
    const cleanup = () => { socket.off('message', onMessage); socket.off('error', onError); };
    socket.on('message', onMessage);
    socket.on('error', onError);
  });
}
