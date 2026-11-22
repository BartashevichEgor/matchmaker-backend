import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import type { DbPool } from '../src/db.js';
import { getOrCreateConversation } from '../src/conversations.js';
import { insertMessage } from '../src/messages.js';
import { markRead, unreadCount } from '../src/read-state.js';
import { clearTestData, connectTestPool, databaseUrl } from './db-test-helpers.js';

describe.skipIf(!databaseUrl)('per-user unread state', () => {
  let pool: DbPool;
  beforeAll(async () => { pool = await connectTestPool(); });
  beforeEach(async () => { await clearTestData(pool); });
  afterAll(async () => { await pool?.end(); });

  it('counts only the other participant and advances one user cursor', async () => {
    const conversation = await getOrCreateConversation(pool, 42);
    await insertMessage(pool, conversation.id, 7, 'candidate-1', 'outbound');
    await insertMessage(pool, conversation.id, 3, 'owner-1', 'inbound');
    await insertMessage(pool, conversation.id, 3, 'owner-2', 'inbound again');
    expect(await unreadCount(pool, conversation.id, 7)).toBe(2);
    expect(await unreadCount(pool, conversation.id, 3)).toBe(1);
    expect(await markRead(pool, conversation.id, 7)).toBe(0);
    expect(await unreadCount(pool, conversation.id, 3)).toBe(1);
  });
});
