import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Navigate, Route, Routes } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthProvider';
import { ProtectedRoute } from './ProtectedRoute';
import type { AuthService, User } from '../../shared/lib/auth/auth-types';

beforeEach(() => {
  localStorage.clear();
});

function AuthStatus() {
  const { isInitialized, user, authError } = useAuth();

  return (
    <div>
      <p>initialized: {isInitialized ? 'yes' : 'no'}</p>
      <p>user: {user?.email ?? 'none'}</p>
      <p>error: {authError ?? 'none'}</p>
    </div>
  );
}

describe('AuthProvider', () => {
  it('restores an existing session on mount', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );
    localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'user-1' }));

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthStatus />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/initialized: yes/i)).toBeInTheDocument());
    expect(screen.getByText(/user: test@example.com/i)).toBeInTheDocument();
    expect(screen.getByText(/error: none/i)).toBeInTheDocument();
  });

  it('redirects guests from protected routes to login after initialization', async () => {
    render(
      <MemoryRouter initialEntries={['/feed']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/feed"
              element={
                <ProtectedRoute>
                  <div>feed content</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>login page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/login page/i)).toBeInTheDocument());
  });

  it('lets authenticated users stay inside protected routes', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );
    localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'user-1' }));

    render(
      <MemoryRouter initialEntries={['/feed']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/feed"
              element={
                <ProtectedRoute>
                  <div>feed content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/feed content/i)).toBeInTheDocument());
  });

  it('shows a storage unavailable error in the UI when localStorage cannot be accessed', async () => {
    const originalStorage = Object.getOwnPropertyDescriptor(window, 'localStorage');

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      get() {
        throw new Error('denied');
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthStatus />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/initialized: yes/i)).toBeInTheDocument());
    expect(screen.getByText(/user: none/i)).toBeInTheDocument();
    expect(screen.getByText(/error: .*недоступ/i)).toBeInTheDocument();

    if (originalStorage) {
      Object.defineProperty(window, 'localStorage', originalStorage);
    }
  });

  it('does not expose an unknown internal error message to the UI', async () => {
    const authService = createAuthService(null);
    authService.getCurrentUser = vi
      .fn()
      .mockRejectedValue(new Error('database password should never reach the browser UI'));

    render(
      <MemoryRouter>
        <AuthProvider authService={authService}>
          <AuthStatus />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/initialized: yes/i)).toBeInTheDocument());
    expect(screen.getByText(/Не удалось выполнить операцию/i)).toBeInTheDocument();
    expect(screen.queryByText(/database password/i)).not.toBeInTheDocument();
  });

  it('uses the latest auth service when the provider receives a replacement', async () => {
    const firstUser = createUser('first@example.com');
    const secondUser = createUser('second@example.com');
    const firstService = createAuthService(firstUser);
    const secondService = createAuthService(secondUser);

    const { rerender } = render(
      <MemoryRouter>
        <AuthProvider authService={firstService}>
          <AuthStatus />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/user: first@example.com/i)).toBeInTheDocument());

    rerender(
      <MemoryRouter>
        <AuthProvider authService={secondService}>
          <AuthStatus />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/user: second@example.com/i)).toBeInTheDocument());
    expect(secondService.getCurrentUser).toHaveBeenCalledTimes(1);
  });
});

function createUser(email: string): User {
  return {
    id: email,
    username: email.split('@')[0],
    email,
    createdAt: '2026-01-01T00:00:00.000Z',
  };
}

function createAuthService(currentUser: User | null): AuthService {
  const fallbackUser = currentUser ?? createUser('fallback@example.com');

  return {
    getCurrentUser: vi.fn().mockResolvedValue(currentUser),
    login: vi.fn().mockResolvedValue(fallbackUser),
    register: vi.fn().mockResolvedValue(fallbackUser),
    logout: vi.fn().mockResolvedValue(undefined),
  };
}
