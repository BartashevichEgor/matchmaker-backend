import { useId, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import type { ZodIssue } from 'zod';
import type { AuthErrorCode, CredentialsInput, RegisterInput } from '../../../shared/lib/auth/auth-types';
import { credentialsSchema, registerFormSchema } from '../../../shared/lib/auth/auth-schemas';

type AuthFormMode = 'login' | 'register';
type FieldName = 'username' | 'email' | 'password' | 'confirmPassword';
type FieldErrors = Partial<Record<FieldName, string>>;

type AuthFormProps =
  | {
      mode: 'login';
      title: string;
      description: string;
      submitLabel: string;
      onSubmit: (input: CredentialsInput) => Promise<void>;
      externalError?: string | null;
      externalErrorCode?: AuthErrorCode | null;
      onClearExternalError?: () => void;
    }
  | {
      mode: 'register';
      title: string;
      description: string;
      submitLabel: string;
      onSubmit: (input: RegisterInput) => Promise<void>;
      externalError?: string | null;
      externalErrorCode?: AuthErrorCode | null;
      onClearExternalError?: () => void;
    };

function isFieldName(value: unknown): value is FieldName {
  return value === 'username' || value === 'email' || value === 'password' || value === 'confirmPassword';
}

function getFieldErrors(issues: readonly ZodIssue[]): FieldErrors {
  return issues.reduce<FieldErrors>((errors, issue) => {
    const fieldName = issue.path[0];

    if (isFieldName(fieldName) && !errors[fieldName]) {
      errors[fieldName] = issue.message;
    }

    return errors;
  }, {});
}

function getExternalFieldErrors(
  error: string | null | undefined,
  errorCode: AuthErrorCode | null | undefined,
): FieldErrors {
  if (!error) {
    return {};
  }

  if (errorCode === 'duplicate_email') {
    return { email: error };
  }

  if (errorCode === 'invalid_credentials') {
    return { password: error };
  }

  return {};
}

function EyeIcon({ isOpen }: { isOpen: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" focusable="false">
      <path d="M2.5 12s3.4-5 9.5-5 9.5 5 9.5 5-3.4 5-9.5 5-9.5-5-9.5-5Z" />
      <circle cx="12" cy="12" r="2.5" />
      {!isOpen ? <path d="m4 4 16 16" /> : null}
    </svg>
  );
}

export function AuthForm({
  mode,
  title,
  description,
  submitLabel,
  onSubmit,
  externalError,
  externalErrorCode,
  onClearExternalError,
}: AuthFormProps) {
  const usernameId = useId();
  const emailId = useId();
  const passwordId = useId();
  const confirmPasswordId = useId();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const [isConfirmPasswordVisible, setIsConfirmPasswordVisible] = useState(false);

  const externalFieldErrors = getExternalFieldErrors(externalError, externalErrorCode);
  const visibleFieldErrors = { ...externalFieldErrors, ...fieldErrors };
  const invalidCredentials = externalErrorCode === 'invalid_credentials';
  const visibleFormError = formError ?? (Object.keys(externalFieldErrors).length === 0 ? externalError : null);

  const clearExternalError = () => {
    onClearExternalError?.();
    setFormError(null);
  };

  const handleFieldChange = (fieldName: FieldName, value: string) => {
    if (fieldName === 'username') {
      setUsername(value);
    } else if (fieldName === 'email') {
      setEmail(value);
    } else if (fieldName === 'password') {
      setPassword(value);
    } else {
      setConfirmPassword(value);
    }

    setFieldErrors((currentErrors) => ({ ...currentErrors, [fieldName]: undefined }));
    clearExternalError();
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFieldErrors({});
    setFormError(null);
    clearExternalError();

    if (mode === 'register') {
      const validationResult = registerFormSchema.safeParse({ username, email, password, confirmPassword });

      if (!validationResult.success) {
        setFieldErrors(getFieldErrors(validationResult.error.issues));
        return;
      }

      const { confirmPassword: _confirmPassword, ...registerInput } = validationResult.data;
      setIsSubmitting(true);

      try {
        await onSubmit(registerInput);
      } catch {
        // AuthProvider exposes the service error through externalError.
      } finally {
        setIsSubmitting(false);
      }

      return;
    }

    const validationResult = credentialsSchema.safeParse({ email, password });

    if (!validationResult.success) {
      setFieldErrors(getFieldErrors(validationResult.error.issues));
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(validationResult.data);
    } catch {
      // AuthProvider exposes the service error through externalError.
    } finally {
      setIsSubmitting(false);
    }
  };

  const usernameError = visibleFieldErrors.username;
  const emailError = visibleFieldErrors.email;
  const passwordError = visibleFieldErrors.password;
  const confirmPasswordError = visibleFieldErrors.confirmPassword;
  const emailHasError = Boolean(emailError || invalidCredentials);
  const passwordHasError = Boolean(passwordError || invalidCredentials);

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <div className="auth-form__header">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      {visibleFormError ? (
        <p role="alert" className="auth-form__form-error">
          {visibleFormError}
        </p>
      ) : null}

      {mode === 'register' ? (
        <div className="auth-form__field">
          <label htmlFor={usernameId}>Имя пользователя</label>
          <input
            id={usernameId}
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => handleFieldChange('username', event.target.value)}
            placeholder="username"
            aria-invalid={Boolean(usernameError)}
            aria-describedby={usernameError ? `${usernameId}-error` : undefined}
          />
          {usernameError ? (
            <p id={`${usernameId}-error`} className="auth-form__field-error" role="alert">
              {usernameError}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="auth-form__field">
        <label htmlFor={emailId}>E-mail</label>
        <input
          id={emailId}
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => handleFieldChange('email', event.target.value)}
          placeholder="you@example.com"
          aria-invalid={emailHasError}
          aria-describedby={emailError ? `${emailId}-error` : undefined}
        />
        {emailError ? (
          <p id={`${emailId}-error`} className="auth-form__field-error" role="alert">
            {emailError}
          </p>
        ) : null}
      </div>

      <div className="auth-form__field">
        <label htmlFor={passwordId}>Пароль</label>
        <div className="auth-form__password-control">
          <input
            id={passwordId}
            type={isPasswordVisible ? 'text' : 'password'}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            value={password}
            onChange={(event) => handleFieldChange('password', event.target.value)}
            placeholder="Не менее 8 символов"
            aria-invalid={passwordHasError}
            aria-describedby={passwordError ? `${passwordId}-error` : undefined}
          />
          <button
            className="auth-form__password-toggle"
            type="button"
            aria-label={isPasswordVisible ? 'Скрыть пароль' : 'Показать пароль'}
            aria-pressed={isPasswordVisible}
            aria-controls={passwordId}
            onClick={() => setIsPasswordVisible((visible) => !visible)}
          >
            <EyeIcon isOpen={isPasswordVisible} />
          </button>
        </div>
        {passwordError ? (
          <p id={`${passwordId}-error`} className="auth-form__field-error" role="alert">
            {passwordError}
          </p>
        ) : null}
      </div>

      {mode === 'login' ? <div className="auth-form__forgot-password">Забыли пароль?</div> : null}

      {mode === 'register' ? (
        <div className="auth-form__field">
          <label htmlFor={confirmPasswordId}>Подтвердите пароль</label>
          <div className="auth-form__password-control">
            <input
              id={confirmPasswordId}
              type={isConfirmPasswordVisible ? 'text' : 'password'}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => handleFieldChange('confirmPassword', event.target.value)}
              placeholder="Повторите пароль"
              aria-invalid={Boolean(confirmPasswordError)}
              aria-describedby={confirmPasswordError ? `${confirmPasswordId}-error` : undefined}
            />
            <button
              className="auth-form__password-toggle"
              type="button"
              aria-label={isConfirmPasswordVisible ? 'Скрыть пароль' : 'Показать пароль'}
              aria-pressed={isConfirmPasswordVisible}
              aria-controls={confirmPasswordId}
              onClick={() => setIsConfirmPasswordVisible((visible) => !visible)}
            >
              <EyeIcon isOpen={isConfirmPasswordVisible} />
            </button>
          </div>
          {confirmPasswordError ? (
            <p id={`${confirmPasswordId}-error`} className="auth-form__field-error" role="alert">
              {confirmPasswordError}
            </p>
          ) : null}
        </div>
      ) : null}

      <button className="button button-primary auth-form__submit" type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Отправка...' : submitLabel}
      </button>

      {mode === 'login' ? (
        <p className="auth-form__switch">
          Нет аккаунта?{' '}
          <Link className="auth-form__switch-link" to="/register">
            Зарегистрироваться
          </Link>
        </p>
      ) : null}

      {mode === 'register' ? (
        <p className="auth-form__switch">
          Уже есть аккаунт?{' '}
          <Link className="auth-form__switch-link" to="/login">
            Войти
          </Link>
        </p>
      ) : null}
    </form>
  );
}
