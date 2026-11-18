const MAX_MESSAGE_LENGTH = 2000;

export function parseClientEvent(raw) {
  let event;
  try {
    event = JSON.parse(String(raw));
  } catch {
    return { ok: false, error: 'invalid_json' };
  }

  if (!event || typeof event !== 'object' || Array.isArray(event)) {
    return { ok: false, error: 'invalid_event' };
  }

  if (event.type === 'authenticate') {
    const matchId = Number(event.match_id);
    if (!Number.isInteger(matchId) || matchId <= 0 || typeof event.access_token !== 'string' || !event.access_token.trim()) {
      return { ok: false, error: 'invalid_authentication' };
    }
    return { ok: true, event: { type: 'authenticate', matchId, accessToken: event.access_token.trim() } };
  }

  if (event.type === 'message') {
    const text = typeof event.text === 'string' ? event.text.trim() : '';
    if (!text || text.length > MAX_MESSAGE_LENGTH) return { ok: false, error: 'invalid_message' };
    return { ok: true, event: { type: 'message', text, clientMessageId: String(event.client_message_id ?? '') } };
  }

  return { ok: false, error: 'unsupported_event' };
}

export class RoomConnections {
  #rooms = new Map();

  add(roomKey, socket) {
    const sockets = this.#rooms.get(roomKey) ?? new Set();
    sockets.add(socket);
    this.#rooms.set(roomKey, sockets);
  }

  remove(roomKey, socket) {
    const sockets = this.#rooms.get(roomKey);
    if (!sockets) return;
    sockets.delete(socket);
    if (!sockets.size) this.#rooms.delete(roomKey);
  }

  broadcast(roomKey, payload) {
    const message = JSON.stringify(payload);
    for (const socket of this.#rooms.get(roomKey) ?? []) {
      if (socket.readyState === socket.OPEN) socket.send(message);
    }
  }
}
