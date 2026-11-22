import { z } from 'zod';
import { Buffer } from 'node:buffer';
import websocket from '@fastify/websocket';
import type { FastifyInstance } from 'fastify';
import type { WebSocket } from 'ws';
import { BackendError, type ChatAccess } from './backend-client.js';
import type { DbPool } from './db.js';
import { getOrCreateConversation } from './conversations.js';
import { MessageConflict, insertMessage, publicMessage } from './messages.js';
import { markRead } from './read-state.js';

type Backend = { getChatAccess(matchId: number, token: string): Promise<ChatAccess> };
type Session = { token: string; matchId: number; userId: number; conversationId: string };

const authenticate = z.object({ type: z.literal('authenticate'), access_token: z.string().min(1).max(4096), match_id: z.number().int().positive() }).strict();
const send = z.object({ type: z.literal('send'), client_message_id: z.string().min(1).max(128), body: z.string().min(1).max(4000).refine((value) => value.trim().length > 0) }).strict();
const read = z.object({ type: z.literal('read'), last_read_message_id: z.number().int().positive().optional() }).strict();
// shortcut: broadcasts stay in this process; add shared pub/sub when running multiple chat replicas.
const peers = new Map<string, Set<WebSocket>>();

function emit(socket: WebSocket, event: unknown) {
  if (socket.readyState === socket.OPEN) socket.send(JSON.stringify(event));
}

function error(socket: WebSocket, code: string, closeCode?: number) {
  emit(socket, { type: 'error', code });
  if (closeCode && socket.readyState === socket.OPEN) socket.close(closeCode, code);
}

export async function registerWebSocket(app: FastifyInstance, pool: DbPool, backend: Backend, allowedOrigins: string[]) {
  await app.register(websocket, { options: { maxPayload: 16384 } });
  app.get('/chat/ws', {
    websocket: true,
    preHandler: async (request, reply) => {
      const origin = request.headers.origin;
      if (origin && !allowedOrigins.includes(origin)) return reply.code(403).send({ error: 'forbidden' });
    },
  }, (socket) => {
    let session: Session | undefined;
    let queue = Promise.resolve();
    let queuedMessages = 0;
    const timeout = setTimeout(() => error(socket, 'unauthorized', 4401), 5000);
    timeout.unref();

    const cleanup = () => {
      clearTimeout(timeout);
      if (session) {
        const room = peers.get(session.conversationId);
        room?.delete(socket);
        if (room?.size === 0) peers.delete(session.conversationId);
      }
    };
    socket.on('close', cleanup);
    socket.on('error', cleanup);
    socket.on('message', (raw, isBinary) => {
      if (queuedMessages >= 32) return error(socket, 'unavailable', 1013);
      queuedMessages += 1;
      queue = queue.then(async () => {
        if (socket.readyState !== socket.OPEN) return;
        const data = Buffer.isBuffer(raw) ? raw : Array.isArray(raw) ? Buffer.concat(raw) : Buffer.from(raw as ArrayBuffer);
        if (isBinary || data.length > 16384) return error(socket, 'invalid_message', 4400);
        let event: unknown;
        try { event = JSON.parse(data.toString()); } catch { return error(socket, 'invalid_message', 4400); }

        if (!session) {
          const input = authenticate.safeParse(event);
          if (!input.success) return error(socket, 'invalid_message', 4400);
          try {
            const access = await backend.getChatAccess(input.data.match_id, input.data.access_token);
            const conversation = await getOrCreateConversation(pool, input.data.match_id);
            session = { token: input.data.access_token, matchId: input.data.match_id, userId: access.current_user_id, conversationId: conversation.id };
            let room = peers.get(conversation.id);
            if (!room) peers.set(conversation.id, (room = new Set()));
            room.add(socket);
            clearTimeout(timeout);
            emit(socket, { type: 'authenticated', conversation_id: conversation.id });
          } catch (cause) {
            error(socket, cause instanceof BackendError && cause.status === 401 ? 'unauthorized' : cause instanceof BackendError && cause.status === 403 ? 'forbidden' : cause instanceof BackendError && cause.status === 404 ? 'forbidden' : 'unavailable', 4401);
          }
          return;
        }

        const sendEvent = send.safeParse(event);
        if (sendEvent.success) {
          try {
            const access = await authorizeAgain(backend, session);
            if (access.current_user_id !== session.userId) return error(socket, 'forbidden', 4403);
            const result = await insertMessage(pool, session.conversationId, session.userId, sendEvent.data.client_message_id, sendEvent.data.body);
            emit(socket, { type: 'message_ack', client_message_id: sendEvent.data.client_message_id, duplicate: result.duplicate, message: publicMessage(result.message) });
            if (!result.duplicate) {
              const payload = JSON.stringify({ type: 'message', message: publicMessage(result.message) });
              for (const peer of peers.get(session.conversationId) ?? []) {
                if (peer.readyState === peer.OPEN) {
                  if (peer.bufferedAmount > 1_000_000) peer.close(1013, 'slow_consumer');
                  else peer.send(payload);
                }
              }
            }
          } catch (cause) {
            if (cause instanceof MessageConflict) return error(socket, 'invalid_message');
            if (cause instanceof BackendError) return error(socket, cause.status === 401 ? 'unauthorized' : 'forbidden', 4401);
            error(socket, 'unavailable', 1011);
          }
          return;
        }

        const readEvent = read.safeParse(event);
        if (!readEvent.success) return error(socket, 'invalid_message');
        try {
          const access = await authorizeAgain(backend, session);
          if (access.current_user_id !== session.userId) return error(socket, 'forbidden', 4403);
          const unread_count = await markRead(pool, session.conversationId, session.userId, readEvent.data.last_read_message_id);
          emit(socket, { type: 'read', unread_count });
        } catch (cause) {
          if (cause instanceof RangeError) return error(socket, 'invalid_message');
          if (cause instanceof BackendError) return error(socket, cause.status === 401 ? 'unauthorized' : 'forbidden', 4401);
          error(socket, 'unavailable', 1011);
        }
      }).catch(() => error(socket, 'unavailable', 1011)).finally(() => { queuedMessages -= 1; });
    });
  });
}

async function authorizeAgain(backend: Backend, session: Session) {
  const access = await backend.getChatAccess(session.matchId, session.token);
  if (access.expires_at && Date.parse(access.expires_at) <= Date.now()) throw new BackendError(401);
  return access;
}
