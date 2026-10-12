/**
 * Application error with a stable machine-readable `code`.
 * Clients localize messages from `code`; `message` is for logs/debugging.
 */
export class AppError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = 'AppError';
  }

  static badRequest(code: string, message: string, details?: unknown) {
    return new AppError(400, code, message, details);
  }
  static unauthorized(code = 'UNAUTHORIZED', message = 'Authentication required') {
    return new AppError(401, code, message);
  }
  static forbidden(code = 'FORBIDDEN', message = 'Not allowed') {
    return new AppError(403, code, message);
  }
  static notFound(code = 'NOT_FOUND', message = 'Resource not found') {
    return new AppError(404, code, message);
  }
  static conflict(code: string, message: string) {
    return new AppError(409, code, message);
  }
  static payloadTooLarge(message = 'File too large') {
    return new AppError(413, 'PAYLOAD_TOO_LARGE', message);
  }
  static tooMany(code = 'RATE_LIMITED', message = 'Too many requests') {
    return new AppError(429, code, message);
  }
  static quotaExceeded(message = 'Monthly analysis quota exceeded') {
    return new AppError(402, 'QUOTA_EXCEEDED', message);
  }
  static upstream(message = 'AI service is temporarily unavailable') {
    return new AppError(502, 'AI_UPSTREAM_ERROR', message);
  }
  static notImplemented(code: string, message: string) {
    return new AppError(501, code, message);
  }
}
