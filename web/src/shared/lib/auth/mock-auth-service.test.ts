import { beforeEach, describe, expect, it } from 'vitest';
import { AuthError } from './auth-types';
import { mockAuthService } from './mock-auth-service';

beforeEach(() => {
  localStorage.clear();
});

describe('mockAuthService', () => {
  it('registers a user and stores the session', async () => {
    const user = await mockAuthService.register({
      username: 'Test User',
      email: 'Test@Example.com',
      password: 'password123',
    });

    expect(user.username).toBe('Test User');
    expect(user.email).toBe('test@example.com');
    expect(user.id).toBeTruthy();
    expect(await mockAuthService.getCurrentUser()).toEqual(user);
  });

  it('rejects duplicate emails regardless of case', async () => {
    await mockAuthService.register({ username: 'Test User', email: 'test@example.com', password: 'password123' });

    await expect(mockAuthService.register({
      username: 'Another User',
      email: ' TEST@example.com ',
      password: 'password123',
    })).rejects.toMatchObject({
      code: 'duplicate_email',
    });
  });

  it('validates credentials at the service boundary', async () => {
    await expect(mockAuthService.register({
      username: 'Test User',
      email: 'invalid-email',
      password: 'short',
    })).rejects.toMatchObject({
      code: 'validation_error',
    });
  });

  it('logs in and logs out a user', async () => {
    await mockAuthService.register({ username: 'Test User', email: 'test@example.com', password: 'password123' });
    await mockAuthService.logout();

    const loggedInUser = await mockAuthService.login({ email: ' test@example.com ', password: 'password123' });

    expect(loggedInUser.email).toBe('test@example.com');
    expect(await mockAuthService.getCurrentUser()).toEqual(loggedInUser);

    await mockAuthService.logout();
    expect(await mockAuthService.getCurrentUser()).toBeNull();
  });

  it('returns null and clears the session for an unknown user id', async () => {
    localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'missing-user' }));

    await expect(mockAuthService.getCurrentUser()).resolves.toBeNull();
    expect(localStorage.getItem('matchmaker:v1:session')).toBeNull();
  });

  it('clears corrupted users data and treats the session as a guest session', async () => {
    localStorage.setItem('matchmaker:v1:users', JSON.stringify({ invalid: true }));
    localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'user-1' }));

    await expect(mockAuthService.getCurrentUser()).resolves.toBeNull();
    expect(localStorage.getItem('matchmaker:v1:users')).toBeNull();
    expect(localStorage.getItem('matchmaker:v1:session')).toBeNull();
  });

  it('throws a storage unavailable error when localStorage cannot be accessed', async () => {
    const originalStorage = Object.getOwnPropertyDescriptor(window, 'localStorage');

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('denied');
      },
    });

    await expect(mockAuthService.getCurrentUser()).rejects.toMatchObject({ code: 'storage_unavailable' });

    if (originalStorage) {
      Object.defineProperty(window, 'localStorage', originalStorage);
    }
  });
});
