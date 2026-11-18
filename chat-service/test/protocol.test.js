import assert from 'node:assert/strict';
import test from 'node:test';
import { parseClientEvent, RoomConnections } from '../src/protocol.js';

test('accepts only a valid first authentication event', () => {
  assert.deepEqual(parseClientEvent('{"type":"authenticate","match_id":4,"access_token":"jwt"}'), {
    ok: true,
    event: { type: 'authenticate', matchId: 4, accessToken: 'jwt' },
  });
  assert.equal(parseClientEvent('{"type":"authenticate","match_id":0,"access_token":""}').ok, false);
});

test('validates message content before broadcasting', () => {
  assert.deepEqual(parseClientEvent('{"type":"message","text":" Привет ","client_message_id":"a1"}'), {
    ok: true,
    event: { type: 'message', text: 'Привет', clientMessageId: 'a1' },
  });
  assert.equal(parseClientEvent('{"type":"message","text":""}').ok, false);
});

test('broadcasts only to active room clients', () => {
  const sent = [];
  const active = { OPEN: 1, readyState: 1, send: (value) => sent.push(value) };
  const closed = { OPEN: 1, readyState: 3, send: () => sent.push('closed') };
  const rooms = new RoomConnections();
  rooms.add('match:1', active);
  rooms.add('match:1', closed);
  rooms.broadcast('match:1', { type: 'message', text: 'hello' });
  assert.deepEqual(sent, ['{"type":"message","text":"hello"}']);
});
