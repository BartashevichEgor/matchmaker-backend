import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  AuthError,
  type AuthErrorCode,
  type AuthService,
  type CredentialsInput,
  type RegisterInput,
  type User,
} from '../../shared/lib/auth/auth-types';
import { mockAuthService } from '../../shared/lib/auth/mock-auth-service';

type AuthContextValue = {
  user: User | null;
  isInitialized: boolean;
  authError: string | null;
  authErrorCode: AuthErrorCode | null;
  login: (input: CredentialsInput) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
  logout: () => Promise<void>;
  clearAuthError: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const SAFE_AUTH_ERROR_MESSAGE = 'Не удалось выполнить операцию. Попробуйте ещё раз.';

function getErrorDetails(error: unknown): { code: AuthErrorCode | null; message: string } {
  if (error instanceof AuthError) {
    return { code: error.code, message: error.message };
  }

  if (error instanceof Error) {
    return { code: null, message: SAFE_AUTH_ERROR_MESSAGE };
  }

  return { code: null, message: SAFE_AUTH_ERROR_MESSAGE };
}

export function AuthProvider({
  children,
  authService = mockAuthService,
}: {
  children: ReactNode;
  authService?: AuthService;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authErrorCode, setAuthErrorCode] = useState<AuthErrorCode | null>(null);

  useEffect(() => {
    let active = true;

    const initializeAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();

        if (!active) {
          return;
        }

        setUser(currentUser);
        setAuthError(null);
        setAuthErrorCode(null);
      } catch (error) {
        if (!active) {
          return;
        }

        setUser(null);
        const details = getErrorDetails(error);
        setAuthError(details.message);
        setAuthErrorCode(details.code);
      } finally {
        if (active) {
          setIsInitialized(true);
        }
      }
    };

    void initializeAuth();

    return () => {
      active = false;
    };
  }, [authService]);

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user,
      isInitialized,
      authError,
      authErrorCode,
      clearAuthError: () => {
        setAuthError(null);
        setAuthErrorCode(null);
      },
      login: async (input: CredentialsInput) => {
        setAuthError(null);
        setAuthErrorCode(null);

        try {
          const nextUser = await authService.login(input);
          setUser(nextUser);
          return nextUser;
        } catch (error) {
          const details = getErrorDetails(error);
          setAuthError(details.message);
          setAuthErrorCode(details.code);
          throw error;
        }
      },
      register: async (input: RegisterInput) => {
        setAuthError(null);
        setAuthErrorCode(null);

        try {
          const nextUser = await authService.register(input);
          setUser(nextUser);
          return nextUser;
        } catch (error) {
          const details = getErrorDetails(error);
          setAuthError(details.message);
          setAuthErrorCode(details.code);
          throw error;
        }
      },
      logout: async () => {
        setAuthError(null);
        setAuthErrorCode(null);

        try {
          await authService.logout();
          setUser(null);
        } catch (error) {
          const details = getErrorDetails(error);
          setAuthError(details.message);
          setAuthErrorCode(details.code);
          throw error;
        }
      },
    }),
    [authError, authErrorCode, authService, isInitialized, user],
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
