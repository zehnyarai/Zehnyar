import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml
from tools import signing_identity as signing

ROOT = Path(__file__).resolve().parent.parent


def identity(cert=b'public certificate fixture'):
    return {'schema_version': 1, 'status': 'configured', 'package_id': 'ir.pestino.app',
            'key_alias': 'pestino-release', 'certificate_sha256': hashlib.sha256(cert).hexdigest()}


def write_identity(tmp_path, data):
    path = tmp_path / 'identity.json'
    path.write_text(json.dumps(data))
    return path


def test_missing_or_invalid_public_pin_is_never_a_release_identity(tmp_path):
    for data in [{**identity(), 'status': 'not_configured'}, {**identity(), 'certificate_sha256': None},
                 {**identity(), 'certificate_sha256': 'made-up'}, {**identity(), 'key_alias': '../bad'},
                 {**identity(), 'package_id': 'another.app'}]:
        with pytest.raises(ValueError):
            signing.load_identity(write_identity(tmp_path, data))


def test_actual_certificate_and_apk_signer_must_match_pin(tmp_path):
    cert = tmp_path / 'cert.der'
    cert.write_bytes(b'public certificate fixture')
    signing.assert_certificate(cert, identity())
    digest = identity()['certificate_sha256']
    signing.assert_apk_signer(f'Signer #1 certificate SHA-256 digest: {digest}\n', identity())
    for text in ['', f'Signer #1 public key SHA-256 digest: {digest}',
                 'Signer #1 certificate SHA-256 digest: ' + 'f' * 64,
                 f'Signer #1 certificate SHA-256 digest: {digest}\nSigner #2 certificate SHA-256 digest: {digest}']:
        with pytest.raises(ValueError):
            signing.assert_apk_signer(text, identity())
    cert.write_bytes(b'different public certificate')
    with pytest.raises(ValueError):
        signing.assert_certificate(cert, identity())


def test_previous_stable_identity_cannot_be_silently_replaced(tmp_path):
    previous = tmp_path / 'SIGNING.json'
    previous.write_text(json.dumps(identity()))
    signing.check_previous(identity(), previous)
    with pytest.raises(ValueError):
        signing.check_previous(identity(b'new unrelated cert'), previous)


def fixture_repository(tmp_path):
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'android/app').mkdir(parents=True)
    for filename in ['signing_identity.py', 'configure-android-signing.py', 'sign-compat-apk.sh']:
        shutil.copy(ROOT / 'tools' / filename, tmp_path / 'tools' / filename)
    (tmp_path / 'android/signing-identity.json').write_text(json.dumps({**identity(), 'status': 'not_configured', 'certificate_sha256': None}))
    (tmp_path / 'package.json').write_text('{"version":"0.8.2"}')
    (tmp_path / 'android/app/build.gradle').write_text('versionCode 22\nversionName "0.8.2"')


def test_missing_identity_stops_signing_before_any_key_generation_or_apk(tmp_path):
    fixture_repository(tmp_path)
    env = {k: v for k, v in os.environ.items() if not k.startswith('PESTINO_ANDROID_')}
    result = subprocess.run(['bash', 'tools/sign-compat-apk.sh'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Signing blocked' in result.stderr
    assert not (tmp_path / 'apk-output').exists()
    assert not list(tmp_path.rglob('*.p12'))
    assert '-genkeypair' not in (ROOT / 'tools/sign-compat-apk.sh').read_text()


def test_ci_reports_blocked_without_claiming_an_installer_was_built(tmp_path):
    fixture_repository(tmp_path)
    output = tmp_path / 'outputs'
    summary = tmp_path / 'summary'
    result = subprocess.run(['python3', 'tools/signing_identity.py', '--ci-status'], cwd=tmp_path,
                            env={**os.environ, 'GITHUB_OUTPUT': str(output), 'GITHUB_STEP_SUMMARY': str(summary)}, capture_output=True, text=True)
    assert result.returncode == 0
    assert output.read_text() == 'ready=false\n'
    assert 'No installable update built' in summary.read_text()
    assert not list(tmp_path.rglob('*.p12'))


def test_version_must_advance_and_legacy_installer_is_not_overwritten(tmp_path):
    fixture_repository(tmp_path)
    (tmp_path / 'installers').mkdir()
    (tmp_path / 'installers/package-info.txt').write_text("versionCode='21'")
    assert signing.release_metadata(tmp_path) == ('0.8.2', 22)
    (tmp_path / 'installers/Pestino-0.8.2.apk').write_bytes(b'old archived APK')
    with pytest.raises(ValueError):
        signing.release_metadata(tmp_path)
    (tmp_path / 'installers/Pestino-0.8.2.apk').unlink()
    (tmp_path / 'android/app/build.gradle').write_text('versionCode 21\nversionName "0.8.2"')
    with pytest.raises(ValueError):
        signing.release_metadata(tmp_path)


def test_setup_permission_denial_creates_no_identity_or_private_key(tmp_path, monkeypatch):
    fixture_repository(tmp_path)
    spec = importlib.util.spec_from_file_location('setup_signing_test', ROOT / 'tools/configure-android-signing.py')
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)
    monkeypatch.setattr(setup, 'ROOT', tmp_path)
    monkeypatch.setattr(setup.shutil, 'which', lambda _: '/mock/tool')
    def denied(*args, **kwargs):
        raise RuntimeError('GitHub Secrets denied')
    monkeypatch.setattr(setup, 'run', denied)
    with pytest.raises(RuntimeError, match='denied'):
        setup.main()
    assert not (tmp_path / '.private').exists()
    assert json.loads((tmp_path / 'android/signing-identity.json').read_text())['status'] == 'not_configured'


@pytest.mark.skipif(not shutil.which('openssl'), reason='OpenSSL unavailable')
def test_one_time_setup_keeps_private_key_out_of_public_pin_and_reuses_it_after_partial_upload(tmp_path):
    fixture_repository(tmp_path)
    binary = tmp_path / 'bin'
    binary.mkdir()
    fake = binary / 'gh'
    fake.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
state=pathlib.Path(os.environ['TEST_GH_STATE'])
data=json.loads(state.read_text()) if state.exists() else {}
args=sys.argv[1:]
if args[:1]==['api']: print('{}')
elif args[:2]==['secret','list']:
 for name in data: print(name+'  test-only')
elif args[:2]==['secret','set']:
 name=args[2]
 if name=='PESTINO_ANDROID_STORE_PASSWORD' and os.environ.get('TEST_FAIL_SECOND')=='1': sys.exit(1)
 data[name]=sys.stdin.read();state.write_text(json.dumps(data))
else: sys.exit(1)
''')
    fake.chmod(0o700)
    env = {k: v for k, v in os.environ.items() if k not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    env.update(PATH=str(binary) + os.pathsep + os.environ['PATH'], TEST_GH_STATE=str(tmp_path / 'mock-secrets.json'), TEST_FAIL_SECOND='1')
    first = subprocess.run(['python3', 'tools/configure-android-signing.py'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert first.returncode != 0
    key = tmp_path / '.private/android-signing/pestino-release.p12'
    old_key = key.read_bytes()
    assert json.loads((tmp_path / 'android/signing-identity.json').read_text())['status'] == 'not_configured'
    env['TEST_FAIL_SECOND'] = '0'
    second = subprocess.run(['python3', 'tools/configure-android-signing.py'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert key.read_bytes() == old_key
    pin = signing.load_identity(tmp_path / 'android/signing-identity.json')
    data = json.loads((tmp_path / 'mock-secrets.json').read_text())
    assert base64.b64decode(data['PESTINO_ANDROID_KEYSTORE_B64']) == old_key
    for secret in data.values():
        assert secret not in second.stdout + second.stderr
        assert secret not in json.dumps(pin)
    assert not list((tmp_path / '.private').rglob('*.pem'))
    third = subprocess.run(['python3', 'tools/configure-android-signing.py'], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert third.returncode != 0  # no accidental rotation on rerun
    assert key.read_bytes() == old_key


def test_both_delivery_paths_require_stable_signing_and_upgrade_probe_never_uninstalls_between_stages():
    workflow = yaml.load((ROOT / '.github/workflows/pestino-standalone.yml').read_text(), Loader=yaml.BaseLoader)
    assert workflow['jobs']['deliver']['if'] == "needs.signing.outputs.ready == 'true'"
    steps = workflow['jobs']['apk']['steps']
    for step in steps:
        if step.get('name', '').startswith(('Sign ONLY', 'Verify actual')) or step.get('with', {}).get('name') == 'pestino-android-installer':
            assert step['if'] == "needs.signing.outputs.ready == 'true'"
    online = yaml.load((ROOT / '.github/workflows/pestino-apk.yml').read_text(), Loader=yaml.BaseLoader)
    assert "needs.configuration.outputs.ready == 'true'" in online['jobs']['apk']['if']
    script = (ROOT / 'tools/check-key-storage.sh').read_text()
    middle = script.split('pestinoStage seed', 1)[1].split('pestinoStage verify', 1)[0]
    assert 'adb install -r' in middle and 'adb uninstall' not in middle and 'pm clear' not in middle
