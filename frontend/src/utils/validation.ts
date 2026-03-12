/**
 * Validates that a name is between 1 and 100 characters (after trimming).
 */
export function isValidName(s: string): boolean {
  const trimmed = s.trim();
  return trimmed.length >= 1 && trimmed.length <= 100;
}

/**
 * Validates that a phone number is between 7 and 20 characters (after trimming).
 */
export function isValidPhone(s: string): boolean {
  const trimmed = s.trim();
  return trimmed.length >= 7 && trimmed.length <= 20;
}
