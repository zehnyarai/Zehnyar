import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import type { ConnectOptions, PurchaseResult } from "../CafeBazaarBilling.types";
import { getBillingModule } from "../nativeModule";

export type UseBillingProductOptions = ConnectOptions;

export type UseBillingProductResult = {
  /** Whether the product is already purchased. */
  purchased: PurchaseResult | null;
  /** True while checking purchase status on mount or after refresh(). */
  loading: boolean;
  /** Start purchase flow. Resolves with result on success. */
  purchase: (options?: { developerPayload?: string; dynamicPriceToken?: string }) => Promise<PurchaseResult | null>;
  /** True while purchase flow is in progress. */
  purchasing: boolean;
  /** Last error message from purchase or refresh. */
  error: string | null;
  /** Re-query purchase status from Bazaar. */
  refresh: () => Promise<void>;
  /** False when billing is not available (e.g. not Android or module not linked). */
  isAvailable: boolean;
};

export function useBillingProduct(
  productId: string,
  connectOptions?: UseBillingProductOptions,
): UseBillingProductResult {
  const billing = getBillingModule();
  const isAvailable =
    Platform.OS === "android" && billing !== null && billing !== undefined;

  const [purchased, setPurchased] = useState<PurchaseResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!billing) {
      setPurchased(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await billing.connect(connectOptions);
      const result = await billing.queryPurchaseProduct(productId);
      setPurchased(result ?? null);
    } catch {
      setPurchased(null);
    } finally {
      setLoading(false);
      billing.disconnect().catch(() => {});
    }
  }, [billing, productId, connectOptions?.rsaPublicKey]);

  useEffect(() => {
    if (!isAvailable) {
      setLoading(false);
      setPurchased(null);
      return;
    }
    let cancelled = false;
    fetchStatus().then(() => {
      if (cancelled) return;
    });
    return () => {
      cancelled = true;
    };
  }, [isAvailable, fetchStatus]);

  const purchase = useCallback(
    async (options?: {
      developerPayload?: string;
      dynamicPriceToken?: string;
    }) => {
      if (!billing || !isAvailable) return null;
      setError(null);
      setPurchasing(true);
      try {
        await billing.connect(connectOptions);
        const result = await billing.purchaseProduct(productId, options);
        await billing.disconnect();
        setPurchased(result);
        return result;
      } catch (e) {
        const message = e instanceof Error ? e.message : "Purchase failed";
        setError(message);
        return null;
      } finally {
        setPurchasing(false);
        billing.disconnect().catch(() => {});
      }
    },
    [billing, isAvailable, productId, connectOptions],
  );

  return {
    purchased,
    loading,
    purchase,
    purchasing,
    error,
    refresh: fetchStatus,
    isAvailable,
  };
}
