import { logger } from './logger.js';
import { AppError } from './errors.js';

/**
 * Abstraction over the SMS gateway that delivers OTP codes.
 * Production implementations: Iranian providers (e.g. Kavenegar / SMS.ir / Melipayamak)
 * behind an HTTP adapter. Only the dev sender is included in the repo.
 */
export interface SmsSender {
  sendOtp(phone: string, code: string): Promise<void>;
}

/** Writes the code to the server log. Development only. */
export class DevLogSmsSender implements SmsSender {
  async sendOtp(phone: string, code: string): Promise<void> {
    logger.warn('DEV SMS (not delivered to a real phone)', { phone: maskPhone(phone), code });
  }
}

/** Used in production until a real gateway adapter is configured. Fails closed. */
export class UnconfiguredSmsSender implements SmsSender {
  async sendOtp(): Promise<void> {
    throw new AppError(503, 'SMS_NOT_CONFIGURED', 'SMS gateway is not configured');
  }
}

export function maskPhone(phone: string): string {
  return phone.length >= 7 ? `${phone.slice(0, 4)}***${phone.slice(-3)}` : '***';
}
