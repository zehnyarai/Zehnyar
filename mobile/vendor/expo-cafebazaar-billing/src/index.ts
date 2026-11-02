import { requireOptionalNativeModule } from "expo-modules-core";

import type { CafeBazaarBillingModule } from "./CafeBazaarBilling.types";

export type {
  CafeBazaarBillingModule,
  ConnectOptions,
  PurchaseOptions,
  PurchaseResult,
  SkuDetails,
  TrialSubscriptionInfo,
} from "./CafeBazaarBilling.types";

const NativeModule =
  requireOptionalNativeModule<CafeBazaarBillingModule>("CafeBazaarBilling");

export default NativeModule;

export { useBillingProduct } from "./hooks/useBillingProduct";
export { useBillingSubscription } from "./hooks/useBillingSubscription";
