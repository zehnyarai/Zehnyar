#!/usr/bin/env node
/**
 * Patches the Expo-generated Android project so that `assembleRelease`
 * produces a signed, installable APK.
 *
 * Signing material is read from environment variables so no secret ever
 * lives in the repository:
 *   ANDROID_KEYSTORE_PATH, ANDROID_KEY_ALIAS,
 *   ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_PASSWORD
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const androidDir = path.join(root, 'mobile', 'android');
const gradlePath = path.join(androidDir, 'app', 'build.gradle');

if (!fs.existsSync(gradlePath)) {
  console.error('android/app/build.gradle not found. Run `npx expo prebuild -p android` first.');
  process.exit(1);
}

const keystorePath = process.env.ANDROID_KEYSTORE_PATH;
const alias = process.env.ANDROID_KEY_ALIAS;
const storePassword = process.env.ANDROID_KEYSTORE_PASSWORD;
const keyPassword = process.env.ANDROID_KEY_PASSWORD;

if (!keystorePath || !alias || !storePassword || !keyPassword) {
  console.error('Missing signing environment variables.');
  process.exit(1);
}

let gradle = fs.readFileSync(gradlePath, 'utf8');

const signingBlock = `
    signingConfigs {
        release {
            storeFile file("${keystorePath.replace(/\\/g, '/')}")
            storePassword "${storePassword}"
            keyAlias "${alias}"
            keyPassword "${keyPassword}"
        }
    }
`;

if (!gradle.includes('signingConfigs {')) {
  console.error('Unexpected build.gradle layout: no signingConfigs block.');
  process.exit(1);
}
gradle = gradle.replace('signingConfigs {', `${signingBlock.trim()}\n\n    signingConfigs {`);

const releaseTypeRegex = /(release\s*\{[\s\S]*?)signingConfig signingConfigs\.debug/;
if (releaseTypeRegex.test(gradle)) {
  gradle = gradle.replace(releaseTypeRegex, '$1signingConfig signingConfigs.release');
} else if (!/release\s*\{[\s\S]*?signingConfig signingConfigs\.release/.test(gradle)) {
  gradle = gradle.replace(/release\s*\{/, `release {\n            signingConfig signingConfigs.release`);
}

// Keep the release build lean but debuggable-free.
if (gradle.includes('minifyEnabled enableProguardInReleaseBuilds')) {
  gradle = gradle.replace('minifyEnabled enableProguardInReleaseBuilds', 'minifyEnabled false');
  gradle = gradle.replace('shrinkResources enableProguardInReleaseBuilds', 'shrinkResources false');
}

// Universal APK: ship all ABIs so one file installs on any phone.
const abiBlock = `
    splits {
        abi {
            enable false
            reset()
            include "armeabi-v7a", "arm64-v8a", "x86", "x86_64"
            universalApk true
        }
    }
`;
if (!gradle.includes('splits {')) {
  gradle = gradle.replace('android {', `android {${abiBlock}`);
}

fs.writeFileSync(gradlePath, gradle);

const propsPath = path.join(androidDir, 'gradle.properties');
if (fs.existsSync(propsPath)) {
  let props = fs.readFileSync(propsPath, 'utf8');
  props = props.replace(/^android\.enableProguardInReleaseBuilds=.*$/m, 'android.enableProguardInReleaseBuilds=false');
  if (!props.includes('android.enableProguardInReleaseBuilds')) {
    props += '\nandroid.enableProguardInReleaseBuilds=false\n';
  }
  fs.writeFileSync(propsPath, props);
}

console.log('Android release signing configured (universal APK, all ABIs).');
