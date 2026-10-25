import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { dictionary } from './dictionary';
import { loadLanguage, saveLanguage } from '../core/storage';

const I18nContext = createContext(null);

function resolve(source, path) {
  return path.split('.').reduce((node, key) => (node && node[key] !== undefined ? node[key] : undefined), source);
}

export function I18nProvider({ children, initialLang = 'fa' }) {
  const [lang, setLang] = useState(initialLang);

  useEffect(() => {
    let mounted = true;
    loadLanguage().then((stored) => {
      if (mounted && stored) setLang(stored);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const changeLanguage = useCallback((next) => {
    setLang(next);
    saveLanguage(next);
  }, []);

  const value = useMemo(() => {
    const other = lang === 'fa' ? 'en' : 'fa';
    const t = (path, fallback) => {
      const hit = resolve(dictionary[lang], path);
      if (hit !== undefined) return hit;
      const backup = resolve(dictionary[other], path);
      if (backup !== undefined) return backup;
      return fallback !== undefined ? fallback : path;
    };
    return {
      lang,
      isRtl: lang === 'fa',
      dir: lang === 'fa' ? 'rtl' : 'ltr',
      setLanguage: changeLanguage,
      toggleLanguage: () => changeLanguage(other),
      t,
      pick: (fa, en) => (lang === 'fa' ? fa : en),
    };
  }, [lang, changeLanguage]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error('useI18n must be used inside I18nProvider');
  return context;
}

export function useDirection() {
  const { isRtl } = useI18n();
  return useMemo(() => ({
    isRtl,
    row: isRtl ? 'row-reverse' : 'row',
    rowRev: isRtl ? 'row' : 'row-reverse',
    text: isRtl ? 'right' : 'left',
    textOpposite: isRtl ? 'left' : 'right',
    align: isRtl ? 'flex-end' : 'flex-start',
    alignEnd: isRtl ? 'flex-start' : 'flex-end',
    writing: isRtl ? 'rtl' : 'ltr',
  }), [isRtl]);
}

export default I18nProvider;
