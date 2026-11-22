import { Buffer } from 'node:buffer';
import type { DbPool } from './db.js';

export type Message = { id: string; conversation_id: string; sender_user_id: string; client_message_id: string; body: string; created_at: Date };
export class MessageConflict extends Error {}

export function encodeCursor(message: Pick<Message, 'id' | 'created_at'>) {
  return Buffer.from(JSON.stringify([new Date(message.created_at).toISOString(), message.id])).toString('base64url');
}

export function decodeCursor(cursor: string) {
  try {
    if (cursor.length > 512 || !/^[A-Za-z0-9_-]+$/.test(cursor)) throw new Error();
    const value: unknown = JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8'));
    if (!Array.isArray(value) || value.length !== 2 || typeof value[0] !== 'string' || !Number.isSafeInteger(Number(value[1]))) throw new Error();
    const date = new Date(value[0]);
    if (!Number.isFinite(date.getTime()) || Number(value[1]) < 1) throw new Error();
    return { createdAt: date, id: Number(value[1]) };
  } catch {
    throw new TypeError('Invalid cursor');
  }
}

export function publicMessage(message: Message) {
  return {
    id: String(message.id),
    conversation_id: message.conversation_id,
    sender_user_id: Number(message.sender_user_id),
    client_message_id: message.client_message_id,
    body: message.body,
    created_at: message.created_at,
  };
}

export async function insertMessage(pool: DbPool, conversationId: string, senderUserId: number, clientMessageId: string, body: string) {
  const { rows } = await pool.query(
    'INSERT INTO message(conversation_id, sender_user_id, client_message_id, body) VALUES ($1, $2, $3, $4) ON CONFLICT (sender_user_id, client_message_id) DO NOTHING RETURNING id, conversation_id, sender_user_id, client_message_id, body, created_at',
    [conversationId, senderUserId, clientMessageId, body],
  );
  if (rows[0]) return { message: rows[0] as Message, duplicate: false };
  const existing = await pool.query(
    'SELECT id, conversation_id, sender_user_id, client_message_id, body, created_at FROM message WHERE sender_user_id = $1 AND client_message_id = $2',
    [senderUserId, clientMessageId],
  );
  const prior = existing.rows[0] as Message | undefined;
  if (!prior || prior.conversation_id !== conversationId) throw new MessageConflict('Client message ID already used');
  return { message: prior, duplicate: true };
}

export async function listMessages(pool: DbPool, conversationId: string, cursor: string | undefined, limit: number) {
  const position = cursor ? decodeCursor(cursor) : undefined;
  const { rows } = await pool.query(
    'SELECT id, conversation_id, sender_user_id, client_message_id, body, created_at FROM message WHERE conversation_id = $1 AND ($2::timestamptz IS NULL OR (created_at, id) < ($2, $3)) ORDER BY created_at DESC, id DESC LIMIT $4',
    [conversationId, position?.createdAt ?? null, position?.id ?? null, limit + 1],
  );
  const hasMore = rows.length > limit;
  const page = rows.slice(0, limit) as Message[];
  return { messages: page.reverse(), nextCursor: hasMore && page.length ? encodeCursor(page[0]!) : null };
}
