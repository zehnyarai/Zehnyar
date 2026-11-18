// Lightweight regression check: node tools/test_manual_review.js
const assert = require('assert');
const dataset = require('../shared/dataset.json');
const bundled = require('../mobile/src/data/dataset.json');
const engine = require('../mobile/src/core/engine');
assert.deepStrictEqual(dataset, bundled, 'Mobile dataset must match the shared dataset');
let checked = 0;
for (const country of dataset.countries) {
  for (const visa of country.visas) {
    if (!visa.gates.some((gate) => gate.kind === 'manual_review')) continue;
    const result = engine.scoreVisa(dataset, country, visa, engine.emptyProfile());
    assert(!result.eligible, `${visa.id}: manual review must prevent a green eligible result`);
    assert(result.blockers.some((blocker) => blocker.kind === 'manual_review'), visa.id);
    checked++;
  }
}
assert.strictEqual(checked, 99);
const canada = dataset.countries.find((country) => country.code === 'CA');
const startup = canada.visas.find((visa) => visa.id === 'ca_suv');
assert(engine.scoreVisa(dataset, canada, startup, engine.emptyProfile()).blockers.some((b) => b.kind === 'program_closed'));
console.log(`OK: ${checked} routes require manual review; closed program is blocked`);
for (const id of ['au_189', 'au_190', 'au_491']) {
  const visa = dataset.countries.flatMap(c => c.visas).find(v => v.id === id);
  assert(!visa.gates.some(g => g.kind === 'age_gate'), `${id}: current age cannot establish age at invitation`);
  assert(visa.gates.some(g => g.kind === 'manual_review'));
}
console.log('OK: Australian skilled routes require invitation-age review');
const ptNomad = dataset.countries.flatMap(c => c.visas).find(v => v.id === 'pt_digital_nomad');
assert(!ptNomad.gates.some(g => g.kind === 'remote_income_gate'), 'A fixed USD value cannot verify Portuguese 3-month EUR average');
assert(ptNomad.gates.some(g => g.kind === 'manual_review'));
console.log('OK: Portugal remote income needs individual review');

const dkPay = dataset.countries.flatMap(c => c.visas).find(v => v.id === "dk_pay_limit");
assert(!dkPay.gates.some(g => g.kind === "salary_gate"), "A fixed salary gate cannot cover every extension or exception");
assert(dkPay.gates.some(g => g.kind === "manual_review"));
console.log("OK: Danish pay threshold needs individual review");

for (const id of ["de_blue_card", "de_chancenkarte", "de_job_seeker", "de_student", "de_self_employed"]) {
 const route = dataset.countries.flatMap(c => c.visas).find(v => v.id === id);
 assert(route && route.gates.some(g => g.kind === "manual_review"), `${id}: needs manual review`);
}
console.log("OK: all five existing German routes need individual review");

const fsw = dataset.countries.flatMap(c => c.visas).find(v => v.id === "ca_ee_fsw");
assert(!fsw.gates.some(g => g.kind === "experience_gate"), "FSW hours and continuity require individual review");
for (const visa of dataset.countries.flatMap(c => c.visas).filter(v => v.id.startsWith("ca_"))) {
 const bio = visa.fees.find(f => f.labelEn.startsWith("Biometrics"));
 assert(bio && bio.includeInTotal === false, `${visa.id}: biometrics is conditional`);
}
console.log("OK: Canadian biometrics is conditional and FSW experience needs review");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(fr_|pt_|es_)/.test(v.id))) {
 assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: needs individual review`);
 if (v.id.startsWith("pt_")) assert(v.fees[0].includeInTotal === false, `${v.id}: visa fee exemptions apply`);
}
console.log("OK: selected French, Portuguese and Spanish routes need individual review");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(au_|uk_|nz_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: needs individual review`);
const investor = dataset.countries.flatMap(c => c.visas).find(v => v.id === "nz_investor");
assert(!investor.gates.some(g => g.kind === "investment_gate"), "Fixed FX cannot establish investor NZD amount");
const hpi = dataset.countries.flatMap(c => c.visas).find(v => v.id === "uk_hpi");
assert(hpi.fees.find(f => f.labelEn.startsWith("Ecctis")).includeInTotal === false);
console.log("OK: Australia, UK and NZ routes require manual review; investor and HPI safeguards");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(nl_|ie_|dk_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires case review`);
const dkList = dataset.countries.flatMap(c => c.visas).find(v => v.id === "dk_positive_list");
assert(!dkList.gates.some(g => g.key === "inDemandOccupation"), "Current list membership cannot determine all extensions");
for (const id of ["ie_critical_skills", "ie_general_employment", "ie_student", "nl_startup"]) { const r = dataset.countries.flatMap(c => c.visas).find(v => v.id === id); assert(r.fees[0].includeInTotal === false); }
console.log("OK: NL, Ireland, Denmark route safeguards and conditional fees");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(be_|fi_|se_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires individual review`);
for (const id of ["fi_specialist", "fi_employed_person"]) { const r = dataset.countries.flatMap(c => c.visas).find(v => v.id === id); assert(!r.gates.some(g => g.kind === "salary_gate")); }
const seWork = dataset.countries.flatMap(c => c.visas).find(v => v.id === "se_work");
assert.strictEqual(seWork.fees[1].amount, 750);
console.log("OK: Belgium, Finland and Sweden safeguards; Swedish child fee");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(it_|sg_|jp_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires individual review`);
for (const id of ["sg_employment_pass", "sg_s_pass"]) assert(!dataset.countries.flatMap(c => c.visas).find(v => v.id === id).gates.some(g => g.kind === "salary_gate"));
assert(!dataset.countries.flatMap(c => c.visas).find(v => v.id === "it_blue_card").gates.some(g => g.kind === "flag_gate"));
console.log("OK: Italy, Singapore and Japan safeguards");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(us_|ae_|kr_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires individual review`);
for (const v of dataset.countries.flatMap(c => c.visas).filter(v => v.id.startsWith("us_"))) assert(v.notesEn.some(n => n.includes("Proclamation 10998")), `${v.id}: nationality restrictions warning required`);
console.log("OK: US, UAE and South Korea safeguards; US entry restrictions");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(my_|tr_|cn_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires individual review`);
assert(dataset.countries.flatMap(c => c.visas).find(v => v.id === "my_student_pass").requirementsEn.some(s => s.includes("seven working days")));
assert(dataset.countries.flatMap(c => c.visas).find(v => v.id === "cn_q1_reunion").requirementsEn.some(s => s.includes("foster-care")));
console.log("OK: Malaysia, Türkiye and China safeguards");

for (const v of dataset.countries.flatMap(c => c.visas).filter(v => /^(qa_|om_)/.test(v.id))) assert(v.gates.some(g => g.kind === "manual_review"), `${v.id}: requires individual review`);
assert(!dataset.countries.flatMap(c => c.visas).find(v => v.id === "qa_executive_residency").gates.some(g => g.kind === "flag_gate"));
console.log("OK: all Qatar and Oman routes require individual review");
