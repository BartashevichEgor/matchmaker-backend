import { AuthError, type AuthService, type CredentialsInput, type RegisterInput, type User } from './auth-types';
import { normalizeEmail, normalizeUsername } from './auth-schemas';

type TokenPayload = { access_token: string; refresh_token: string };
type ApiError = { detail?: string };

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const TOKENS_STORAGE_KEY = 'matchmaker:v1:tokens';

function readTokens(): TokenPayload | null {
  try {
    const value = window.localStorage.getItem(TOKENS_STORAGE_KEY);
    if (!value) return null;
    const parsed = JSON.parse(value) as Partial<TokenPayload>;
    return typeof parsed.access_token === 'string' && typeof parsed.refresh_token === 'string' ? parsed as TokenPayload : null;
  } catch (error) {
    throw new AuthError('storage_unavailable', 'Локальное хранилище недоступно', error);
  }
}

function writeTokens(tokens: TokenPayload | null) {
  try {
    if (tokens) window.localStorage.setItem(TOKENS_STORAGE_KEY, JSON.stringify(tokens));
    else window.localStorage.removeItem(TOKENS_STORAGE_KEY);
  } catch (error) {
    throw new AuthError('storage_unavailable', 'Локальное хранилище недоступно', error);
  }
}

function errorFromResponse(status: number, detail?: string): AuthError {
  if (status === 409) return new AuthError(detail?.toLowerCase().includes('username') ? 'duplicate_username' : 'duplicate_email', detail ?? 'Такой пользователь уже существует');
  if (status === 403) return new AuthError('email_unverified', 'Сначала подтвердите e-mail');
  if (status === 401) return new AuthError('invalid_credentials', 'Неверный e-mail или пароль');
  if (status === 422) return new AuthError('validation_error', 'Проверьте введённые данные');
  return new AuthError('network_error', detail ?? 'Сервер временно недоступен. Попробуйте ещё раз.');
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init.headers },
    });
  } catch (error) {
    throw new AuthError('network_error', 'Не удалось подключиться к серверу. Проверьте, что backend запущен.', error);
  }

  const body = await response.json().catch(() => ({})) as ApiError & T;
  if (!response.ok) throw errorFromResponse(response.status, body.detail);
  return body as T;
}

async function register(input: RegisterInput): Promise<User> {
  await request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username: normalizeUsername(input.username), email: normalizeEmail(input.email), password: input.password }),
  });
  // Registration does not authenticate a real user before e-mail verification.
  // The empty id is a private AuthProvider signal: route to verification rather
  // than creating a client session.
  return { id: '', username: normalizeUsername(input.username), email: normalizeEmail(input.email), createdAt: '' };
}

async function verifyEmail(email: string, code: string): Promise<void> {
  await request('/auth/verify-email', { method: 'POST', body: JSON.stringify({ email: normalizeEmail(email), code }) });
}

async function getCurrentUserOrThrow(accessToken: string): Promise<User> {
  return request<User>('/auth/session', { headers: { Authorization: `Bearer ${accessToken}` } });
}

async function login(input: CredentialsInput): Promise<User> {
  const tokens = await request<TokenPayload>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: normalizeEmail(input.email), password: input.password }),
  });
  writeTokens(tokens);
  try {
    return await getCurrentUserOrThrow(tokens.access_token);
  } catch (error) {
    writeTokens(null);
    throw error;
  }
}

async function getCurrentUser(): Promise<User | null> {
  const tokens = readTokens();
  if (!tokens) return null;
  try {
    return await getCurrentUserOrThrow(tokens.access_token);
  } catch (error) {
    if (error instanceof AuthError && error.code === 'invalid_credentials') writeTokens(null);
    throw error;
  }
}

async function logout(): Promise<void> {
  const tokens = readTokens();
  try {
    if (tokens) await request('/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${tokens.access_token}` } });
  } finally {
    writeTokens(null);
  }
}

export const apiAuthService: AuthService = { register, verifyEmail, login, logout, getCurrentUser };
