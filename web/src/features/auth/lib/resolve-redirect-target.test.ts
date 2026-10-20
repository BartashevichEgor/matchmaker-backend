import { describe, expect, it } from 'vitest';
import { resolveRedirectTarget } from './resolve-redirect-target';

describe('resolveRedirectTarget', () => {
  it('preserves a valid internal path with search and hash', () => {
    expect(
      resolveRedirectTarget({ from: { pathname: '/chat/abc', search: '?tab=info', hash: '#messages' } }),
    ).toBe('/chat/abc?tab=info#messages');
  });

  it.each(['https://example.com', '//example.com', '/\\example.com'])(
    'falls back for an external path: %s',
    (pathname) => {
      expect(resolveRedirectTarget({ from: { pathname } })).toBe('/feed');
    },
  );

  it.each(['relative/path', 'path/without/leading/slash'])(
    'falls back for a non internal path: %s',
    (pathname) => {
      expect(resolveRedirectTarget({ from: { pathname } })).toBe('/feed');
    },
  );

  it('falls back when from is missing or malformed', () => {
    expect(resolveRedirectTarget(undefined)).toBe('/feed');
    expect(resolveRedirectTarget(null)).toBe('/feed');
    expect(resolveRedirectTarget({})).toBe('/feed');
    expect(resolveRedirectTarget({ from: null })).toBe('/feed');
    expect(resolveRedirectTarget({ from: { pathname: 123 } })).toBe('/feed');
    expect(resolveRedirectTarget({ from: { pathname: '/chat/abc', search: 123, hash: 123 } })).toBe('/chat/abc');
  });
});