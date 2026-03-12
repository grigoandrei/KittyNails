import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthProvider';
import type { ReactNode } from 'react';

export function RequireAuth({ children }: { children: ReactNode }) {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/owner/login" replace />;
  }

  return <>{children}</>;
}
