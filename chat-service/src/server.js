import http from 'node:http';
import { WebSocketServer } from 'ws';
import { parseClientEvent, RoomConnections } from './protocol.js';

const port = Number(process.env.CHAT_PORT ?? 8010);
const coreApiUrl = (process.env.CORE_API_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const rooms = new RoomConnections();

async function authorize(accessToken, matchId) {
  const response = await fetch(`${coreApiUrl}/matches/${matchId}/chat-access`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) throw new Error(`Match authorization failed with HTTP ${response.status}`);
  const match = await response.json();
  return { matchId, roomKey: typeof match.room_key === 'string' ? match.room_key : `match:${matchId}` };
}

function send(socket, payload) {
  if (socket.readyState === socket.OPEN) socket.send(JSON.stringify(payload));
}

const server = http.createServer((request, response) => {
  if (request.url === '/health') {
    response.writeHead(200, { 'content-type': 'application/json' });
    response.end(JSON.stringify({ status: 'ok', service: 'chat' }));
    return;
  }
  response.writeHead(404).end();
});

const websocketServer = new WebSocketServer({ noServer: true });
websocketServer.on('connection', (socket) => {
  let access = null;

  socket.on('message', async (raw) => {
    const parsed = parseClientEvent(raw);
    if (!parsed.ok) return send(socket, { type: 'error', code: parsed.error });

    if (parsed.event.type === 'authenticate') {
      try {
        access = await authorize(parsed.event.accessToken, parsed.event.matchId);
        rooms.add(access.roomKey, socket);
        send(socket, { type: 'authenticated', match_id: access.matchId });
      } catch {
        send(socket, { type: 'error', code: 'access_denied' });
        socket.close(1008, 'Access denied');
      }
      return;
    }

    if (!access) return send(socket, { type: 'error', code: 'authentication_required' });
    rooms.broadcast(access.roomKey, {
      type: 'message',
      match_id: access.matchId,
      text: parsed.event.text,
      client_message_id: parsed.event.clientMessageId,
      sent_at: new Date().toISOString(),
    });
  });

  socket.on('close', () => {
    if (access) rooms.remove(access.roomKey, socket);
  });
});

server.on('upgrade', (request, socket, head) => {
  if (request.url !== '/ws') return socket.destroy();
  websocketServer.handleUpgrade(request, socket, head, (client) => websocketServer.emit('connection', client, request));
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Matchmaker chat service listening on ws://127.0.0.1:${port}/ws`);
});
