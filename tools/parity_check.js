#!/usr/bin/env node
/**
 * Asserts that the JavaScript engine (used by the app, offline) produces the
 * same numbers as the Python reference engine for a set of fixtures.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const dataset = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'dataset.json'), 'utf8'));
const fixtures = JSON.parse(fs.readFileSync(path.join(root, 'shared', 'engine-fixtures.json'), 'utf8'));
const engine = require(path.join(root, 'mobile', 'src', 'core', 'engine.js'));

const TOLERANCE = 0.25;
let failures = 0;
let checks = 0;

function compare(label, actual, expected) {
  checks += 1;
  if (Math.abs(actual - expected) > TOLERANCE) {
    failures += 1;
    console.log(`  MISMATCH ${label}: js=${actual} py=${expected}`);
  }
}

Object.keys(fixtures).forEach((name) => {
  const fixture = fixtures[name];
  const result = engine.assess(dataset, fixture.profile, (key, fallback) => fallback || key);
  const byCode = {};
  result.countries.forEach((country) => {
    byCode[country.code] = country;
  });
  Object.keys(fixture.countries).forEach((code) => {
    const expected = fixture.countries[code];
    const actual = byCode[code];
    if (!actual) {
      failures += 1;
      console.log(`  MISSING country ${code} in js engine`);
      return;
    }
    compare(`${name}.${code}.best.visaId`, actual.best.visaId === expected.best ? 1 : 0, 1);
    actual.visas.forEach((visa) => {
      const target = expected.visas[visa.visaId];
      if (!target) return;
      compare(`${name}.${code}.${visa.visaId}.chance`, visa.chance, target.chance);
      compare(`${name}.${code}.${visa.visaId}.readiness`, visa.readiness, target.readiness);
      compare(`${name}.${code}.${visa.visaId}.achieved`, visa.achieved, target.achieved);
      const actualBlockers = visa.blockers.map((b) => b.kind).sort().join(',');
      const expectedBlockers = [...target.blockers].sort().join(',');
      checks += 1;
      if (actualBlockers !== expectedBlockers) {
        failures += 1;
        console.log(`  BLOCKERS ${name}.${code}.${visa.visaId}: js=[${actualBlockers}] py=[${expectedBlockers}]`);
      }
    });
  });
});

console.log(`\nparity checks: ${checks}, mismatches: ${failures}`);
process.exit(failures === 0 ? 0 : 1);
