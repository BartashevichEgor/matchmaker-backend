import type { DbPool } from './db.js';

export const conversationId = (matchId: number) => 'match:' + matchId;

export async function getOrCreateConversation(pool: DbPool, matchId: number) {
  const id = conversationId(matchId);
  const { rows } = await pool.query(
    'INSERT INTO conversation(id, match_id) VALUES ($1, $2) ON CONFLICT (match_id) DO UPDATE SET match_id = EXCLUDED.match_id RETURNING id, match_id, created_at',
    [id, matchId],
  );
  return rows[0] as { id: string; match_id: string; created_at: Date };
}
