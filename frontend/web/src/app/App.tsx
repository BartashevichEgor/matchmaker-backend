import { AppRouter } from './router';
import { AuthProvider } from './providers/AuthProvider';
import { apiAuthService } from '../shared/lib/auth/api-auth-service';

export function App() {
  return (
    <AuthProvider authService={apiAuthService}>
      <AppRouter />
    </AuthProvider>
  );
}
