import type { DbPool } from './db.js';

export async function unreadCount(pool: DbPool, conversationId: string, userId: number) {
  const { rows } = await pool.query(
    'SELECT count(*)::int AS unread_count FROM message m LEFT JOIN conversation_read_state r ON r.conversation_id = m.conversation_id AND r.user_id = $2 LEFT JOIN message cursor_message ON cursor_message.id = r.last_read_message_id WHERE m.conversation_id = $1 AND m.sender_user_id <> $2 AND (r.last_read_message_id IS NULL OR (m.created_at, m.id) > (cursor_message.created_at, cursor_message.id))',
    [conversationId, userId],
  );
  return rows[0].unread_count as number;
}

export async function markRead(pool: DbPool, conversationId: string, userId: number, requestedMessageId?: number) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    let messageId: string | null;
    if (requestedMessageId === undefined) {
      const latest = await client.query('SELECT id FROM message WHERE conversation_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1', [conversationId]);
      messageId = latest.rows[0]?.id ?? null;
    } else {
      const requested = await client.query('SELECT id FROM message WHERE conversation_id = $1 AND id = $2', [conversationId, requestedMessageId]);
      if (!requested.rows[0]) throw new RangeError('Message does not belong to conversation');
      messageId = requested.rows[0].id;
    }
    if (messageId !== null) {
      await client.query(
        'INSERT INTO conversation_read_state(conversation_id, user_id, last_read_message_id) VALUES ($1, $2, $3) ON CONFLICT (conversation_id, user_id) DO UPDATE SET last_read_message_id = CASE WHEN conversation_read_state.last_read_message_id IS NULL OR (SELECT created_at FROM message WHERE id = EXCLUDED.last_read_message_id) > (SELECT created_at FROM message WHERE id = conversation_read_state.last_read_message_id) OR ((SELECT created_at FROM message WHERE id = EXCLUDED.last_read_message_id) = (SELECT created_at FROM message WHERE id = conversation_read_state.last_read_message_id) AND EXCLUDED.last_read_message_id > conversation_read_state.last_read_message_id) THEN EXCLUDED.last_read_message_id ELSE conversation_read_state.last_read_message_id END, last_read_at = now()',
        [conversationId, userId, messageId],
      );
    }
    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
  return unreadCount(pool, conversationId, userId);
}
