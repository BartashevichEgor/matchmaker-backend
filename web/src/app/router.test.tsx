import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRouter } from './router';
import { AuthProvider } from './providers/AuthProvider';

describe('AppRouter', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the home page on /', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText(/Подбор проектов и людей для совместной работы/i)).toBeInTheDocument());
  });

  it('renders the login page on /login', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Войти в аккаунт/i })).toBeInTheDocument());
  });

  it('renders the register page on /register', async () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Создать аккаунт/i })).toBeInTheDocument());
  });

  it('renders the feed placeholder on /feed for an authenticated user', async () => {
    setAuthenticatedUser();
    render(
      <MemoryRouter initialEntries={['/feed']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Лента/i })).toBeInTheDocument());
    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Matchmaker' })).toHaveAttribute('href', '/feed');
    expect(screen.getByText(/В разработке/i)).toBeInTheDocument();
  });

  it('renders the chat placeholder with matchId on /chat/:matchId for an authenticated user', async () => {
    setAuthenticatedUser();
    render(
      <MemoryRouter initialEntries={['/chat/abc']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Чат/i })).toBeInTheDocument());
    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Matchmaker' })).toHaveAttribute('href', '/feed');
    expect(screen.getByText(/matchId: abc/i)).toBeInTheDocument();
  });

  it.each([
    ['/projects', 'Проекты'],
    ['/profile', 'Профиль'],
    ['/matches', 'Мэтчи'],
  ])('renders the protected placeholder for %s', async (path, heading) => {
    setAuthenticatedUser();
    render(
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: heading })).toBeInTheDocument());
    expect(screen.getByRole('navigation', { name: 'Основная навигация' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Matchmaker' })).toHaveAttribute('href', '/feed');
  });

  it('renders the public 404 page on unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Страница не найдена/i })).toBeInTheDocument());
  });
});

function setAuthenticatedUser() {
  localStorage.setItem(
    'matchmaker:v1:users',
    JSON.stringify([
      { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
    ]),
  );
  localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'user-1' }));
}
