import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { getDataset, subscribeDataset } from './data';
import engine from './engine';
import { clearAll, loadProfile, saveProfile, saveResult } from './storage';
import { consumeAssessmentCredit } from './paymentApi';

const AppStateContext = createContext(null);

export function AppStateProvider({ children, initialProfile, initialResult }) {
  const [profile, setProfileState] = useState(() => ({ ...engine.emptyProfile(), ...(initialProfile || {}) }));
  const [result, setResult] = useState(initialResult || null);
  const [hydrated, setHydrated] = useState(!!initialProfile);
  const [dataRevision, setDataRevision] = useState(0);
  const saveTimer = useRef(null);

  useEffect(() => subscribeDataset(() => setDataRevision((revision) => revision + 1)), []);

  useEffect(() => {
    if (initialProfile) return undefined;
    let mounted = true;
    loadProfile().then((stored) => {
      if (!mounted) return;
      if (stored) setProfileState({ ...engine.emptyProfile(), ...stored });
      setHydrated(true);
    });
    return () => {
      mounted = false;
    };
  }, [initialProfile]);

  const persist = useCallback((next) => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => saveProfile(next), 350);
  }, []);

  const setProfile = useCallback((updater) => {
    setProfileState((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      persist(next);
      return next;
    });
  }, [persist]);

  const updateProfile = useCallback((patch) => {
    setProfile((current) => ({ ...current, ...patch }));
  }, [setProfile]);

  const updateNested = useCallback((key, patch) => {
    setProfile((current) => ({ ...current, [key]: { ...current[key], ...patch } }));
  }, [setProfile]);


  const compute = useCallback(async (t) => {
    const allowance = await consumeAssessmentCredit();
    if (!allowance) return false;
    const next = engine.assess(getDataset(), profile, t);
    setResult(next);
    saveResult(next);
    return next;
  }, [profile]);

  const resetAll = useCallback(async () => {
    await clearAll();
    setProfileState(engine.emptyProfile());
    setResult(null);
  }, []);

  const value = useMemo(() => ({
    profile,
    setProfile,
    updateProfile,
    updateNested,
    result,
    setResult,
    compute,
    resetAll,
    hydrated,
    hasAssessment: !!result,
    dataRevision,
  }), [profile, setProfile, updateProfile, updateNested, result, compute, resetAll, hydrated, dataRevision]);

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) throw new Error('useAppState must be used inside AppStateProvider');
  return context;
}

export default AppStateProvider;
