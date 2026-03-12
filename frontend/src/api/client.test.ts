import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { apiClient, buildUrl } from './client';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('apiClient', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  describe('buildUrl', () => {
    it('concatenates base URL and path', () => {
      const url = buildUrl('/services/');
      expect(url).toContain('/services/');
    });

    it('appends query params', () => {
      const url = buildUrl('/appointments/available', { date: '2025-01-15', service_id: '3' });
      expect(url).toContain('date=2025-01-15');
      expect(url).toContain('service_id=3');
    });
  });

  describe('Authorization header', () => {
    it('attaches Bearer token when auth_token exists in sessionStorage', async () => {
      sessionStorage.setItem('auth_token', 'my-secret-token');
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ id: 1 }), { status: 200 }));

      await apiClient.get('/services/');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBe('Bearer my-secret-token');
    });

    it('does not attach Authorization header when no token', async () => {
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

      await apiClient.get('/services/');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBeUndefined();
    });
  });

  describe('get', () => {
    it('parses JSON response and returns typed data', async () => {
      const data = [{ id: 1, name: 'Manicure' }];
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify(data), { status: 200 }));

      const result = await apiClient.get('/services/');
      expect(result).toEqual(data);
    });
  });

  describe('post', () => {
    it('sends JSON body and returns parsed response', async () => {
      const body = { name: 'Gel Nails', duration_minutes: 60, price: 45 };
      const response = { id: 1, ...body };
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 201 }));

      const result = await apiClient.post('/services/', body);

      expect(result).toEqual(response);
      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('POST');
      expect(JSON.parse(options.body)).toEqual(body);
    });
  });

  describe('put', () => {
    it('sends PUT request with JSON body', async () => {
      const body = { name: 'Updated Nails' };
      mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ id: 1, ...body }), { status: 200 }));

      await apiClient.put('/services/1', body);

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PUT');
    });
  });

  describe('delete', () => {
    it('sends DELETE request and handles 204 No Content', async () => {
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }));

      await expect(apiClient.delete('/appointments/1')).resolves.toBeUndefined();

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('DELETE');
    });
  });

  describe('error handling', () => {
    it('throws ApiError with status and detail on non-2xx response', async () => {
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Not found' }), { status: 404 })
      );

      try {
        await apiClient.get('/appointments/999');
        expect.fail('Should have thrown');
      } catch (err: unknown) {
        const apiErr = err as { status: number; detail: string };
        expect(apiErr.status).toBe(404);
        expect(apiErr.detail).toBe('Not found');
      }
    });

    it('throws ApiError with default detail when response has no JSON', async () => {
      mockFetch.mockResolvedValueOnce(
        new Response('Server Error', { status: 500 })
      );

      try {
        await apiClient.get('/services/');
        expect.fail('Should have thrown');
      } catch (err: unknown) {
        const apiErr = err as { status: number; detail: string };
        expect(apiErr.status).toBe(500);
        expect(apiErr.detail).toBe('An unexpected error occurred');
      }
    });

    it('clears auth_token from sessionStorage on 403 response', async () => {
      sessionStorage.setItem('auth_token', 'expired-token');
      mockFetch.mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Forbidden' }), { status: 403 })
      );

      try {
        await apiClient.get('/services/');
      } catch {
        // expected
      }

      expect(sessionStorage.getItem('auth_token')).toBeNull();
    });
  });
});
