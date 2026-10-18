import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/providers/AuthProvider';
import { AuthForm } from '../../features/auth/ui/AuthForm';
import { AuthPageLayout } from '../../layouts/AuthPageLayout/AuthPageLayout';

export function LoginPage() {
  const { user, isInitialized, authError, authErrorCode, clearAuthError, login } = useAuth();
  const navigate = useNavigate();

  if (isInitialized && user) {
    return <Navigate to="/feed" replace />;
  }

  const handleSubmit = async (input: { email: string; password: string }) => {
    await login(input);
    navigate('/feed', { replace: true });
  };

  return (
    <AuthPageLayout>
      <AuthForm
        mode="login"
        title="Войти в аккаунт"
        description="Авторизуйтесь, чтобы получить доступ к защищённым разделам."
        submitLabel="Войти"
        onSubmit={handleSubmit}
        externalError={authError}
        externalErrorCode={authErrorCode}
        onClearExternalError={clearAuthError}
      />
    </AuthPageLayout>
  );
}
