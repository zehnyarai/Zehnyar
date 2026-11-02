import { requireOptionalNativeModule } from "expo-modules-core";
const NativeModule = requireOptionalNativeModule("CafeBazaarBilling");
export default NativeModule;
export { useBillingProduct } from "./hooks/useBillingProduct";
export { useBillingSubscription } from "./hooks/useBillingSubscription";
//# sourceMappingURL=index.js.map