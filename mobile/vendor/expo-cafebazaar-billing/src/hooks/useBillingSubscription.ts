import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import type { ConnectOptions, PurchaseResult } from "../CafeBazaarBilling.types";
import { getBillingModule } from "../nativeModule";

export type UseBillingSubscriptionOptions = ConnectOptions;

export type UseBillingSubscriptionResult = {
  /** Active subscription for this product, or null if none / expired. */
  activeSubscription: PurchaseResult | null;
  /** True while checking subscription status on mount or after refresh(). */
  loading: boolean;
  /** Start subscription flow. Resolves with result on success. */
  subscribe: (options?: { developerPayload?: string; dynamicPriceToken?: string }) => Promise<PurchaseResult | null>;
  /** True while subscribe flow is in progress. */
  subscribing: boolean;
  /** Last error message from subscribe or refresh. */
  error: string | null;
  /** Re-query subscription status from Bazaar. */
  refresh: () => Promise<void>;
  /** False when billing is not available (e.g. not Android or module not linked). */
  isAvailable: boolean;
};

export function useBillingSubscription(
  productId: string,
  connectOptions?: UseBillingSubscriptionOptions,
): UseBillingSubscriptionResult {
  const billing = getBillingModule();
  const isAvailable =
    Platform.OS === "android" && billing !== null && billing !== undefined;

  const [activeSubscription, setActiveSubscription] =
    useState<PurchaseResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!billing) {
      setActiveSubscription(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await billing.connect(connectOptions);
      const result = await billing.querySubscribeProduct(productId);
      setActiveSubscription(result ?? null);
    } catch {
      setActiveSubscription(null);
    } finally {
      setLoading(false);
      billing.disconnect().catch(() => {});
    }
  }, [billing, productId, connectOptions?.rsaPublicKey]);

  useEffect(() => {
    if (!isAvailable) {
      setLoading(false);
      setActiveSubscription(null);
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

  const subscribe = useCallback(
    async (options?: {
      developerPayload?: string;
      dynamicPriceToken?: string;
    }) => {
      if (!billing || !isAvailable) return null;
      setError(null);
      setSubscribing(true);
      try {
        await billing.connect(connectOptions);
        const result = await billing.subscribeProduct(productId, options);
        await billing.disconnect();
        setActiveSubscription(result);
        return result;
      } catch (e) {
        const message = e instanceof Error ? e.message : "Subscribe failed";
        setError(message);
        return null;
      } finally {
        setSubscribing(false);
        billing.disconnect().catch(() => {});
      }
    },
    [billing, isAvailable, productId, connectOptions],
  );

  return {
    activeSubscription,
    loading,
    subscribe,
    subscribing,
    error,
    refresh: fetchStatus,
    isAvailable,
  };
}
