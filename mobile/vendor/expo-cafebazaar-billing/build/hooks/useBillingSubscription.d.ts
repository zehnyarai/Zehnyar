import type { ConnectOptions, PurchaseResult } from "../CafeBazaarBilling.types";
export type UseBillingSubscriptionOptions = ConnectOptions;
export type UseBillingSubscriptionResult = {
    /** Active subscription for this product, or null if none / expired. */
    activeSubscription: PurchaseResult | null;
    /** True while checking subscription status on mount or after refresh(). */
    loading: boolean;
    /** Start subscription flow. Resolves with result on success. */
    subscribe: (options?: {
        developerPayload?: string;
        dynamicPriceToken?: string;
    }) => Promise<PurchaseResult | null>;
    /** True while subscribe flow is in progress. */
    subscribing: boolean;
    /** Last error message from subscribe or refresh. */
    error: string | null;
    /** Re-query subscription status from Bazaar. */
    refresh: () => Promise<void>;
    /** False when billing is not available (e.g. not Android or module not linked). */
    isAvailable: boolean;
};
export declare function useBillingSubscription(productId: string, connectOptions?: UseBillingSubscriptionOptions): UseBillingSubscriptionResult;
//# sourceMappingURL=useBillingSubscription.d.ts.map