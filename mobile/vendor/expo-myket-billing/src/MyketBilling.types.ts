/**
 * Result of a successful in-app product purchase from Myket.
 * @see https://myket.ir/kb/topics/technical-docs/
 */
export type PurchaseResult = {
  orderId: string;
  packageName: string;
  sku: string;
  purchaseTime: number;
  purchaseState: number;
  developerPayload: string;
  token: string;
  originalJson: string;
  signature: string;
  responseCode?: number;
};

/**
 * SKU (product) details from Myket developer panel.
 */
export type SkuDetails = {
  sku: string;
  title: string;
  price: string;
  description?: string;
  type: string;
  itemType: string;
  json: string;
};

/**
 * Options when connecting to Myket billing.
 */
export type ConnectOptions = {
  /**
   * RSA public key for purchase verification (recommended for production).
   * Obtain from Myket developer panel → In-app products → Public key.
   */
  rsaPublicKey?: string;
};

/**
 * Options when purchasing a product.
 */
export type PurchaseOptions = {
  /**
   * Optional developer payload for linking the purchase to a user/order.
   * Maximum 800 characters. Verify on server for security.
   */
  developerPayload?: string;
};

/**
 * Inventory result containing products and active purchases.
 */
export type InventoryResult = {
  products: SkuDetails[];
  purchases: PurchaseResult[];
  responseCode: number;
};

/**
 * Native module interface for Myket Billing.
 */
export interface MyketBillingModule {
  connect(options?: ConnectOptions): Promise<void>;
  disconnect(): Promise<void>;
  queryInventory(
    querySkuDetails: boolean,
    skus: string[],
  ): Promise<InventoryResult>;
  purchaseProduct(
    sku: string,
    options?: PurchaseOptions,
  ): Promise<PurchaseResult>;
  consumePurchase(purchaseToken: string): Promise<void>;
  getPurchasedProducts(): Promise<PurchaseResult[]>;
  getInAppSkuDetails(productIds: string[]): Promise<SkuDetails[]>;
}
