import { z } from 'zod';
import type { FastifyInstance, FastifyRequest } from 'fastify';
import { BackendError, type MatchSummary } from '../backend-client.js';
import type { ChatAccess } from '../backend-client.js';
import type { DbPool } from '../db.js';
import { conversationId, getOrCreateConversation } from '../conversations.js';
import { listMessages, MessageConflict, insertMessage, publicMessage } from '../messages.js';
import { markRead, unreadCount } from '../read-state.js';

type Backend = {
  getChatAccess(matchId: number, token: string): Promise<ChatAccess>;
  getChatSendAccess(matchId: number, token: string): Promise<ChatAccess>;
  listMatches(token: string): Promise<MatchSummary[]>;
};

function bearer(request: FastifyRequest) {
  const header = request.headers.authorization;
  const match = typeof header === 'string' && /^Bearer ([^\s]+)$/.exec(header);
  if (!match) throw new BackendError(401);
  return match[1]!;
}

async function authorized(request: FastifyRequest, backend: Backend, pool: DbPool, id: string, sending = false) {
  const match = /^match:([1-9]\d{0,17})$/.exec(id);
  if (!match) throw new BackendError(404);
  const matchId = Number(match[1]);
  if (!Number.isSafeInteger(matchId)) throw new BackendError(404);
  const token = bearer(request);
  const access = sending ? await backend.getChatSendAccess(matchId, token) : await backend.getChatAccess(matchId, token);
  const conversation = await getOrCreateConversation(pool, matchId);
  return { access, conversation };
}

function sendError(reply: { code(status: number): { send(body: unknown): unknown }; header(name: string, value: string): unknown }, error: unknown) {
  if (error instanceof BackendError) {
    const status = [401, 403, 404, 429].includes(error.status) ? error.status : 503;
    if (status === 429) reply.header('retry-after', error.retryAfter ?? '60');
    return reply.code(status).send({ error: status === 401 ? 'unauthorized' : status === 403 ? 'forbidden' : status === 404 ? 'not_found' : status === 429 ? 'rate_limited' : 'unavailable' });
  }
  if (error instanceof z.ZodError || error instanceof TypeError || error instanceof RangeError) return reply.code(422).send({ error: 'invalid_request' });
  return reply.code(500).send({ error: 'internal_error' });
}

const messageBody = z.object({
  client_message_id: z.string().min(1).max(128),
  body: z.string().min(1).max(4000).refine((value) => value.trim().length > 0),
}).strict();

export function registerConversationRoutes(app: FastifyInstance, pool: DbPool, backend: Backend) {
  app.get('/chat/conversations', async (request, reply) => {
    try {
      const token = bearer(request);
      const matches = await backend.listMatches(token);
      const result = [];
      for (let offset = 0; offset < matches.length; offset += 10) {
        const batch = await Promise.all(matches.slice(offset, offset + 10).map(async (match) => {
          try {
            const access = await backend.getChatAccess(match.id, token);
            const conversation = await getOrCreateConversation(pool, match.id);
            const last = await pool.query(
              'SELECT id, conversation_id, sender_user_id, client_message_id, body, created_at FROM message WHERE conversation_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1',
              [conversation.id],
            );
            return {
              id: conversationId(match.id),
              match_id: match.id,
              created_at: conversation.created_at,
              project: access.project,
              candidate: access.candidate,
              last_message: last.rows[0] ? publicMessage(last.rows[0]) : null,
              unread_count: await unreadCount(pool, conversation.id, access.current_user_id),
            };
          } catch (error) {
            if (error instanceof BackendError && [403, 404].includes(error.status)) return undefined;
            throw error;
          }
        }));
        result.push(...batch.filter((item) => item !== undefined));
      }
      return reply.send(result);
    } catch (error) {
      return sendError(reply, error);
    }
  });

  app.get<{ Params: { conversation_id: string }; Querystring: { cursor?: string; limit?: string } }>(
    '/chat/conversations/:conversation_id/messages',
    async (request, reply) => {
      try {
        const { access, conversation } = await authorized(request, backend, pool, request.params.conversation_id);
        const limitValue = request.query.limit === undefined ? 50 : Number(request.query.limit);
        if (!Number.isInteger(limitValue) || limitValue < 1 || limitValue > 100) throw new TypeError('Invalid limit');
        const page = await listMessages(pool, conversation.id, request.query.cursor, limitValue);
        return reply.send({ conversation_id: conversation.id, messages: page.messages.map(publicMessage), next_cursor: page.nextCursor, unread_count: await unreadCount(pool, conversation.id, access.current_user_id) });
      } catch (error) {
        return sendError(reply, error);
      }
    },
  );

  app.post<{ Params: { conversation_id: string } }>('/chat/conversations/:conversation_id/messages', async (request, reply) => {
    try {
      const input = messageBody.parse(request.body);
      const { access, conversation } = await authorized(request, backend, pool, request.params.conversation_id, true);
      const result = await insertMessage(pool, conversation.id, access.current_user_id, input.client_message_id, input.body);
      return reply.code(result.duplicate ? 200 : 201).send({ message: publicMessage(result.message), duplicate: result.duplicate, unread_count: await unreadCount(pool, conversation.id, access.current_user_id) });
    } catch (error) {
      if (error instanceof MessageConflict) return reply.code(409).send({ error: 'client_message_id_conflict' });
      return sendError(reply, error);
    }
  });

  app.post<{ Params: { conversation_id: string } }>('/chat/conversations/:conversation_id/read', async (request, reply) => {
    try {
      const { access, conversation } = await authorized(request, backend, pool, request.params.conversation_id);
      return reply.send({ conversation_id: conversation.id, unread_count: await markRead(pool, conversation.id, access.current_user_id) });
    } catch (error) {
      return sendError(reply, error);
    }
  });
}
