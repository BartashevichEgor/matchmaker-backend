import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import type { DbPool } from '../src/db.js';
import { getOrCreateConversation } from '../src/conversations.js';
import { listMessages, MessageConflict, insertMessage } from '../src/messages.js';
import { clearTestData, connectTestPool, databaseUrl } from './db-test-helpers.js';

describe.skipIf(!databaseUrl)('chat message repository', () => {
  let pool: DbPool;
  beforeAll(async () => { pool = await connectTestPool(); });
  beforeEach(async () => { await clearTestData(pool); });
  afterAll(async () => { await pool?.end(); });

  it('creates one conversation per match and deduplicates retries without crossing conversations', async () => {
    const first = await getOrCreateConversation(pool, 42);
    expect(await getOrCreateConversation(pool, 42)).toMatchObject({ id: first.id });
    await getOrCreateConversation(pool, 43);
    const created = await insertMessage(pool, first.id, 7, 'client-1', 'Hello');
    expect(created.duplicate).toBe(false);
    expect((await insertMessage(pool, first.id, 7, 'client-1', 'Hello')).duplicate).toBe(true);
    await expect(insertMessage(pool, 'match:43', 7, 'client-1', 'leak')).rejects.toBeInstanceOf(MessageConflict);
  });

  it('stores only one row when the same client retry races', async () => {
    const conversation = await getOrCreateConversation(pool, 42);
    const results = await Promise.all(Array.from({ length: 8 }, () => insertMessage(pool, conversation.id, 7, 'racing-id', 'once')));
    expect(results.filter((result) => !result.duplicate)).toHaveLength(1);
    expect(results.filter((result) => result.duplicate)).toHaveLength(7);
    const count = await pool.query('SELECT count(*)::int AS total FROM message WHERE conversation_id = $1', [conversation.id]);
    expect(count.rows[0].total).toBe(1);
  });

  it('returns stable ascending cursor pages without repeating messages', async () => {
    const conversation = await getOrCreateConversation(pool, 42);
    for (const id of ['a', 'b', 'c']) await insertMessage(pool, conversation.id, 7, id, id);
    await pool.query('UPDATE message SET created_at = $2 WHERE conversation_id = $1', [conversation.id, new Date('2026-11-15T12:00:00.123Z')]);
    const first = await listMessages(pool, conversation.id, undefined, 2);
    const second = await listMessages(pool, conversation.id, first.nextCursor ?? undefined, 2);
    expect(first.messages.map((message) => message.body)).toEqual(['a', 'b']);
    expect(second.messages.map((message) => message.body)).toEqual(['c']);
    expect(second.nextCursor).toBeNull();
  });
});
