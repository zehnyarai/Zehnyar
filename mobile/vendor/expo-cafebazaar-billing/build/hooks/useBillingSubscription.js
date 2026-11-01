import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import { getBillingModule } from "../nativeModule";
export function useBillingSubscription(productId, connectOptions) {
    const billing = getBillingModule();
    const isAvailable = Platform.OS === "android" && billing !== null && billing !== undefined;
    const [activeSubscription, setActiveSubscription] = useState(null);
    const [loading, setLoading] = useState(true);
    const [subscribing, setSubscribing] = useState(false);
    const [error, setError] = useState(null);
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
        }
        catch {
            setActiveSubscription(null);
        }
        finally {
            setLoading(false);
            billing.disconnect().catch(() => { });
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
            if (cancelled)
                return;
        });
        return () => {
            cancelled = true;
        };
    }, [isAvailable, fetchStatus]);
    const subscribe = useCallback(async (options) => {
        if (!billing || !isAvailable)
            return null;
        setError(null);
        setSubscribing(true);
        try {
            await billing.connect(connectOptions);
            const result = await billing.subscribeProduct(productId, options);
            await billing.disconnect();
            setActiveSubscription(result);
            return result;
        }
        catch (e) {
            const message = e instanceof Error ? e.message : "Subscribe failed";
            setError(message);
            return null;
        }
        finally {
            setSubscribing(false);
            billing.disconnect().catch(() => { });
        }
    }, [billing, isAvailable, productId, connectOptions]);
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
//# sourceMappingURL=useBillingSubscription.js.map