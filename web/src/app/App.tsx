import { AppRouter } from './router';
import { AuthProvider } from './providers/AuthProvider';

export function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}