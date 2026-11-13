# Myket Billing Client
-keep class ir.myket.billingclient.** { *; }
-keep interface ir.myket.billingclient.** { *; }
-keep class com.android.vending.billing.** { *; }
-keep interface com.android.vending.billing.** { *; }

# Models & Reflection
-keepclassmembers class ir.myket.billingclient.util.** {
    public <fields>;
    public <methods>;
}
