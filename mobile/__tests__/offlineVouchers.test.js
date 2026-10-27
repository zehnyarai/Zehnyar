import nacl from 'tweetnacl';
import { verifyOfflineVoucher } from '../src/core/offlineVouchers';

function encodeBase64Url(bytes) {
  const binary = Array.from(bytes, (value) => String.fromCharCode(value)).join('');
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function issueVoucher(pair, payload) {
  const message = new TextEncoder().encode(JSON.stringify(payload));
  return `${encodeBase64Url(message)}.${encodeBase64Url(nacl.sign.detached(message, pair.secretKey))}`;
}

describe('offline assessment vouchers', () => {
  const installId = 'cbf7187c-1c85-4fa9-9fc8-a97aa05bd901';
  const payload = { v: 1, id: 'voucher-one', installId, credits: 3, issuedAt: '2026-10-27T12:00:00+00:00' };
  let pair;
  let publicKey;

  beforeEach(() => {
    pair = nacl.sign.keyPair();
    publicKey = encodeBase64Url(pair.publicKey);
  });

  test('accepts a valid signed voucher for the current installation', () => {
    const code = issueVoucher(pair, payload);
    expect(verifyOfflineVoucher(code, installId, publicKey)).toMatchObject({ credits: 3, id: 'voucher-one' });
  });

  test('rejects a voucher issued to another installation', () => {
    const code = issueVoucher(pair, payload);
    expect(() => verifyOfflineVoucher(code, 'another-install', publicKey)).toThrow('VOUCHER_FOR_ANOTHER_INSTALL');
  });

  test('rejects tampering and unsupported credit amounts', () => {
    const code = issueVoucher(pair, payload);
    const [message, signature] = code.split('.');
    const changed = `${message.slice(0, -1)}${message.endsWith('A') ? 'B' : 'A'}.${signature}`;
    expect(() => verifyOfflineVoucher(changed, installId, publicKey)).toThrow('INVALID_VOUCHER');
    const invalidCode = issueVoucher(pair, { ...payload, credits: 99 });
    expect(() => verifyOfflineVoucher(invalidCode, installId, publicKey)).toThrow('INVALID_VOUCHER');
  });
});
