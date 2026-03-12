import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import { describe, it, expect, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from './AuthProvider';

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

function AuthConsumer() {
  const { token, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="token">{token ?? 'null'}</span>
      <button onClick={() => login('test-token-123')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

function renderWithRouter(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="*" element={<><AuthConsumer /><LocationDisplay /></>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('provides null token when sessionStorage is empty', () => {
    renderWithRouter();
    expect(screen.getByTestId('token').textContent).toBe('null');
  });

  it('reads existing token from sessionStorage on mount', () => {
    sessionStorage.setItem('auth_token', 'existing-token');
    renderWithRouter();
    expect(screen.getByTestId('token').textContent).toBe('existing-token');
  });

  it('login saves token to state and sessionStorage', async () => {
    const user = userEvent.setup();
    renderWithRouter();

    await user.click(screen.getByText('Login'));

    expect(screen.getByTestId('token').textContent).toBe('test-token-123');
    expect(sessionStorage.getItem('auth_token')).toBe('test-token-123');
  });

  it('logout clears token from state and sessionStorage and redirects to /owner/login', async () => {
    const user = userEvent.setup();
    sessionStorage.setItem('auth_token', 'some-token');
    renderWithRouter('/dashboard');

    await user.click(screen.getByText('Logout'));

    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(sessionStorage.getItem('auth_token')).toBeNull();
    expect(screen.getByTestId('location').textContent).toBe('/owner/login');
  });
});

describe('useAuth', () => {
  it('throws when used outside AuthProvider', () => {
    function BadConsumer() {
      useAuth();
      return null;
    }

    expect(() => {
      render(
        <MemoryRouter>
          <BadConsumer />
        </MemoryRouter>
      );
    }).toThrow('useAuth must be used within an AuthProvider');
  });
});
