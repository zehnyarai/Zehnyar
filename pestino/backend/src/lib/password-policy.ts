import { ADMIN_MIN_PASSWORD_LENGTH } from './password.js';

/** Returns a reason when the password is too weak for an admin account, otherwise null. */
export function adminPasswordProblem(password: string): string | null {
  if (password.length < ADMIN_MIN_PASSWORD_LENGTH) return `at least ${ADMIN_MIN_PASSWORD_LENGTH} characters`;
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) return 'letters and digits';
  if (/\s/.test(password)) return 'no spaces';
  return null;
}
