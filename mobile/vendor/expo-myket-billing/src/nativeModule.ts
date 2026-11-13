import { requireOptionalNativeModule } from "expo-modules-core";

import type { MyketBillingModule } from "./MyketBilling.types";

const NativeModule =
  requireOptionalNativeModule<MyketBillingModule>("MyketBilling");

export default NativeModule;
