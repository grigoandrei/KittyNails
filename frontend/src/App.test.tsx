import { render, screen, waitFor } from '@testing-library/react';
import { vi, beforeEach, afterEach } from 'vitest';
import App from './App';

describe('App', () => {
  beforeEach(() => {
    // Mock fetch so BookingWizard's service fetch doesn't throw
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the booking wizard at root', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Book Your Appointment/i)).toBeInTheDocument();
    });
  });
});
