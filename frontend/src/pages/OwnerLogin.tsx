import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';

const OwnerLogin: React.FC = () => {
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (!trimmed) {
      setError('Please enter a token.');
      return;
    }
    setError(null);
    login(trimmed);
    navigate('/owner/dashboard/services');
  };

  return (
    <div style={{ maxWidth: 420, margin: '0 auto', padding: 16 }}>
      <h1 style={{ textAlign: 'center', color: '#e91e8c', marginBottom: 8 }}>
        Owner Login
      </h1>
      <p style={{ textAlign: 'center', color: '#888', marginBottom: 24, fontSize: 14 }}>
        Enter your access token to manage the salon.
      </p>

      <form onSubmit={handleSubmit}>
        <label htmlFor="owner-token" style={{ display: 'block', marginBottom: 4, color: '#666' }}>
          Access Token
        </label>
        <input
          id="owner-token"
          type="text"
          value={token}
          onChange={e => { setToken(e.target.value); setError(null); }}
          placeholder="Paste your Bearer token"
          required
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: 8,
            border: '1px solid #f0e0eb',
            fontSize: 14,
            marginBottom: 12,
            boxSizing: 'border-box',
          }}
        />

        {error && (
          <p role="alert" style={{ color: '#c0392b', fontSize: 13, marginBottom: 8 }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: 8,
            border: 'none',
            backgroundColor: '#e91e8c',
            color: '#fff',
            fontSize: 16,
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          Log In
        </button>
      </form>
    </div>
  );
};

export default OwnerLogin;
