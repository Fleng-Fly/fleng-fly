// English-only i18n stand-in for the vm-based DOM tests (no window/localStorage needed).
import en from '../frontend/js/i18n/en.js';

const fill = (text, params) => text.replace(/\{(\w+)\}/g, (m, k) => (params && k in params ? String(params[k]) : m));
export const i18nStub = {
  t: (key, params) => fill(en[key] ?? key, params),
  tn: (key, count, params) => {
    const form = new Intl.PluralRules('en').select(count);
    return fill(en[`${key}.${form}`] ?? en[`${key}.other`] ?? key, { count, ...params });
  },
  getLang: () => 'en',
  applyDom() {},
  applyUserLanguage: async () => {},
  createLanguageSwitch: () => ({}),
};
