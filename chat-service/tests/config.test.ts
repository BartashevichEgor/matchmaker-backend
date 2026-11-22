import { describe, expect, it } from 'vitest';
import { loadConfig } from '../src/config.js';

const required = { CHAT_DATABASE_URL: 'postgresql://chat:pw@localhost/chat', MATCHMAKER_API_URL: 'http://localhost:8000' };

describe('chat service config', () => {
  it('uses bounded defaults and normalizes the API base URL', () => {
    expect(loadConfig(required)).toEqual({
      CHAT_PORT: 3000,
      CHAT_DATABASE_URL: required.CHAT_DATABASE_URL,
      MATCHMAKER_API_URL: required.MATCHMAKER_API_URL,
      CHAT_ALLOWED_ORIGINS: ['http://localhost:5173', 'http://127.0.0.1:5173'],
      CHAT_INTERNAL_TIMEOUT_MS: 3000,
    });
  });

  it('rejects missing and out-of-range settings', () => {
    expect(() => loadConfig({ ...required, CHAT_PORT: '70000' })).toThrow();
    expect(() => loadConfig({ CHAT_DATABASE_URL: required.CHAT_DATABASE_URL })).toThrow();
    expect(() => loadConfig({ ...required, CHAT_ALLOWED_ORIGINS: '*' })).toThrow();
    expect(() => loadConfig({ ...required, CHAT_ALLOWED_ORIGINS: 'https://example.test/path' })).toThrow();
  });
});
