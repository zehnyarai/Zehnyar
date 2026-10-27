const expo = require('./app.json').expo;
const apiBaseUrl = String(process.env.VISAYAR_API_BASE_URL || expo.extra.apiBaseUrl || '').trim().replace(/\/$/, '');

module.exports = {
  ...expo,
  extra: {
    ...expo.extra,
    apiBaseUrl,
  },
};
