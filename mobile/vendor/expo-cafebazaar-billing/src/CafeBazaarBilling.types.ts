/**
 * Result of a successful in-app product purchase.
 * @see https://developers.cafebazaar.ir/fa/guidelines/in-app-billing/intro
 */
export type PurchaseResult = {
  orderId: string;
  packageName: string;
  productId: string;
  purchaseTime: number;
  purchaseState: number;
  developerPayload: string;
  purchaseToken: string;
  originalJson: string;
  dataSignature: string;
};

/**
 * Trial subscription eligibility from Cafe Bazaar.
 * @see https://github.com/cafebazaar/Poolakey
 */
export type TrialSubscriptionInfo = {
  /** Whether a trial subscription is available for the user. */
  isAvailable: boolean;
  /** Trial period length in days when available. */
  trialPeriodDays: number;
};

/**
 * SKU (product) details from Cafe Bazaar.
 */
export type SkuDetails = {
  sku: string;
  type: string;
  price: string;
  title: string;
  description: string;
};

/**
 * Options when connecting to Cafe Bazaar billing.
 */
export type ConnectOptions = {
  /**
   * RSA public key for purchase verification (recommended for production).
   * If omitted, local security check is disabled.
   */
  rsaPublicKey?: string;
};

/**
 * Options when purchasing a product or subscription.
 */
export type PurchaseOptions = {
  /** Optional developer payload. */
  developerPayload?: string;
  /** Optional dynamic price token for dynamic pricing. */
  dynamicPriceToken?: string;
};

/**
 * Native module interface for Cafe Bazaar Billing.
 */
export interface CafeBazaarBillingModule {
  connect(options?: ConnectOptions): Promise<void>;
  disconnect(): Promise<void>;
  purchaseProduct(
    productId: string,
    options?: PurchaseOptions,
  ): Promise<PurchaseResult>;
  subscribeProduct(
    productId: string,
    options?: PurchaseOptions,
  ): Promise<PurchaseResult>;
  consumePurchase(purchaseToken: string): Promise<void>;
  getPurchasedProducts(): Promise<PurchaseResult[]>;
  getSubscribedProducts(): Promise<PurchaseResult[]>;
  queryPurchaseProduct(productId: string): Promise<PurchaseResult | null>;
  querySubscribeProduct(productId: string): Promise<PurchaseResult | null>;
  getInAppSkuDetails(productIds: string[]): Promise<SkuDetails[]>;
  getSubscriptionSkuDetails(productIds: string[]): Promise<SkuDetails[]>;
  checkTrialSubscription(): Promise<TrialSubscriptionInfo>;
}
