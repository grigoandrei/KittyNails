import { describe, it, expect } from 'vitest';
import { isValidName, isValidPhone } from './validation';

describe('isValidName', () => {
  it('accepts a normal name', () => {
    expect(isValidName('Alice')).toBe(true);
  });

  it('accepts a single character name', () => {
    expect(isValidName('A')).toBe(true);
  });

  it('accepts a 100-character name', () => {
    expect(isValidName('a'.repeat(100))).toBe(true);
  });

  it('rejects an empty string', () => {
    expect(isValidName('')).toBe(false);
  });

  it('rejects a whitespace-only string', () => {
    expect(isValidName('   ')).toBe(false);
  });

  it('rejects a 101-character name', () => {
    expect(isValidName('a'.repeat(101))).toBe(false);
  });

  it('trims before validating', () => {
    expect(isValidName('  Bob  ')).toBe(true);
  });
});

describe('isValidPhone', () => {
  it('accepts a valid phone number', () => {
    expect(isValidPhone('1234567')).toBe(true);
  });

  it('accepts a 20-character phone number', () => {
    expect(isValidPhone('1'.repeat(20))).toBe(true);
  });

  it('rejects a 6-character phone number', () => {
    expect(isValidPhone('123456')).toBe(false);
  });

  it('rejects a 21-character phone number', () => {
    expect(isValidPhone('1'.repeat(21))).toBe(false);
  });

  it('rejects an empty string', () => {
    expect(isValidPhone('')).toBe(false);
  });

  it('trims before validating', () => {
    expect(isValidPhone('  1234567  ')).toBe(true);
  });
});
