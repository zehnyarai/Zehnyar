"""Public identity pin, never a private signing key or an AI provider credential."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
IDENTITY = ROOT / 'android/signing-identity.json'
SECRETS = ('PESTINO_ANDROID_KEYSTORE_B64', 'PESTINO_ANDROID_STORE_PASSWORD')


def load_identity(path=IDENTITY):
    data = json.loads(Path(path).read_text())
    if data.get('schema_version') != 1 or data.get('package_id') != 'ir.pestino.app':
        raise ValueError('Invalid signing identity schema/package')
    if data.get('status') != 'configured':
        raise ValueError('Stable Android signing is not configured; no update APK may be published')
    if not re.fullmatch(r'[0-9a-f]{64}', data.get('certificate_sha256') or ''):
        raise ValueError('A real public certificate SHA-256 pin is required')
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', data.get('key_alias') or ''):
        raise ValueError('Invalid signing alias')
    return data


def check_previous(identity, previous_path=None):
    path = previous_path or ROOT / 'installers/SIGNING.json'
    if Path(path).exists():
        previous = json.loads(Path(path).read_text())
        if previous.get('certificate_sha256') != identity['certificate_sha256'] or previous.get('package_id') != identity['package_id']:
            raise ValueError('Signing identity differs from the last stable delivery; rotation is blocked')


def assert_certificate(cert_path, identity):
    if hashlib.sha256(Path(cert_path).read_bytes()).hexdigest() != identity['certificate_sha256']:
        raise ValueError('Keystore certificate does not match the approved public fingerprint')


def assert_apk_signer(text, identity):
    digests = re.findall(r'^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)\s*$', text, re.M)
    if len(digests) != 1 or digests[0].lower() != identity['certificate_sha256']:
        raise ValueError('Actual APK signer does not match the approved identity')


def release_metadata(root=ROOT):
    version = json.loads((root / 'package.json').read_text())['version']
    gradle = (root / 'android/app/build.gradle').read_text()
    code = re.search(r'\bversionCode\s+(\d+)', gradle)
    name = re.search(r'\bversionName\s+"([^"]+)"', gradle)
    if not re.fullmatch(r'\d+\.\d+\.\d+', version) or not code or not name or name[1] != version:
        raise ValueError('Android/package versions must agree before release')
    code = int(code[1])
    previous = root / 'installers/package-info.txt'
    if previous.exists():
        old = re.search(r"versionCode='(\d+)'", previous.read_text())
        if old and code <= int(old[1]):
            raise ValueError('Increase versionCode before a stable release; old installers must not be overwritten')
    if (root / f'installers/Pestino-{version}.apk').exists():
        raise ValueError('An installer with this version already exists; preserve the historical APK and increment the version')
    return version, code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ci-status', action='store_true')
    parser.add_argument('--certificate', type=Path)
    parser.add_argument('--verify-apk-info', type=Path)
    parser.add_argument('--record-apk', type=Path)
    args = parser.parse_args()
    try:
        identity = load_identity()
        check_previous(identity)
        version, version_code = release_metadata()
        if (args.ci_status or not (args.certificate or args.verify_apk_info or args.record_apk)) and any(not os.environ.get(key) for key in SECRETS):
            raise ValueError('Stable signing secrets are missing; no random/test signing fallback is allowed')
        if args.certificate:
            assert_certificate(args.certificate, identity)
        if args.verify_apk_info:
            assert_apk_signer(args.verify_apk_info.read_text(), identity)
        if args.record_apk:
            if not args.verify_apk_info:
                raise ValueError('Actual APK signer verification is required before recording delivery')
            record = {**identity, 'apk_sha256': hashlib.sha256(args.record_apk.read_bytes()).hexdigest(),
                      'apk_name': args.record_apk.name,
                      'source_commit': os.environ.get('GITHUB_SHA', ''),
                      'version': version, 'version_code': version_code,
                      'legacy_install_upgrade_compatible': False}
            # Compatibility with a historical random-key install is NEVER inferred.
            (args.record_apk.parent / 'SIGNING.json').write_text(json.dumps(record, indent=2) + '\n')
        if args.ci_status:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                output.write('ready=true\n')
    except (ValueError, OSError, json.JSONDecodeError) as error:
        if not args.ci_status:
            print(f'Signing blocked: {error}', file=sys.stderr)
            return 1
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('ready=false\n')
        message = f'No installable update built: {error}. Existing app/data must not be removed.'
        print(f'::notice title=Stable Android signing blocked::{message}')
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
                summary.write('## Android update not published\n' + message + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
