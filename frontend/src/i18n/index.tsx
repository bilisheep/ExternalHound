import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { translations } from './translations';

export type Locale = keyof typeof translations;
export type TFunction = (key: string, vars?: Record<string, string | number>) => string;

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: TFunction;
}

const STORAGE_KEY = 'externalhound-locale';

const getInitialLocale = (): Locale => {
  if (typeof window === 'undefined') {
    return 'zh';
  }
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'zh') {
    return stored;
  }
  return 'zh';
};

const interpolate = (template: string, vars?: Record<string, string | number>) =>
  template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    const value = vars?.[key];
    return value === undefined || value === null ? '' : String(value);
  });

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  const setLocale = useCallback((nextLocale: Locale) => {
    setLocaleState(nextLocale);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, nextLocale);
    }
  }, []);

  const t = useCallback<TFunction>(
    (key, vars) => {
      const current = translations[locale] as Record<string, string>;
      const fallback = translations.en as Record<string, string>;
      const template = current[key] ?? fallback[key] ?? key;
      return interpolate(template, vars);
    },
    [locale]
  );

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
};
