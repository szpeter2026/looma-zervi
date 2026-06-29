/**
 * Validation utilities shared across brands.
 */

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isPasswordStrong(password: string): boolean {
  return password.length >= 8;
}
