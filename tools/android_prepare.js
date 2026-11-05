#!/usr/bin/env node
/**
 * Patches the Expo-generated Android project so that `assembleRelease`
 * produces a signed, installable APK with the configured release key.
 *
 * Signing material is read from environment variables; no secret belongs in
 * the repository or in an APK:
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

function matchingBrace(source, openIndex) {
  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;

  for (let index = openIndex; index < source.length; index += 1) {
    const char = source[index];
    const next = source[index + 1];
    if (lineComment) {
      if (char === '\n') lineComment = false;
      continue;
    }
    if (blockComment) {
      if (char === '*' && next === '/') {
        blockComment = false;
        index += 1;
      }
      continue;
    }
    if (quote) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === quote) quote = null;
      continue;
    }
    if (char === '/' && next === '/') {
      lineComment = true;
      index += 1;
      continue;
    }
    if (char === '/' && next === '*') {
      blockComment = true;
      index += 1;
      continue;
    }
    if (char === "'" || char === '"') {
      quote = char;
      continue;
    }
    if (char === '{') depth += 1;
    if (char === '}') {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  throw new Error('Unbalanced braces in generated build.gradle.');
}

function findBlock(source, name, start = 0, limit = source.length) {
  const matcher = new RegExp(`\\b${name}\\s*\\{`, 'g');
  matcher.lastIndex = start;
  const match = matcher.exec(source);
  if (!match || match.index >= limit) return null;
  const open = source.indexOf('{', match.index);
  const close = matchingBrace(source, open);
  if (close > limit) return null;
  return { start: match.index, open, close };
}

function groovyString(value) {
  const escaped = String(value)
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\$/g, '\\$');
  return `"${escaped}"`;
}

let gradle = fs.readFileSync(gradlePath, 'utf8');
const signingConfigs = findBlock(gradle, 'signingConfigs');
const buildTypes = findBlock(gradle, 'buildTypes');
if (!signingConfigs || !buildTypes) {
  console.error('Unexpected build.gradle layout: signingConfigs or buildTypes block is missing.');
  process.exit(1);
}

const signingBlock = `release {
            storeFile file(${groovyString(keystorePath.replace(/\\/g, '/'))})
            storeType "JKS"
            storePassword ${groovyString(storePassword)}
            keyAlias ${groovyString(alias)}
            keyPassword ${groovyString(keyPassword)}
        }`;
const existingReleaseConfig = findBlock(gradle, 'release', signingConfigs.open + 1, signingConfigs.close);
if (existingReleaseConfig) {
  gradle = `${gradle.slice(0, existingReleaseConfig.start)}${signingBlock}${gradle.slice(existingReleaseConfig.close + 1)}`;
} else {
  gradle = `${gradle.slice(0, signingConfigs.close)}\n        ${signingBlock}\n    ${gradle.slice(signingConfigs.close)}`;
}

const updatedBuildTypes = findBlock(gradle, 'buildTypes');
const releaseBuildType = findBlock(gradle, 'release', updatedBuildTypes.open + 1, updatedBuildTypes.close);
if (!releaseBuildType) {
  console.error('Unexpected build.gradle layout: release build type is missing.');
  process.exit(1);
}
const releaseBody = gradle.slice(releaseBuildType.open + 1, releaseBuildType.close);
const releaseSigningLine = /^(\s*)signingConfig\s+signingConfigs\.[A-Za-z0-9_]+\s*$/m;
if (releaseSigningLine.test(releaseBody)) {
  const bodyStart = releaseBuildType.open + 1;
  const updatedBody = releaseBody.replace(releaseSigningLine, '$1signingConfig signingConfigs.release');
  gradle = `${gradle.slice(0, bodyStart)}${updatedBody}${gradle.slice(releaseBuildType.close)}`;
} else {
  const lineStart = gradle.lastIndexOf('\n', releaseBuildType.start - 1) + 1;
  const indentation = gradle.slice(lineStart, releaseBuildType.start).match(/^[ \t]*/)[0];
  const insertAt = releaseBuildType.open + 1;
  gradle = `${gradle.slice(0, insertAt)}\n${indentation}    signingConfig signingConfigs.release${gradle.slice(insertAt)}`;
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
