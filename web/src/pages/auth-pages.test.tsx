import { beforeEach, describe, expect, it } from 'vitest';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../app/providers/AuthProvider';
import { AppRouter } from '../app/router';

beforeEach(() => {
  localStorage.clear();
});

describe('auth pages', () => {
  it('renders login inside a two-panel auth layout', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole('region', { name: 'Презентационная панель' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Matchmaker' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Войти в аккаунт/i })).toBeInTheDocument();
    expect(screen.queryByText('Вход', { selector: '.section-badge' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Зарегистрироваться' })).toHaveAttribute('href', '/register');
  });

  it('shows validation errors on the login form', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /войти/i }));

    expect(screen.getByText(/Введите email/i)).toBeInTheDocument();
  });

  it('shows client validation errors under the corresponding fields', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/e-?mail/i), 'invalid-email');
    await user.type(screen.getByLabelText(/^пароль$/i), 'short');
    await user.click(screen.getByRole('button', { name: /войти/i }));

    expect(screen.getByLabelText(/e-?mail/i)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText(/^пароль$/i)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText(/Введите корректный email/i)).toBeInTheDocument();
    expect(screen.getByText(/Пароль должен содержать не менее 8 символов/i)).toBeInTheDocument();
    expect(document.querySelector('.auth-form__alert')).not.toBeInTheDocument();
  });

  it('toggles password visibility', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/register']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    const password = screen.getByLabelText(/^пароль$/i);
    const showPasswordButtons = screen.getAllByRole('button', { name: 'Показать пароль' });

    expect(showPasswordButtons).toHaveLength(2);
    expect(password).toHaveAttribute('type', 'password');

    await user.click(showPasswordButtons[0]);

    expect(password).toHaveAttribute('type', 'text');
    expect(screen.getAllByRole('button', { name: 'Скрыть пароль' })).toHaveLength(1);
  });

  it('registers a user and redirects to feed', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/register']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(screen.queryByText('Регистрация', { selector: '.section-badge' })).not.toBeInTheDocument();
    await user.type(screen.getByLabelText(/имя пользователя/i), 'new-user');
    await user.type(screen.getByLabelText(/e-?mail/i), 'new@example.com');
    await user.type(screen.getByLabelText(/^пароль$/i), 'password123');
    await user.type(screen.getByLabelText(/подтвердите пароль/i), 'password123');
    await user.click(screen.getByRole('button', { name: /создать аккаунт/i }));

    await waitFor(() => expect(screen.getByRole('heading', { name: /Лента/i })).toBeInTheDocument());
  });

  it('logs in a returning user and redirects to feed', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );

    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/e-?mail/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^пароль$/i), 'password123');
    await user.click(screen.getByRole('button', { name: /войти/i }));

    await waitFor(() => expect(screen.getByRole('heading', { name: /Лента/i })).toBeInTheDocument());
  });

  it('redirects a user to /feed after login', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );
    const user = userEvent.setup();

    render(
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/login',
            state: { from: { pathname: '/chat/abc', search: '?tab=info', hash: '#messages' } },
          },
        ]}
      >
        <AuthProvider>
          <AppRouter />
          <LocationProbe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/e-?mail/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^пароль$/i), 'password123');
    await user.click(screen.getByRole('button', { name: /войти/i }));

    await waitFor(() => expect(screen.getByText(/Подходят тебе/i)).toBeInTheDocument());
    expect(screen.getByTestId('current-location')).toHaveTextContent('/feed');
  });

  it('redirects an authenticated user away from the login page', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );
    localStorage.setItem('matchmaker:v1:session', JSON.stringify({ userId: 'user-1' }));

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByRole('heading', { name: /Лента/i })).toBeInTheDocument());
  });

  it('shows auth errors from the provider on the login form', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );

    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/e-?mail/i), 'TEST@example.com');
    await user.type(screen.getByLabelText(/^пароль$/i), 'wrong-password');
    await user.click(screen.getByRole('button', { name: /войти/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/Неверный email или пароль/i),
    );
    expect(screen.getByLabelText(/e-?mail/i)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText(/^пароль$/i)).toHaveAttribute('aria-invalid', 'true');
    expect(document.querySelector('.auth-form__alert')).not.toBeInTheDocument();
  });

  it('shows auth errors from the provider on the register form', async () => {
    localStorage.setItem(
      'matchmaker:v1:users',
      JSON.stringify([
        { id: 'user-1', email: 'test@example.com', password: 'password123', createdAt: '2026-01-01T00:00:00.000Z' },
      ]),
    );

    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/register']}>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/имя пользователя/i), 'existing-user');
    await user.type(screen.getByLabelText(/e-?mail/i), ' TEST@example.com ');
    await user.type(screen.getByLabelText(/^пароль$/i), 'password123');
    await user.type(screen.getByLabelText(/подтвердите пароль/i), 'password123');
    await user.click(screen.getByRole('button', { name: /создать аккаунт/i }));

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/Пользователь с таким email уже существует/i),
    );
    expect(screen.getByLabelText(/e-?mail/i)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText(/^пароль$/i)).toHaveAttribute('aria-invalid', 'false');
  });
});

function LocationProbe() {
  const location = useLocation();

  return (
    <output data-testid="current-location">
      {location.pathname}
      {location.search}
      {location.hash}
    </output>
  );
}
