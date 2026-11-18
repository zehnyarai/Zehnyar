// Lightweight check: node tools/test_conditional_fees.js
const assert = require('assert');
const dataset = require('../shared/dataset.json');
const engine = require('../mobile/src/core/engine');
for (const id of ['fr_talent', 'fr_business']) {
  const visa = dataset.countries.flatMap(c => c.visas).find(v => v.id === id);
  const result = engine.visaCosts(dataset, visa, 1, 'USD');
  const conditional = result.lines.find(l => l.includeInTotal === false);
  const without = engine.visaCosts(dataset, {...visa, fees: visa.fees.filter(f => f.includeInTotal !== false)}, 1, 'USD');
  assert(conditional && conditional.usd > 0, `${id}: conditional fee should remain visible`);
  assert.strictEqual(result.applicantTotalUsd, without.applicantTotalUsd, `${id}: conditional fee must not be summed`);
  assert.strictEqual(result.grandTotalUsd, without.grandTotalUsd);
  const included = engine.visaCosts(dataset, {...visa, fees: visa.fees.map(f => ({...f, includeInTotal: true}))}, 1, 'USD');
  assert(included.applicantTotalUsd > result.applicantTotalUsd);
}
console.log('OK: conditional France fees remain visible but excluded from mobile totals');
for (const id of ['au_189', 'au_190', 'au_491', 'se_work', 'uk_skilled_worker', 'uk_global_talent', 'uk_student', 'uk_innovator', 'uk_hpi']) {
  const visa = dataset.countries.flatMap(c => c.visas).find(v => v.id === id);
  for (const size of [1, 4]) {
    const costs = engine.visaCosts(dataset, visa, size, 'USD');
    assert(costs.lines.some(f => f.includeInTotal === false && f.usd > 0), id);
    const includedOnly = engine.visaCosts(dataset, {...visa, fees: visa.fees.filter(f => f.includeInTotal !== false)}, size, 'USD');
    assert.strictEqual(costs.applicantTotalUsd, includedOnly.applicantTotalUsd, id);
  }
}
for (const id of ['fi_student', 'se_study', 'se_work']) {
  const visa = dataset.countries.flatMap(c => c.visas).find(v => v.id === id);
  assert.strictEqual(engine.visaCosts(dataset, visa, 1, 'USD').applicantTotalUsd, engine.visaCosts(dataset, visa, 4, 'USD').applicantTotalUsd, `${id}: adult is not whole family`);
}
console.log('OK: dependant fees and annual IHS are reference-only; adult is not multiplied by total family size');
