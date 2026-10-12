-- Pestino (پستینو) - admin password login
-- Only admin accounts use a password. Farmers keep OTP-only login.
-- Hashes use scrypt (see src/lib/password.ts). Lockout after repeated failures.

ALTER TABLE users
    ADD COLUMN password_hash          VARCHAR(255),
    ADD COLUMN password_failed_count  INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN password_locked_until  TIMESTAMPTZ,
    ADD COLUMN password_changed_at    TIMESTAMPTZ;
-- An admin without a password simply cannot log in; the CLI refuses to grant admin without one.
