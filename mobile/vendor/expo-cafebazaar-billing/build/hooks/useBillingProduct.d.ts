import type { ConnectOptions, PurchaseResult } from "../CafeBazaarBilling.types";
export type UseBillingProductOptions = ConnectOptions;
export type UseBillingProductResult = {
    /** Whether the product is already purchased. */
    purchased: PurchaseResult | null;
    /** True while checking purchase status on mount or after refresh(). */
    loading: boolean;
    /** Start purchase flow. Resolves with result on success. */
    purchase: (options?: {
        developerPayload?: string;
        dynamicPriceToken?: string;
    }) => Promise<PurchaseResult | null>;
    /** True while purchase flow is in progress. */
    purchasing: boolean;
    /** Last error message from purchase or refresh. */
    error: string | null;
    /** Re-query purchase status from Bazaar. */
    refresh: () => Promise<void>;
    /** False when billing is not available (e.g. not Android or module not linked). */
    isAvailable: boolean;
};
export declare function useBillingProduct(productId: string, connectOptions?: UseBillingProductOptions): UseBillingProductResult;
//# sourceMappingURL=useBillingProduct.d.ts.map