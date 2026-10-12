# Pestino — Mobile build and store release

Target stores: Cafe Bazaar, Myket, Google Play, and the Apple App Store.
Application ID / bundle ID: `ir.pestino.app`. Display name: پستینو. Version: `pubspec.yaml` (`1.0.0+1`).

## 1. One-time setup

On a machine with the Flutter stable SDK (3.27 or newer) and JDK 17:

```bash
cd pestino/mobile
tool/bootstrap.sh              # runs flutter create for missing platform files, then pub get, analyze, test
```

`bootstrap.sh` does not overwrite the Pestino-specific files already in `android/` and `ios/`
(Gradle config, manifests, `Info.plist`, `PrivacyInfo.xcprivacy`). It generates the missing pieces:
Gradle wrapper jar, Xcode project, Podfile, launcher icons.

The platform files were written by hand in an environment without Flutter. Run `flutter analyze`
and build once on a real machine before the first store upload.

## 2. Android signing (required for store builds)

```bash
keytool -genkey -v -keystore ~/secure/pestino-upload.jks -keyalg RSA -keysize 2048 -validity 10000 -alias pestino
cp android/key.properties.example android/key.properties   # fill in; keep it out of Git
```

- Back up the keystore and passwords in two places. Losing the upload key blocks all future updates.
- Enable Play App Signing in Google Play Console so Google holds the app signing key.
- In CI, write `key.properties` and the keystore from encrypted secrets.
- Store builds pass `-PpestinoStoreBuild=true`. Gradle fails if the keystore is missing, so an unsigned or debug-signed build cannot be uploaded by mistake.

## 3. Build commands

```bash
export API_BASE_URL=https://api.pestino.ir     # https is required in release builds
tool/build_release.sh aab    # Google Play: build/app/outputs/bundle/release/app-release.aab
tool/build_release.sh apk    # Cafe Bazaar, Myket, direct download: per-ABI APKs
tool/build_release.sh ipa    # App Store: macOS + Xcode only
```

Each build runs `analyze` and `test`, obfuscates Dart code, and writes debug symbols to `build/symbols`.
Keep the symbols with each release for crash analysis.

The app refuses to start in release mode if `API_BASE_URL` is not https.

## 4. Store-specific checklist

| Item | Google Play | Cafe Bazaar / Myket | App Store |
|---|---|---|---|
| Format | AAB (required) | APK (per-ABI or universal; confirm in each console) | IPA via Xcode / Transporter |
| Minimum OS | Android 6.0 (API 23) | Android 6.0 | iOS 13 (set in Podfile) |
| Privacy policy URL | required | required | required |
| Data safety / privacy labels | Data safety form | store questionnaire | App Privacy (uses `PrivacyInfo.xcprivacy`) |
| In-app purchases | Google Play Billing | Bazaar IAP / Myket IAP SDK | StoreKit |
| Review | automated + manual | manual | manual, typically 1–2 days |

Before submitting:
- Confirm the current target API level requirement in the Google Play Console. It changes each year.
- Include the app's Persian store listing: title, short and full description, screenshots (phone and tablet), and feature graphic.
- Add the iOS `PrivacyInfo.xcprivacy` to the Runner target in Xcode. Declared data: phone number, photos, name, all used for app functionality, not tracking.
- Complete export-compliance answers (`ITSAppUsesNonExemptEncryption` is already set to false).
- Do not enable paid features until receipt verification for each store is implemented. Premium features are gated by the server, so a store build without IAP cannot grant premium.

## 5. Icons and screenshots

- App icon: 1024×1024 PNG, no transparency, used for Android adaptive icons and iOS. Generate sizes with `flutter_launcher_icons` (add it to `dev_dependencies` when the icon is final).
- Splash: a flat sand background (`#F7F4EC`) is already set in `launch_background.xml` and the iOS launch screen.

## 6. Release process

1. Bump `version:` in `pubspec.yaml` (build number must increase for every upload).
2. Run `tool/build_release.sh aab` (and `apk` for Bazaar/Myket) with the production `API_BASE_URL`.
3. Smoke-test the release build on a physical Android device: OTP login, farm create, analysis with camera and gallery, report, history, logout.
4. Upload to the store console, staged rollout where available (for example 10% on Google Play).
5. Tag the commit `v<version>` and archive the symbols.
