import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { hashPassword, verifyPassword } from '../src/lib/password.js';
import { adminPasswordProblem } from '../src/lib/password-policy.js';

describe('admin password hashing and policy', () => {
  test('scrypt hash verifies only the right password', async () => {
    const h = await hashPassword('Correct-Horse-9');
    assert.match(h, /^scrypt\$/);
    assert.ok(!h.includes('Correct-Horse'));
    assert.equal(await verifyPassword('Correct-Horse-9', h), true);
    assert.equal(await verifyPassword('Correct-Horse-8', h), false);
  });

  test('two hashes of the same password differ (random salt)', async () => {
    assert.notEqual(await hashPassword('Same-Pass-1234'), await hashPassword('Same-Pass-1234'));
  });

  test('missing or malformed stored hash never verifies', async () => {
    assert.equal(await verifyPassword('anything-1234', null), false);
    assert.equal(await verifyPassword('anything-1234', 'plain'), false);
  });

  test('policy: length, letters and digits, no spaces', () => {
    assert.ok(adminPasswordProblem('short1'));
    assert.ok(adminPasswordProblem('onlyletterslong'));
    assert.ok(adminPasswordProblem('12345678901234'));
    assert.ok(adminPasswordProblem('has space 12345'));
    assert.equal(adminPasswordProblem('Strong-Pass-2026'), null);
  });
});
