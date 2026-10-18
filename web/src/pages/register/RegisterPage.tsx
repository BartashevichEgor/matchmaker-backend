import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/providers/AuthProvider';
import { AuthForm } from '../../features/auth/ui/AuthForm';
import { AuthPageLayout } from '../../layouts/AuthPageLayout/AuthPageLayout';
import type { RegisterInput } from '../../shared/lib/auth/auth-types';

export function RegisterPage() {
  const { user, isInitialized, authError, authErrorCode, clearAuthError, register } = useAuth();
  const navigate = useNavigate();

  if (isInitialized && user) {
    return <Navigate to="/feed" replace />;
  }

  const handleSubmit = async (input: RegisterInput) => {
    await register(input);
    navigate('/feed', { replace: true });
  };

  return (
    <AuthPageLayout>
      <AuthForm
        mode="register"
        title="Создать аккаунт"
        description="Зарегистрируйтесь, чтобы сразу получить локальную mock-сессию."
        submitLabel="Создать аккаунт"
        onSubmit={handleSubmit}
        externalError={authError}
        externalErrorCode={authErrorCode}
        onClearExternalError={clearAuthError}
      />
    </AuthPageLayout>
  );
}
