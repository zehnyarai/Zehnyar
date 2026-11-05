import { requireOptionalNativeModule } from "expo-modules-core";
import type { CafeBazaarBillingModule } from "./CafeBazaarBilling.types";

export const getBillingModule = (): CafeBazaarBillingModule | null =>
  requireOptionalNativeModule<CafeBazaarBillingModule>("CafeBazaarBilling");
