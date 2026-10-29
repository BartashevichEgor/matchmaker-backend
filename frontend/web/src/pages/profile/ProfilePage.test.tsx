import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../../app/providers/AuthProvider';
import { ProtectedRoute } from '../../app/providers/ProtectedRoute';
import type { AuthService } from '../../shared/lib/auth/auth-types';
import { ProfilePage } from './ProfilePage';

describe('ProfilePage', () => {
  it('logs out and navigates to registration', async () => {
    const user = userEvent.setup();
    const authService: AuthService = {
      getCurrentUser: vi.fn().mockResolvedValue({
        id: 'user-1',
        username: 'veronika',
        email: 'test@example.com',
        createdAt: '2026-01-01T00:00:00.000Z',
      }),
      login: vi.fn(),
      register: vi.fn(),
      verifyEmail: vi.fn(),
      logout: vi.fn().mockResolvedValue(undefined),
    };

    render(
      <MemoryRouter initialEntries={['/profile']}>
        <AuthProvider authService={authService}>
          <Routes>
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route path="/register" element={<div>Register Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    await user.click(await screen.findByRole('button', { name: 'Выйти из профиля' }));

    await waitFor(() => expect(screen.getByText('Register Page')).toBeInTheDocument());
    expect(authService.logout).toHaveBeenCalledOnce();
  });
});
