#!/usr/bin/env node
/**
 * Fails the build if any Persian UI string contains Latin letters or Latin
 * digits. The product promise is a Persian layer with zero English words.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'mobile', 'src', 'i18n', 'dictionary.js'), 'utf8');

// Extract the `fa: { ... }` object literal by brace matching, then scan strings.
const start = source.indexOf('  fa: {');
if (start === -1) {
  console.error('Could not locate the fa dictionary');
  process.exit(1);
}
let depth = 0;
let end = start;
for (let i = source.indexOf('{', start); i < source.length; i += 1) {
  if (source[i] === '{') depth += 1;
  if (source[i] === '}') {
    depth -= 1;
    if (depth === 0) {
      end = i;
      break;
    }
  }
}
const block = source.slice(source.indexOf('{', start), end + 1);

const strings = block.match(/'[^'\\]*'|"[^"\\]*"/g) || [];
const latin = /[A-Za-z]/;
const latinDigits = /[0-9]/;
const offenders = strings.filter((literal) => latin.test(literal) || latinDigits.test(literal));

// Keys are also matched by the regex; ignore pure identifiers used as keys.
const keys = block.match(/^\s*([A-Za-z0-9_]+):/gm) || [];
const keyNames = new Set(keys.map((line) => line.trim().replace(':', '')));

const realOffenders = offenders.filter((literal) => {
  const value = literal.slice(1, -1);
  if (keyNames.has(value)) return false;
  if (value.includes('-') && /^[A-Za-z-]+$/.test(value)) return false; // font names / ids
  return latin.test(value) || latinDigits.test(value);
});

if (realOffenders.length) {
  console.error('Persian strings contain Latin characters:');
  realOffenders.forEach((item) => console.error('  -', item));
  process.exit(1);
}

// Also scan screens/components for stray Latin text inside Persian literals.
const dirs = ['mobile/src/screens', 'mobile/src/components'];
let screenOffenders = 0;
dirs.forEach((dir) => {
  const full = path.join(root, dir);
  if (!fs.existsSync(full)) return;
  fs.readdirSync(full).forEach((file) => {
    const content = fs.readFileSync(path.join(full, file), 'utf8');
    const matches = content.match(/'(?:[^'\\]|\\.)*[\u0600-\u06FF](?:[^'\\]|\\.)*'/g) || [];
    matches.forEach((literal) => {
      if (latin.test(literal) || latinDigits.test(literal)) {
        console.error(`  - ${file}: ${literal}`);
        screenOffenders += 1;
      }
    });
  });
});

if (screenOffenders) {
  console.error('Persian literals in UI files contain Latin characters.');
  process.exit(1);
}

console.log(`i18n check passed (${strings.length} Persian strings scanned)`);
