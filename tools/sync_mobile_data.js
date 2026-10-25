#!/usr/bin/env node
/**
 * Copies the generated dataset into the mobile bundle so Metro resolves it
 * locally and the app ships with an offline copy of the reference data.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const source = path.join(root, 'shared', 'dataset.json');
const targetDir = path.join(root, 'mobile', 'src', 'data');
const target = path.join(targetDir, 'dataset.json');

if (!fs.existsSync(source)) {
  console.error('shared/dataset.json is missing. Run: python3 tools/build_dataset.py');
  process.exit(1);
}
fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(source, target);
const size = (fs.statSync(target).size / 1024).toFixed(0);
console.log(`dataset synced -> mobile/src/data/dataset.json (${size} KB)`);
