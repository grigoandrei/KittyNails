import type { ApiError } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

function getAuthHeaders(): Record<string, string> {
  const token = sessionStorage.getItem('auth_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

function buildUrl(path: string, params?: Record<string, string>): string {
  // Ensure no double slashes between base and path
  const base = BASE_URL.replace(/\/+$/, '');
  const cleanPath = path.replace(/^\/+/, '');
  const url = new URL(`${base}/${cleanPath}`);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      url.searchParams.set(key, value);
    }
  }

  return url.toString();
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // On 403, clear the auth token
    if (response.status === 403) {
      sessionStorage.removeItem('auth_token');
    }

    let detail = 'An unexpected error occurred';
    try {
      const body = await response.json();
      if (body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // Response body wasn't valid JSON — keep default detail
    }

    const error: ApiError = { status: response.status, detail };
    throw error;
  }

  // 204 No Content — return undefined as T (used by delete)
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const response = await fetch(buildUrl(path, params), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    });
    return handleResponse<T>(response);
  },

  async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(buildUrl(path), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(response);
  },

  async put<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(buildUrl(path), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(response);
  },

  async delete(path: string): Promise<void> {
    const response = await fetch(buildUrl(path), {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    });
    return handleResponse<void>(response);
  },
};

// Also export the buildUrl helper for testing
export { buildUrl };
