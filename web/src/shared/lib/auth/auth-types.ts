export type User = {
  id: string;
  username: string;
  email: string;
  createdAt: string;
};

export type CredentialsInput = {
  email: string;
  password: string;
};

export type RegisterInput = CredentialsInput & {
  username: string;
};

export type RegisterFormInput = RegisterInput & {
  confirmPassword: string;
};

export type AuthService = {
  register(input: RegisterInput): Promise<User>;
  login(input: CredentialsInput): Promise<User>;
  verifyEmail(email: string, code: string): Promise<void>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<User | null>;
};

export type AuthErrorCode =
  | 'duplicate_email'
  | 'duplicate_username'
  | 'invalid_credentials'
  | 'email_unverified'
  | 'network_error'
  | 'storage_unavailable'
  | 'validation_error';

export class AuthError extends Error {
  code: AuthErrorCode;
  cause?: unknown;

  constructor(code: AuthErrorCode, message: string, cause?: unknown) {
    super(message);
    this.name = 'AuthError';
    this.code = code;
    this.cause = cause;
  }
}
