import { describe, expect, it, vi } from 'vitest';
import { createBackendClient } from '../src/backend-client.js';

const access = {
  id: 42, project_id: 9, candidate_id: 7, room_key: 'match:42', created_at: '2026-11-15T12:00:00Z', allowed: true,
  current_user_id: 7, project_owner_id: 3, expires_at: null,
  project: { id: 9, title: 'API Platform', owner_id: 3, kind: 'project' },
  candidate: { user_id: 7, display_name: 'Ada', headline: 'Developer', avatar_url: null },
};

describe('FastAPI chat access client', () => {
  it('sends access tokens only in Authorization headers and validates the response', async () => {
    const fetchImpl = vi.fn(async () => new Response(JSON.stringify(access), { status: 200 }));
    const client = createBackendClient('http://api:8000', 1000, fetchImpl as typeof fetch);
    await expect(client.getChatAccess(42, 'secret-access')).resolves.toMatchObject({ current_user_id: 7 });
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).not.toContain('secret-access');
    expect(new Headers(init.headers).get('authorization')).toBe('Bearer secret-access');
  });

  it('maps upstream status without reading or returning its response body', async () => {
    const client = createBackendClient('http://api:8000', 1000, vi.fn(async () => new Response('private', { status: 403 })) as typeof fetch);
    await expect(client.getChatAccess(42, 'secret-access')).rejects.toMatchObject({ status: 403 });
  });

  it('accepts nullable candidate headlines returned by the matches endpoint', async () => {
    const match = { ...access, candidate: { ...access.candidate, headline: null } };
    const client = createBackendClient('http://api:8000', 1000, vi.fn(async () => new Response(JSON.stringify([match]), { status: 200 })) as typeof fetch);
    await expect(client.listMatches('secret-access')).resolves.toMatchObject([{ candidate: { headline: null } }]);
  });

  it('rejects a valid response after its access window has expired', async () => {
    const expired = { ...access, expires_at: '2020-01-01T00:00:00+00:00' };
    const client = createBackendClient('http://api:8000', 1000, vi.fn(async () => new Response(JSON.stringify(expired), { status: 200 })) as typeof fetch);
    await expect(client.getChatAccess(42, 'secret-access')).rejects.toMatchObject({ status: 401 });
  });
});
