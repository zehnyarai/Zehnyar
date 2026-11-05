import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import {
  getDataset,
  getDatasetSyncStatus,
  subscribeDataset,
  subscribeDatasetSync,
  syncDataset,
} from './data';
import engine from './engine';
import { isBazaarIabBuild } from './bazaarBilling';
import { clearAll, loadPrivacyConsent, loadProfile, loadResult, profileFingerprint, savePrivacyConsent, saveProfile, saveResult } from './storage';
import { consumeAssessmentCredit } from './paymentApi';

const AppStateContext = createContext(null);

export function AppStateProvider({ children, initialProfile, initialResult, initialPrivacyConsent = false }) {
  const [profile, setProfileState] = useState(() => ({ ...engine.emptyProfile(), ...(initialProfile || {}) }));
  const [result, setResult] = useState(initialResult || null);
  const [privacyConsent, setPrivacyConsent] = useState(!!initialPrivacyConsent);
  const [hydrated, setHydrated] = useState(!!initialProfile);
  const [dataRevision, setDataRevision] = useState(0);
  const [datasetSync, setDatasetSync] = useState(getDatasetSyncStatus);
  const saveTimer = useRef(null);
  const assessedRevision = useRef(0);

  useEffect(() => subscribeDataset(() => setDataRevision((revision) => revision + 1)), []);
  useEffect(() => subscribeDatasetSync(setDatasetSync), []);
  useEffect(() => {
    if (privacyConsent && isBazaarIabBuild() && !initialProfile) syncDataset();
  }, [privacyConsent, initialProfile]);

  useEffect(() => {
    const dataChanged = dataRevision !== assessedRevision.current;
    assessedRevision.current = dataRevision;
    if (!hydrated || !result) return;
    const currentVersion = getDataset().meta.version;
    if (!dataChanged && result.datasetVersion === currentVersion) return;
    const refreshed = engine.assess(getDataset(), profile);
    setResult(refreshed);
    saveResult(refreshed, profile);
  }, [dataRevision, hydrated, profile, result]);


  useEffect(() => {
    if (initialProfile) return undefined;
    let mounted = true;
    Promise.all([loadProfile(), loadResult(), loadPrivacyConsent()]).then(([stored, savedResult, consentGiven]) => {
      if (!mounted) return;
      const restoredProfile = { ...engine.emptyProfile(), ...(stored || {}) };
      if (stored) setProfileState(restoredProfile);
      setPrivacyConsent(consentGiven);

      // The persisted result is a compact cache, not the full result model used
      // by the screens. Recompute it from the saved profile and current dataset
      // so a process restart restores the user's last assessment without
      // consuming another assessment credit or showing stale cached scores.
      if (
        savedResult
        && savedResult.profileFingerprint === profileFingerprint(restoredProfile)
        && (
          savedResult.hasResult === true
          || (Array.isArray(savedResult.countries) && savedResult.countries.length > 0)
        )
      ) {
        try {
          setResult(engine.assess(getDataset(), restoredProfile));
        } catch (error) {
          setResult(null);
        }
      }
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

  const acceptPrivacyConsent = useCallback(async () => {
    const saved = await savePrivacyConsent();
    if (saved) setPrivacyConsent(true);
    return saved;
  }, []);

  const compute = useCallback(async (t) => {
    const allowance = await consumeAssessmentCredit();
    if (!allowance) return false;
    const next = engine.assess(getDataset(), profile, t);
    setResult(next);
    saveResult(next, profile);
    return next;
  }, [profile]);

  const resetAll = useCallback(async () => {
    await clearAll();
    setProfileState(engine.emptyProfile());
    setResult(null);
    setPrivacyConsent(false);
  }, []);
  const refreshDataset = useCallback(
    () => (!isBazaarIabBuild() || privacyConsent ? syncDataset() : Promise.resolve({ status: 'consent-required' })),
    [privacyConsent],
  );

  const value = useMemo(() => ({
    profile,
    setProfile,
    updateProfile,
    privacyConsent,
    acceptPrivacyConsent,
    updateNested,
    result,
    setResult,
    compute,
    resetAll,
    hydrated,
    hasAssessment: !!result,
    dataRevision,
    datasetSync,
    refreshDataset,
  }), [profile, setProfile, updateProfile, privacyConsent, acceptPrivacyConsent, updateNested, result, compute, resetAll, hydrated, dataRevision, datasetSync, refreshDataset]);

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) throw new Error('useAppState must be used inside AppStateProvider');
  return context;
}

export default AppStateProvider;
