# Hook flowcharts

Mermaid flowcharts for `useBillingProduct` and `useBillingSubscription`. See [README](../README.md#hooks-recommended) for full API and examples.

---

## useBillingProduct

### On mount

```mermaid
flowchart TB
  A["useBillingProduct()"] --> B{isAvailable?}
  B -->|No| C["loading = false\npurchased = null"]
  B -->|Yes| D["fetchStatus()"]
  D --> E["connect(connectOptions)"]
  E --> F["queryPurchaseProduct(productId)"]
  F --> G["setPurchased(result)"]
  G --> H["disconnect()"]
  H --> I["loading = false"]
```

### purchase()

```mermaid
flowchart TB
  P["purchase() called"] --> Q{isAvailable?}
  Q -->|No| R["return null"]
  Q -->|Yes| S["setPurchasing(true)"]
  S --> T["connect(connectOptions)"]
  T --> U["purchaseProduct(productId, options)"]
  U --> V{Success?}
  V -->|Yes| W["setPurchased(result)\nreturn result"]
  V -->|No| X["setError(message)\nreturn null"]
  W --> Y["disconnect()"]
  X --> Y
  Y --> Z["setPurchasing(false)"]
```

---

## useBillingSubscription

### On mount

```mermaid
flowchart TB
  A["useBillingSubscription()"] --> B{isAvailable?}
  B -->|No| C["loading = false\nactiveSubscription = null"]
  B -->|Yes| D["fetchStatus()"]
  D --> E["connect(connectOptions)"]
  E --> F["querySubscribeProduct(productId)"]
  F --> G["setActiveSubscription(result)"]
  G --> H["disconnect()"]
  H --> I["loading = false"]
```

### subscribe()

```mermaid
flowchart TB
  P["subscribe() called"] --> Q{isAvailable?}
  Q -->|No| R["return null"]
  Q -->|Yes| S["setSubscribing(true)"]
  S --> T["connect(connectOptions)"]
  T --> U["subscribeProduct(productId, options)"]
  U --> V{Success?}
  V -->|Yes| W["setActiveSubscription(result)\nreturn result"]
  V -->|No| X["setError(message)\nreturn null"]
  W --> Y["disconnect()"]
  X --> Y
  Y --> Z["setSubscribing(false)"]
```
