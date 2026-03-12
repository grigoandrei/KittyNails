import { describe, it, expect, vi, afterEach } from 'vitest';
import { isPastDate, getTodayISO } from './date';

describe('isPastDate', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns true for a date in the past', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 5, 15)); // June 15, 2025
    expect(isPastDate('2025-06-14')).toBe(true);
  });

  it('returns false for today', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 5, 15));
    expect(isPastDate('2025-06-15')).toBe(false);
  });

  it('returns false for a future date', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 5, 15));
    expect(isPastDate('2025-06-16')).toBe(false);
  });
});

describe('getTodayISO', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns today in YYYY-MM-DD format', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 0, 5)); // Jan 5, 2025
    expect(getTodayISO()).toBe('2025-01-05');
  });

  it('pads single-digit months and days', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2025, 2, 3)); // March 3, 2025
    expect(getTodayISO()).toBe('2025-03-03');
  });
});
