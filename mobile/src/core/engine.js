/**
 * Visayar assessment engine — JavaScript mirror of backend/app/engine/engine.py.
 *
 * The rule semantics are identical and kept in sync by tools/parity_check.js.
 * CommonJS on purpose: Metro and Node both load it without a build step.
 */

const SKILLS = ['listening', 'reading', 'writing', 'speaking'];
const CEFR_TO_CLB = { A1: 2, A2: 4, B1: 6, B2: 8, C1: 9, C2: 10 };

const EFFORT = {
  language: 'medium',
  funds: 'medium',
  education: 'hard',
  experience: 'hard',
  adaptability: 'medium',
  age: 'locked',
};

const GOAL_TYPES = {
  work: ['skilled', 'work', 'talent', 'jobseeker'],
  study: ['study'],
  startup: ['startup', 'business'],
  investment: ['investment'],
  selfsponsored: ['talent', 'digitalnomad', 'jobseeker'],
};

function clbToCefr(clb) {
  if (clb >= 10) return 'C2';
  if (clb >= 9) return 'C1';
  if (clb >= 7) return 'B2';
  if (clb >= 5) return 'B1';
  if (clb >= 3) return 'A2';
  return 'A1';
}

function educationRank(dataset, educationId) {
  const level = dataset.educationLevels.find((item) => item.id === educationId);
  return level ? level.rank : 1;
}

function testMeta(dataset, testId) {
  return dataset.languageTests.find((test) => test.id === testId) || null;
}

function bandToClb(thresholds, value) {
  let result = 0;
  thresholds.forEach(([floor, clb]) => {
    if (value >= floor) result = clb;
  });
  return result;
}

function normaliseLanguage(dataset, result) {
  const meta = testMeta(dataset, result.testId);
  if (!meta) return null;
  const group = meta.group;
  const skills = {};
  let clb;
  if (meta.kind === 'cefr') {
    const value = CEFR_TO_CLB[result.cefr];
    if (!value) return null;
    clb = value;
    SKILLS.forEach((skill) => {
      skills[skill] = clb;
    });
  } else if (meta.overallOnly) {
    const raw = result.skills && result.skills.overall;
    if (raw === undefined || raw === null) return null;
    clb = bandToClb(meta.thresholds.overall, raw);
    SKILLS.forEach((skill) => {
      skills[skill] = clb;
    });
  } else {
    for (const skill of SKILLS) {
      const raw = result.skills && result.skills[skill];
      if (raw === undefined || raw === null) return null;
      skills[skill] = bandToClb(meta.thresholds[skill], raw);
    }
    clb = Math.min(...SKILLS.map((skill) => skills[skill]));
  }
  const minClb = Math.min(...SKILLS.map((skill) => skills[skill]));
  return { group, testId: result.testId, skills, clb, minClb, cefr: clbToCefr(clb) };
}

function resolveLanguage(dataset, profile, group) {
  const candidates = (profile.languages || [])
    .map((entry) => normaliseLanguage(dataset, entry))
    .filter((entry) => entry && entry.group === group);
  if (!candidates.length) return null;
  return candidates.sort((a, b) => b.minClb - a.minClb || b.clb - a.clb)[0];
}

function fxRate(dataset, currency) {
  const entry = dataset.fx[currency];
  return entry ? entry.rate : 1;
}

function toUsd(dataset, amount, currency) {
  if (amount === null || amount === undefined) return 0;
  return amount * fxRate(dataset, currency);
}

function occupation(dataset, code) {
  if (!code) return null;
  return dataset.occupations.find((item) => item.noc === code) || null;
}

function buildFlags(dataset, profile, countryCode) {
  const occ = occupation(dataset, profile.work.occupationCode);
  const adaptability = profile.adaptability || {};
  const spouse = profile.spouse || {};
  return {
    jobOffer: !!profile.work.jobOffer,
    studyOffer: !!profile.studyOffer,
    startupBacking: !!profile.startupBacking,
    achievement: !!profile.achievement,
    nomination: !!profile.nomination,
    licensing: !!profile.work.licensing,
    inDemandOccupation: !!(occ && occ.inDemand.includes(countryCode)),
    educationStem: !!profile.educationStem || !!(occ && occ.stem),
    relativeInCountry: !!adaptability.relativeInCountry,
    priorStudyInCountry: !!adaptability.priorStudyInCountry,
    priorWorkInCountry: !!adaptability.priorWorkInCountry,
    spouseLanguage: !!(spouse.languageClb >= 4),
    eca: !!adaptability.eca,
    recentGraduateTop: !!profile.recentGraduate,
  };
}

function annualSalaryUsd(dataset, profile) {
  return toUsd(dataset, profile.work.salaryAnnualLocal, profile.work.salaryCurrency || 'USD');
}

function withinBand(bands, value) {
  const ordered = [...bands].sort((a, b) => b[0] - a[0]);
  for (const [floor, score] of ordered) {
    if (value >= floor) return Number(score);
  }
  return 0;
}

function evaluateRule(dataset, rule, profile, flags, salaryUsd, settlementUsdValue) {
  switch (rule.kind) {
    case 'age_band': {
      const band = rule.bands.find(([low, high]) => profile.age >= low && profile.age <= high);
      return band ? Number(band[2]) : 0;
    }
    case 'education_rank': {
      const rank = educationRank(dataset, profile.educationId);
      let best = 0;
      Object.keys(rule.map).forEach((educationId) => {
        if (educationRank(dataset, educationId) === rank) best = Number(rule.map[educationId]);
      });
      return best;
    }
    case 'language_skills': {
      const lang = resolveLanguage(dataset, profile, rule.group);
      if (!lang) return 0;
      let total = 0;
      SKILLS.forEach((skill) => {
        total += withinBand(rule.bands, lang.skills[skill] || 0);
      });
      return rule.cap ? Math.min(total, rule.cap) : total;
    }
    case 'language_best': {
      const lang = resolveLanguage(dataset, profile, rule.group);
      if (!lang) return 0;
      return withinBand(rule.bands, lang.minClb);
    }
    case 'experience_band': {
      const scope = rule.scope || 'any';
      const years = scope === 'overseas'
        ? profile.work.overseasYears || 0
        : scope === 'inCountry' ? profile.work.inCountryYears || 0 : profile.work.totalYears || 0;
      const occ = occupation(dataset, profile.work.occupationCode);
      if (rule.teer && occ && !rule.teer.includes(occ.teer)) return 0;
      return withinBand(rule.bands, years);
    }
    case 'flag':
      return flags[rule.key] ? Number(rule.points) : 0;
    case 'salary_band':
      return withinBand(rule.bands, rule.metric === 'annualSalaryUsd' ? salaryUsd : 0);
    case 'numeric_band': {
      const value = rule.metric === 'investmentUsd'
        ? profile.investmentUsd || 0
        : rule.metric === 'remoteIncomeUsd' ? profile.remoteIncomeUsd || 0 : 0;
      return withinBand(rule.bands, value);
    }
    case 'funds_ratio': {
      const points = Number(rule.points || 0);
      if (settlementUsdValue <= 0) return points;
      const ratio = (profile.funds.availableUsd || 0) / settlementUsdValue;
      return Math.min(points, points * Math.max(0, Math.min(1, ratio / (rule.scale || 1))));
    }
    case 'adaptability': {
      let total = 0;
      rule.factors.forEach((factor) => {
        if (flags[factor]) total += Number(rule.each);
      });
      return rule.cap ? Math.min(total, rule.cap) : total;
    }
    case 'spouse': {
      if (!profile.spouse) return 0;
      const parts = rule.parts;
      let total = 0;
      if (parts.language) total += withinBand(parts.language, profile.spouse.languageClb || 0);
      if (parts.education) total += withinBand(parts.education, educationRank(dataset, profile.spouse.educationId));
      if (parts.work) total += withinBand(parts.work, profile.spouse.workYears || 0);
      return rule.cap ? Math.min(total, rule.cap) : total;
    }
    default:
      return 0;
  }
}

function settlementUsd(dataset, visa, familySize) {
  const table = visa.settlement;
  if (!table) return 0;
  const amounts = table.byFamilySize;
  const index = Math.max(0, Math.min(amounts.length - 1, (familySize || 1) - 1));
  return toUsd(dataset, amounts[index], table.currency);
}

function chancenkartePoints(dataset, profile, flags) {
  let points = 0;
  const rank = educationRank(dataset, profile.educationId);
  if (rank >= 4) points += 4;
  else if (rank >= 2) points += 2;
  const de = resolveLanguage(dataset, profile, 'de');
  if (de) points += de.minClb >= 8 ? 3 : de.minClb >= 6 ? 2 : 1;
  if ((profile.work.totalYears || 0) >= 5) points += 3;
  else if ((profile.work.totalYears || 0) >= 2) points += 2;
  if (profile.age < 35) points += 2;
  else if (profile.age < 40) points += 1;
  if (flags.inDemandOccupation) points += 1;
  return points;
}

function nzPoints(dataset, profile, flags, salaryUsd) {
  const rank = educationRank(dataset, profile.educationId);
  let points = 0;
  if (rank >= 6) points += 6;
  else if (rank >= 5) points += 5;
  else if (rank >= 4) points += 4;
  else if (rank >= 2) points += 3;
  if (salaryUsd >= 120000) points += 6;
  else if (salaryUsd >= 90000) points += 5;
  else if (salaryUsd >= 65000) points += 3;
  if (flags.inDemandOccupation) points += 1;
  if ((profile.work.totalYears || 0) >= 5) points += 1;
  return points;
}

function salaryGatePasses(dataset, rule, profile, salaryUsd, flags) {
  if (profile.work.salaryAnnualLocal === null || profile.work.salaryAnnualLocal === undefined) return false;
  let required = Number(rule.minAmount);
  if (rule.under30Min && profile.age < 30) required = Math.min(required, Number(rule.under30Min));
  if (rule.reducedMin && (flags.inDemandOccupation || profile.age <= 30)) required = Math.min(required, Number(rule.reducedMin));
  if (rule.shortageMin && flags.inDemandOccupation) required = Math.min(required, Number(rule.shortageMin));
  if (rule.newEntrantMin && profile.age < 26) required = Math.min(required, Number(rule.newEntrantMin));
  const requiredUsd = toUsd(dataset, required, rule.currency);
  if (rule.monthly) return salaryUsd / 12 >= requiredUsd;
  if (rule.hourly) return salaryUsd / 2080 >= requiredUsd;
  return salaryUsd >= requiredUsd;
}

function evaluateGates(dataset, visa, profile, flags, totalPoints, salaryUsd, settlement, t) {
  const results = [];
  for (const rule of visa.gates) {
    const advisory = !!rule.advisory;
    let passed = true;
    let messageFa = rule.failFa || '';
    let messageEn = rule.failEn || '';
    switch (rule.kind) {
      case 'age_gate':
        passed = profile.age <= rule.max;
        break;
      case 'language_gate': {
        const lang = resolveLanguage(dataset, profile, rule.group);
        passed = !!(lang && lang.minClb >= rule.minClb);
        break;
      }
      case 'experience_gate': {
        if ((profile.work.totalYears || 0) < (rule.minYears || 0)) passed = false;
        if (rule.teer) {
          const occ = occupation(dataset, profile.work.occupationCode);
          if (occ && !rule.teer.includes(occ.teer)) passed = false;
        }
        break;
      }
      case 'points_gate':
        passed = rule.scale ? totalPoints / rule.scale >= rule.min : totalPoints >= rule.min;
        break;
      case 'funds_gate':
        if (settlement > 0) passed = (profile.funds.availableUsd || 0) >= settlement;
        if (!passed && !(profile.funds.availableUsd > 0)) {
          messageFa = t('gate.noFunds');
          messageEn = 'Settlement funds have not been entered.';
        }
        break;
      case 'education_gate': {
        passed = educationRank(dataset, profile.educationId) >= (rule.minRank || 1);
        if (!passed && rule.allowItExperience && (profile.work.totalYears || 0) >= 3) passed = true;
        break;
      }
      case 'flag_gate':
        passed = !!flags[rule.key];
        break;
      case 'salary_gate':
        passed = salaryGatePasses(dataset, rule, profile, salaryUsd, flags);
        if (profile.work.salaryAnnualLocal === null || profile.work.salaryAnnualLocal === undefined) {
          messageFa = t('gate.noSalary');
          messageEn = 'Enter the offered salary to evaluate this condition.';
        }
        break;
      case 'investment_gate':
        passed = (profile.investmentUsd || 0) >= toUsd(dataset, rule.minAmount, rule.currency);
        break;
      case 'remote_income_gate':
        passed = (profile.remoteIncomeUsd || 0) >= rule.minMonthlyUsd;
        break;
      case 'custom_points':
        if (rule.grid === 'chancenkarte') passed = chancenkartePoints(dataset, profile, flags) >= rule.min;
        else if (rule.grid === 'nz_smc') passed = nzPoints(dataset, profile, flags, salaryUsd) >= rule.min;
        break;
      default:
        passed = true;
    }
    if (passed) continue;
    results.push({ kind: rule.kind, advisory, messageFa, messageEn });
  }
  return results;
}

const BANDS = [
  { chance: 85, fa: 'بسیار قوی', en: 'Very strong' },
  { chance: 70, fa: 'قوی', en: 'Strong' },
  { chance: 55, fa: 'متوسط', en: 'Moderate' },
  { chance: 35, fa: 'ضعیف', en: 'Weak' },
  { chance: 0, fa: 'بسیار ضعیف', en: 'Very weak' },
];

function bandLabel(chance, lang) {
  const found = BANDS.find((band) => chance >= band.chance);
  return found ? found[lang] : BANDS[BANDS.length - 1][lang];
}

function scoreVisa(dataset, country, visa, profile, t) {
  const translate = t || ((key, fallback) => fallback || key);
  const flags = buildFlags(dataset, profile, country.code);
  const salaryUsd = annualSalaryUsd(dataset, profile);
  const settlement = settlementUsd(dataset, visa, profile.familySize);

  const criteria = [];
  let achieved = 0;
  let maxPoints = 0;
  const categories = {};
  visa.criteria.forEach((crit) => {
    const raw = evaluateRule(dataset, crit.rule, profile, flags, salaryUsd, settlement);
    const points = Math.max(0, Math.round(Math.min(raw, crit.max) * 100) / 100);
    achieved += points;
    maxPoints += crit.max;
    const bucket = categories[crit.category] || { achieved: 0, max: 0 };
    bucket.achieved += points;
    bucket.max += crit.max;
    categories[crit.category] = bucket;
    criteria.push({
      id: crit.id,
      labelFa: crit.labelFa,
      labelEn: crit.labelEn,
      category: crit.category,
      max: crit.max,
      score: points,
      actionFa: crit.actionFa,
      actionEn: crit.actionEn,
      noteFa: crit.noteFa,
      noteEn: crit.noteEn,
    });
  });

  achieved = Math.round(achieved * 10) / 10;
  maxPoints = Math.round(maxPoints * 10) / 10;
  const ratio = maxPoints ? achieved / maxPoints : 0;
  const gates = evaluateGates(dataset, visa, profile, flags, achieved, salaryUsd, settlement, translate);
  const blockers = gates.filter((gate) => !gate.advisory);
  const warnings = gates.filter((gate) => gate.advisory);
  const passOk = achieved >= visa.passMark;

  let chance;
  if (blockers.length) {
    chance = 5 + 26 * ratio * Math.max(0.35, 1 - 0.12 * Math.min(blockers.length, 4));
  } else {
    chance = ratio * 100 * (0.62 + 0.38 * visa.selectivity);
    if (!passOk) chance *= 0.72;
  }
  chance = Math.round(Math.max(3, Math.min(96, chance)) * 10) / 10;

  const radar = {};
  Object.keys(categories).forEach((key) => {
    const bucket = categories[key];
    radar[key] = {
      achieved: Math.round(bucket.achieved * 10) / 10,
      max: bucket.max,
      percent: bucket.max ? Math.round((100 * bucket.achieved) / bucket.max * 10) / 10 : 0,
    };
  });

  return {
    visaId: visa.id,
    countryCode: country.code,
    visaNameFa: visa.nameFa,
    visaNameEn: visa.nameEn,
    visaType: visa.type,
    taglineFa: visa.taglineFa,
    taglineEn: visa.taglineEn,
    achieved,
    maxPoints,
    passMark: visa.passMark,
    readiness: Math.round(ratio * 1000) / 10,
    chance,
    bandFa: bandLabel(chance, 'fa'),
    bandEn: bandLabel(chance, 'en'),
    blockers,
    warnings,
    eligible: blockers.length === 0,
    criteria,
    radar,
    settlementRequiredUsd: Math.round(settlement),
    fees: visa.fees,
    processingTimeFa: visa.processingTimeFa,
    processingTimeEn: visa.processingTimeEn,
    officialUrl: visa.officialUrl,
  };
}

function roadmap(scoredVisa, limit) {
  const max = limit || 6;
  const items = [];
  scoredVisa.criteria.forEach((crit) => {
    const gap = Math.round((crit.max - crit.score) * 10) / 10;
    if (gap < 1) return;
    items.push({
      id: crit.id,
      labelFa: crit.labelFa,
      labelEn: crit.labelEn,
      gain: gap,
      actionFa: crit.actionFa,
      actionEn: crit.actionEn,
      effort: EFFORT[crit.category] || 'medium',
      priority: 2,
    });
  });
  scoredVisa.blockers.forEach((blocker) => {
    items.push({
      id: blocker.kind,
      labelFa: 'شرط ورودی مسیر',
      labelEn: 'Route eligibility condition',
      gain: 0,
      actionFa: blocker.messageFa,
      actionEn: blocker.messageEn,
      effort: 'hard',
      priority: 1,
    });
  });
  items.sort((a, b) => a.priority - b.priority || b.gain - a.gain);
  return items.slice(0, max);
}

function assess(dataset, profile, t) {
  const options = profile || {};
  const countries = dataset.countries.map((country) => {
    const results = country.visas
      .map((visa) => scoreVisa(dataset, country, visa, options, t))
      .sort((a, b) => Number(b.eligible) - Number(a.eligible) || b.chance - a.chance || b.readiness - a.readiness);
    const best = results[0];
    return {
      code: country.code,
      nameFa: country.nameFa,
      nameEn: country.nameEn,
      flag: country.flag,
      region: country.region,
      summaryFa: country.summaryFa,
      summaryEn: country.summaryEn,
      lastVerified: country.official.lastVerified,
      portal: country.official.portal,
      authorityFa: country.official.authorityFa,
      authorityEn: country.official.authorityEn,
      prPathFa: country.prPathFa,
      prPathEn: country.prPathEn,
      best,
      goalMatch: (GOAL_TYPES[profile.goal] || []).includes(best.visaType),
      visas: results,
      radar: best.radar,
      roadmap: roadmap(best),
    };
  });
  countries.sort((a, b) => Number(b.best.eligible) - Number(a.best.eligible)
    || Number(b.goalMatch) - Number(a.goalMatch)
    || b.best.chance - a.best.chance);
  const eligibleCountries = countries.filter((country) => country.best.eligible).length;
  return {
    datasetVersion: dataset.meta.version,
    lastVerified: dataset.meta.lastVerified,
    summary: {
      countries: countries.length,
      eligibleCountries,
      bestCountry: countries.length ? countries[0].code : null,
    },
    countries,
    topRoadmap: countries.length ? countries[0].roadmap : [],
    recommendations: recommend(countries),
  };
}

function recommend(countries) {
  return countries.slice(0, 3).map((country) => ({
    code: country.code,
    nameFa: country.nameFa,
    nameEn: country.nameEn,
    flag: country.flag,
    visaId: country.best.visaId,
    visaNameFa: country.best.visaNameFa,
    visaNameEn: country.best.visaNameEn,
    chance: country.best.chance,
    reasonFa: country.best.blockers.length
      ? `نزدیک‌ترین مسیر با ${country.best.readiness}٪ آمادگی؛ پیش از اقدام باید شرط ورودی برطرف شود.`
      : `با ${country.best.readiness}٪ آمادگی پرونده و شانس تخمینی ${country.best.chance}٪، این مسیر آماده اقدام است.`,
    reasonEn: country.best.blockers.length
      ? `The closest route at ${country.best.readiness}% readiness; eligibility must be resolved before filing.`
      : `At ${country.best.readiness}% profile readiness and an estimated ${country.best.chance}% chance, this route is ready to pursue.`,
  }));
}

function visaCosts(dataset, visa, familySize, currency) {
  let applicantTotal = 0;
  let employerTotal = 0;
  const lines = visa.fees.map((item) => {
    let count = 1;
    const label = (item.labelEn || '').toLowerCase();
    if (label.includes('spouse') || label.includes('adult')) count = Math.max(1, familySize || 1);
    else if (label.includes('child')) count = 0;
    const usd = toUsd(dataset, item.amount, item.currency) * count;
    if (item.payer === 'employer') employerTotal += usd;
    else applicantTotal += usd;
    return { ...item, count, usd: Math.round(usd) };
  });
  const settlement = settlementUsd(dataset, visa, familySize);
  const rate = fxRate(dataset, currency || 'USD');
  return {
    lines,
    applicantTotalUsd: Math.round(applicantTotal),
    employerTotalUsd: Math.round(employerTotal),
    settlementUsd: Math.round(settlement),
    grandTotalUsd: Math.round(applicantTotal + settlement),
    displayTotal: Math.round((applicantTotal + settlement) / rate),
  };
}

function emptyProfile() {
  return {
    goal: 'work',
    age: 30,
    maritalStatus: 'single',
    spouse: { educationId: 'bachelor', languageClb: 0, workYears: 0 },
    educationId: 'bachelor',
    educationStem: false,
    languages: [],
    work: {
      totalYears: 0,
      overseasYears: 0,
      inCountryYears: 0,
      occupationCode: null,
      jobOffer: false,
      salaryAnnualLocal: null,
      salaryCurrency: 'USD',
      licensing: false,
      selfEmployedYears: 0,
    },
    funds: { availableUsd: 0, cashUsd: 0, assetsUsd: 0 },
    adaptability: { relativeInCountry: false, priorStudyInCountry: false, priorWorkInCountry: false, eca: false },
    familySize: 1,
    investmentUsd: 0,
    remoteIncomeUsd: 0,
    startupBacking: false,
    studyOffer: false,
    achievement: false,
    nomination: false,
    recentGraduate: false,
  };
}

module.exports = {
  SKILLS,
  assess,
  roadmap,
  scoreVisa,
  settlementUsd,
  visaCosts,
  buildFlags,
  resolveLanguage,
  normaliseLanguage,
  educationRank,
  emptyProfile,
  GOAL_TYPES,
};
