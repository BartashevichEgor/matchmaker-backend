import { AuthError, type AuthService, type CredentialsInput, type RegisterInput, type User } from './auth-types';
import { credentialsSchema, normalizeEmail, normalizeUsername, registerInputSchema } from './auth-schemas';

type StoredUser = User & { password: string };
type StoredUserRecord = {
  id: string;
  username?: string;
  email: string;
  password: string;
  createdAt: string;
};
type StoredSession = { userId: string };

const USERS_STORAGE_KEY = 'matchmaker:v1:users';
const SESSION_STORAGE_KEY = 'matchmaker:v1:session';

function getStorage(): Storage {
  try {
    return window.localStorage;
  } catch (error) {
    throw new AuthError('storage_unavailable', 'Локальное хранилище недоступно', error);
  }
}

function runStorageOperation<T>(operation: (storage: Storage) => T): T {
  try {
    return operation(getStorage());
  } catch (error) {
    if (error instanceof AuthError) {
      throw error;
    }

    throw new AuthError('storage_unavailable', 'Локальное хранилище недоступно', error);
  }
}

function safeRandomId() {
  return globalThis.crypto?.randomUUID?.() ?? `user-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toPublicUser(user: StoredUser): User {
  const { password: _password, ...publicUser } = user;
  return publicUser;
}

function readJson<T>(key: string): T | null {
  const rawValue = runStorageOperation((storage) => storage.getItem(key));

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as T;
  } catch {
    runStorageOperation((storage) => storage.removeItem(key));
    return null;
  }
}

function writeJson(key: string, value: unknown) {
  runStorageOperation((storage) => storage.setItem(key, JSON.stringify(value)));
}

function isStoredUserRecord(value: unknown): value is StoredUserRecord {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const record = value as Partial<StoredUserRecord>;

  return (
    typeof record.id === 'string' &&
    typeof record.email === 'string' &&
    typeof record.password === 'string' &&
    typeof record.createdAt === 'string' &&
    (record.username === undefined || typeof record.username === 'string')
  );
}

function readUsers(): StoredUser[] {
  const rawUsers = readJson<unknown>(USERS_STORAGE_KEY);

  if (rawUsers === null) {
    return [];
  }

  const isValidUsers = Array.isArray(rawUsers) && rawUsers.every(isStoredUserRecord);

  if (!isValidUsers) {
    runStorageOperation((storage) => storage.removeItem(USERS_STORAGE_KEY));
    return [];
  }

  return rawUsers.map((record) => {
    return {
      id: record.id,
      username: record.username?.trim() || record.email.split('@')[0],
      email: record.email,
      password: record.password,
      createdAt: record.createdAt,
    };
  });
}

function writeUsers(users: StoredUser[]) {
  writeJson(USERS_STORAGE_KEY, users);
}

function readSession(): StoredSession | null {
  const rawSession = readJson<unknown>(SESSION_STORAGE_KEY);

  if (rawSession === null) {
    return null;
  }

  if (typeof rawSession !== 'object' || rawSession === null) {
    runStorageOperation((storage) => storage.removeItem(SESSION_STORAGE_KEY));
    return null;
  }

  const session = rawSession as Partial<StoredSession>;

  if (typeof session.userId !== 'string' || session.userId.length === 0) {
    runStorageOperation((storage) => storage.removeItem(SESSION_STORAGE_KEY));
    return null;
  }

  return { userId: session.userId };
}

function writeSession(session: StoredSession | null) {
  if (session === null) {
    runStorageOperation((storage) => storage.removeItem(SESSION_STORAGE_KEY));
    return;
  }

  runStorageOperation((storage) => storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session)));
}

function normalizeCredentials(input: CredentialsInput): CredentialsInput {
  return {
    email: normalizeEmail(input.email),
    password: input.password,
  };
}

function normalizeRegisterInput(input: RegisterInput): RegisterInput {
  return {
    ...normalizeCredentials(input),
    username: normalizeUsername(input.username),
  };
}

function validateCredentials(input: CredentialsInput): CredentialsInput {
  const parsed = credentialsSchema.safeParse(normalizeCredentials(input));

  if (!parsed.success) {
    throw new AuthError('validation_error', parsed.error.issues[0]?.message ?? 'Некорректные данные');
  }

  return parsed.data;
}

function validateRegisterInput(input: RegisterInput): RegisterInput {
  const parsed = registerInputSchema.safeParse(normalizeRegisterInput(input));

  if (!parsed.success) {
    throw new AuthError('validation_error', parsed.error.issues[0]?.message ?? 'Некорректные данные');
  }

  return parsed.data;
}

function createUserRecord(input: RegisterInput): StoredUser {
  const validatedInput = validateRegisterInput(input);
  const users = readUsers();

  if (users.some((user) => user.email === validatedInput.email)) {
    throw new AuthError('duplicate_email', 'Пользователь с таким email уже существует');
  }

  const user: StoredUser = {
    id: safeRandomId(),
    username: validatedInput.username,
    email: validatedInput.email,
    password: validatedInput.password,
    createdAt: new Date().toISOString(),
  };

  writeUsers([...users, user]);
  writeSession({ userId: user.id });

  return user;
}

function authenticateUser(input: CredentialsInput): StoredUser {
  const validatedInput = validateCredentials(input);
  const users = readUsers();
  const matchedUser = users.find((user) => user.email === validatedInput.email);

  if (!matchedUser || matchedUser.password !== validatedInput.password) {
    throw new AuthError('invalid_credentials', 'Неверный email или пароль');
  }

  writeSession({ userId: matchedUser.id });

  return matchedUser;
}

async function register(input: RegisterInput): Promise<User> {
  return toPublicUser(createUserRecord(input));
}

async function login(input: CredentialsInput): Promise<User> {
  return toPublicUser(authenticateUser(input));
}

async function logout(): Promise<void> {
  writeSession(null);
}

async function getCurrentUser(): Promise<User | null> {
  const session = readSession();

  if (!session) {
    return null;
  }

  const users = readUsers();
  const matchedUser = users.find((user) => user.id === session.userId);

  if (!matchedUser) {
    writeSession(null);
    return null;
  }

  return toPublicUser(matchedUser);
}

export const mockAuthService: AuthService = {
  register,
  login,
  logout,
  getCurrentUser,
};
