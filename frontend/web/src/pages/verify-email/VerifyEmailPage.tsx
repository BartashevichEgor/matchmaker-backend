import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { type FormEvent, useState } from 'react';
import { useAuth } from '../../app/providers/AuthProvider';
import { AuthPageLayout } from '../../layouts/AuthPageLayout/AuthPageLayout';

export function VerifyEmailPage() {
  const { user, isInitialized, authError, clearAuthError, verifyEmail } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const email = searchParams.get('email') ?? '';
  const [code, setCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  if (isInitialized && user) return <Navigate to="/feed" replace />;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearAuthError();
    if (!email) {
      setLocalError('Не указан e-mail. Зарегистрируйтесь ещё раз.');
      return;
    }
    if (!/^\d{6}$/.test(code)) {
      setLocalError('Введите шестизначный код из письма.');
      return;
    }
    setLocalError(null);
    setIsSubmitting(true);
    try {
      await verifyEmail(email, code);
      navigate('/login', { replace: true });
    } catch {
      // AuthProvider exposes the safe API error below.
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthPageLayout>
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <div className="auth-form__header">
          <h1>Подтвердите e-mail</h1>
          <p>Введите код из письма, отправленного на {email || 'ваш e-mail'}.</p>
        </div>
        {localError || authError ? <p role="alert" className="auth-form__form-error">{localError ?? authError}</p> : null}
        <div className="auth-form__field">
          <label htmlFor="verification-code">Код подтверждения</label>
          <input id="verification-code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, ''))} placeholder="123456" />
        </div>
        <button className="button button-primary auth-form__submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Проверка...' : 'Подтвердить e-mail'}
        </button>
        <p className="auth-form__switch">Уже подтвердили e-mail? <Link className="auth-form__switch-link" to="/login">Войти</Link></p>
      </form>
    </AuthPageLayout>
  );
}
