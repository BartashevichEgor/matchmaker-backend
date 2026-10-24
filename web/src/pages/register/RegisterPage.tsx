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
    const createdUser = await register(input);
    navigate(
      createdUser.id ? '/feed' : `/verify-email?email=${encodeURIComponent(input.email.trim().toLowerCase())}`,
      { replace: true },
    );
  };

  return (
    <AuthPageLayout>
      <AuthForm
        mode="register"
        title="Создать аккаунт"
        description="После регистрации подтвердите e-mail кодом из письма."
        submitLabel="Создать аккаунт"
        onSubmit={handleSubmit}
        externalError={authError}
        externalErrorCode={authErrorCode}
        onClearExternalError={clearAuthError}
      />
    </AuthPageLayout>
  );
}
