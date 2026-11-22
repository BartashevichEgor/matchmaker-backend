import { z } from 'zod';

const matchSchema = z.object({
  id: z.number().int().positive(),
  project_id: z.number().int().positive(),
  candidate_id: z.number().int().positive(),
  room_key: z.string(),
  created_at: z.string(),
  project: z.object({ id: z.number(), title: z.string(), owner_id: z.number(), kind: z.literal('project') }),
  candidate: z.object({ user_id: z.number(), display_name: z.string(), headline: z.string().nullable(), avatar_url: z.string().nullable() }),
});

export type MatchSummary = z.infer<typeof matchSchema>;
export type ChatAccess = MatchSummary & { allowed: true; project_owner_id: number; current_user_id: number; expires_at: string | null };

export class BackendError extends Error {
  constructor(readonly status: number) {
    super('Matchmaker API returned ' + status);
  }
}

export function createBackendClient(baseUrl: string, timeoutMs: number, fetchImpl: typeof fetch = fetch) {
  async function request(path: string, token: string) {
    let response: Response;
    try {
      response = await fetchImpl(baseUrl + '/api/v1' + path, {
        headers: { authorization: 'Bearer ' + token, accept: 'application/json' },
        signal: AbortSignal.timeout(timeoutMs),
      });
    } catch {
      throw new BackendError(503);
    }
    if (!response.ok) throw new BackendError(response.status);
    try { return await response.json() as unknown; } catch { throw new BackendError(502); }
  }

  return {
    async getChatAccess(matchId: number, token: string): Promise<ChatAccess> {
      const result = await request('/matches/' + matchId + '/chat-access', token);
      try {
        const access = z.object({
        ...matchSchema.shape,
        allowed: z.literal(true),
        project_owner_id: z.number().int().positive(),
        current_user_id: z.number().int().positive(),
        expires_at: z.iso.datetime({ offset: true }).nullable(),
        }).parse(result);
        if (
          access.id !== matchId ||
          access.room_key !== 'match:' + matchId ||
          access.project.owner_id !== access.project_owner_id ||
          access.candidate.user_id !== access.candidate_id ||
          ![access.candidate_id, access.project_owner_id].includes(access.current_user_id)
        ) throw new Error('Inconsistent chat access response');
        if (access.expires_at && Date.parse(access.expires_at) <= Date.now()) throw new BackendError(401);
        return access;
      } catch (error) { if (error instanceof BackendError) throw error; throw new BackendError(502); }
    },
    async listMatches(token: string): Promise<MatchSummary[]> {
      const all: MatchSummary[] = [];
      for (let offset = 0; ; offset += 100) {
        let rows: MatchSummary[];
        try { rows = z.array(matchSchema).parse(await request('/matches?offset=' + offset + '&limit=100', token)); }
        catch (error) { if (error instanceof BackendError) throw error; throw new BackendError(502); }
        all.push(...rows);
        if (rows.length < 100) return all;
      }
    },
    async health() {
      try {
        const response = await fetchImpl(baseUrl + '/health', { signal: AbortSignal.timeout(timeoutMs) });
        return response.ok;
      } catch {
        return false;
      }
    },
  };
}
