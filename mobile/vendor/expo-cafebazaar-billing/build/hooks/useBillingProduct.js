import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import { getBillingModule } from "../nativeModule";
export function useBillingProduct(productId, connectOptions) {
    const billing = getBillingModule();
    const isAvailable = Platform.OS === "android" && billing !== null && billing !== undefined;
    const [purchased, setPurchased] = useState(null);
    const [loading, setLoading] = useState(true);
    const [purchasing, setPurchasing] = useState(false);
    const [error, setError] = useState(null);
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
        }
        catch {
            setPurchased(null);
        }
        finally {
            setLoading(false);
            billing.disconnect().catch(() => { });
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
            if (cancelled)
                return;
        });
        return () => {
            cancelled = true;
        };
    }, [isAvailable, fetchStatus]);
    const purchase = useCallback(async (options) => {
        if (!billing || !isAvailable)
            return null;
        setError(null);
        setPurchasing(true);
        try {
            await billing.connect(connectOptions);
            const result = await billing.purchaseProduct(productId, options);
            await billing.disconnect();
            setPurchased(result);
            return result;
        }
        catch (e) {
            const message = e instanceof Error ? e.message : "Purchase failed";
            setError(message);
            return null;
        }
        finally {
            setPurchasing(false);
            billing.disconnect().catch(() => { });
        }
    }, [billing, isAvailable, productId, connectOptions]);
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
//# sourceMappingURL=useBillingProduct.js.map