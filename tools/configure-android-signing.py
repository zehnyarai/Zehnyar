#!/usr/bin/env python3
"""Owner-side, one-time setup. Never accepts/prints Gemini/Grok keys. Requires Secrets write permission."""
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
REPO = 'zehnyarai/Zehnyar'


def run(command, **kwargs):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        # Subprocess diagnostics could contain credentials; never echo them.
        raise RuntimeError('Required operation failed; no private material was printed. Check GitHub Secrets permissions or the local OpenSSL installation.')
    return result.stdout


def main():
    config_path = ROOT / 'android/signing-identity.json'
    config = json.loads(config_path.read_text())
    if config.get('status') == 'configured':
        raise RuntimeError('A stable identity is already pinned. Automatic replacement/rotation is forbidden.')
    if not shutil.which('gh') or not shutil.which('openssl'):
        raise RuntimeError('Install GitHub CLI and OpenSSL locally. Do not send any password or key in chat.')
    # Fail BEFORE creating a new identity if this connection cannot access Secrets.
    run(['gh', 'api', f'repos/{REPO}/actions/secrets/public-key'])
    existing = run(['gh', 'secret', 'list', '--repo', REPO]).decode()
    backup = ROOT / '.private/android-signing'
    key = backup / 'pestino-release.p12'
    password_path = backup / 'store-password.txt'
    names = {line.split()[0] for line in existing.splitlines() if line.strip()}
    state_path = backup / 'setup-state.json'
    if any(name in names for name in ('PESTINO_ANDROID_KEYSTORE_B64', 'PESTINO_ANDROID_STORE_PASSWORD')) and not state_path.exists():
        raise RuntimeError('Signing secrets already exist and are not from this pending setup. Do not overwrite an unknown identity.')
    if any(name in names for name in ('PESTINO_ANDROID_KEYSTORE_B64', 'PESTINO_ANDROID_STORE_PASSWORD')) and not (key.exists() and password_path.exists()):
        raise RuntimeError('Signing secrets already exist but local backup is missing. Restore the original identity; never generate a replacement.')
    if key.exists() != password_path.exists():
        raise RuntimeError('Incomplete private backup: do not overwrite it. Restore the matching original key/password.')
    os.umask(0o077)
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Partial uploads reuse the SAME local identity on retry; never silently rotate.
    if not key.exists():
        password = secrets.token_urlsafe(48)
        password_path.write_text(password)
        password_path.chmod(0o600)
        env = {**os.environ, 'PESTINO_SETUP_PASSWORD': password}
        with tempfile.TemporaryDirectory(prefix='encrypted-signing-', dir=backup) as temporary:
            private = str(Path(temporary) / 'encrypted-key.pem')
            cert_path = str(Path(temporary) / 'public-certificate.pem')
            run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-days', '10950',
                 '-keyout', private, '-out', cert_path, '-passout', 'env:PESTINO_SETUP_PASSWORD',
                 '-subj', '/CN=Pestino Android/O=Pestino/C=IR'], env=env)
            run(['openssl', 'pkcs12', '-export', '-inkey', private, '-in', cert_path,
                 '-name', config['key_alias'], '-out', str(key),
                 '-passin', 'env:PESTINO_SETUP_PASSWORD', '-passout', 'env:PESTINO_SETUP_PASSWORD'], env=env)
        key.chmod(0o600)
    password = password_path.read_text()
    env = {**os.environ, 'PESTINO_SETUP_PASSWORD': password}
    public_pem = run(['openssl', 'pkcs12', '-in', str(key), '-passin', 'env:PESTINO_SETUP_PASSWORD', '-clcerts', '-nokeys'], env=env)
    cert = run(['openssl', 'x509', '-outform', 'DER'], input=public_pem)
    digest = hashlib.sha256(cert).hexdigest()
    if state_path.exists() and json.loads(state_path.read_text()) != {'repo': REPO, 'certificate_sha256': digest}:
        raise RuntimeError('Local backup does not match the pending setup. Identity replacement is forbidden.')
    state_path.write_text(json.dumps({'repo': REPO, 'certificate_sha256': digest}))
    state_path.chmod(0o600)
    run(['gh', 'secret', 'set', 'PESTINO_ANDROID_KEYSTORE_B64', '--repo', REPO], input=base64.b64encode(key.read_bytes()))
    run(['gh', 'secret', 'set', 'PESTINO_ANDROID_STORE_PASSWORD', '--repo', REPO], input=password.encode())
    config.update(status='configured', certificate_sha256=digest)
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    print('Stable identity configured. Only the public certificate fingerprint was written into android/signing-identity.json.')
    print('Back up .private/android-signing securely OFFLINE; never commit/upload it or print its contents.')
    print('Increment app version/versionCode before the first stable release; never overwrite a legacy APK.')
    print('Commit only the public JSON on arena/e819b607-zehnyar, then push that same branch. No provider API key is needed.')
    print('This new identity cannot update old randomly signed installs without their original private signing key. Do not uninstall them.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError) as error:
        print(f'Setup blocked: {error}', file=sys.stderr)
        sys.exit(1)
