import dataset from '../data/dataset.json';

export { dataset };

export const countries = dataset.countries;
export const occupations = dataset.occupations;
export const languageTests = dataset.languageTests;
export const educationLevels = dataset.educationLevels;
export const meta = dataset.meta;

export function findCountry(code) {
  return countries.find((country) => country.code === code) || null;
}

export function findVisa(visaId) {
  for (const country of countries) {
    const visa = country.visas.find((item) => item.id === visaId);
    if (visa) return { country, visa };
  }
  return null;
}

export function findOccupation(code) {
  return occupations.find((item) => item.noc === code) || null;
}

export function visaTypeLabelKey(type) {
  return `visaTypes.${type}`;
}

export const allVisaTypes = Array.from(new Set(countries.flatMap((country) => country.visas.map((visa) => visa.type))));

export const totals = {
  countries: countries.length,
  visas: countries.reduce((sum, country) => sum + country.visas.length, 0),
  occupations: occupations.length,
};
