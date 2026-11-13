package expo.modules.myketbilling

import android.app.Activity
import android.os.Handler
import android.os.Looper
import expo.modules.kotlin.Promise
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import ir.myket.billingclient.IabHelper
import ir.myket.billingclient.util.IabResult
import ir.myket.billingclient.util.Inventory
import ir.myket.billingclient.util.Purchase
import java.util.concurrent.ConcurrentHashMap

/**
 * Myket In-App Billing v2.2 for Expo (Android).
 * Uses the official Myket Billing Client SDK (ir.myket:billing:2.2).
 * @see https://myket.ir/kb/topics/technical-docs/
 */
class MyketBillingModule : Module() {

  private var iabHelper: IabHelper? = null
  private var rsaPublicKey: String? = null

  // Cache of purchases returned by queryInventory, keyed by purchase token,
  // so consumePurchase can look up the full Purchase object.
  private val purchaseCache = ConcurrentHashMap<String, Purchase>()

  override fun definition() = ModuleDefinition {
    Name("MyketBilling")

    AsyncFunction("connect") { options: Map<String, Any>?, promise: Promise ->
      val rsaKey = options?.get("rsaPublicKey") as? String
      rsaPublicKey = rsaKey
      val ctx = appContext.reactContext ?: run {
        promise.reject("ERR_CONTEXT", "React context not available", null)
        return@AsyncFunction
      }
      val activity = appContext.currentActivity ?: run {
        promise.reject("ERR_NO_ACTIVITY", "Activity not available", null)
        return@AsyncFunction
      }

      iabHelper = IabHelper(activity, rsaKey ?: "")
      iabHelper?.enableDebugLogging(false, "MyketBilling")

      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String, e: Throwable?) {
        if (settled) return
        settled = true
        if (success) promise.resolve(null) else promise.reject(code, msg, e)
      }

      iabHelper?.startSetup { result ->
        if (result.isSuccess) {
          settleOnce(true, "", "", null)
        } else {
          iabHelper = null
          settleOnce(false, "ERR_CONNECT", result.message ?: "Myket billing setup failed", null)
        }
      }
    }

    AsyncFunction("disconnect") { promise: Promise ->
      iabHelper?.dispose()
      iabHelper = null
      rsaPublicKey = null
      purchaseCache.clear()
      promise.resolve(null)
    }

    AsyncFunction("queryInventory") { querySkuDetails: Boolean, skus: List<String>, promise: Promise ->
      val helper = iabHelper ?: run {
        promise.reject("ERR_NOT_CONNECTED", "Call connect() first", null)
        return@AsyncFunction
      }
      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String, data: Map<String, Any>?) {
        if (settled) return
        settled = true
        if (success) promise.resolve(data) else promise.reject(code, msg, null)
      }

      handler.post {
        helper.queryInventoryAsync(querySkuDetails, skus) { result, inventory ->
          if (result.isFailure || inventory == null) {
            settleOnce(false, "ERR_QUERY", result.message ?: "Query inventory failed", null)
            return@queryInventoryAsync
          }

          val products = mutableListOf<Map<String, Any>>()
          val purchases = mutableListOf<Map<String, Any>>()

          inventory.getAllProducts().forEach { details ->
            val map = mutableMapOf<String, Any>()
            map["sku"] = details.getSku()
            map["title"] = details.getTitle()
            map["price"] = details.getPrice()
            map["description"] = details.getDescription()
            map["type"] = details.getType()
            map["itemType"] = details.getType()
            map["json"] = details.toJson().toString()
            products.add(map)
          }

          inventory.getAllPurchases().forEach { purchase ->
            val map = mutableMapOf<String, Any>()
            map["sku"] = purchase.getSku()
            map["orderId"] = purchase.getOrderId()
            map["packageName"] = purchase.getPackageName()
            map["purchaseTime"] = purchase.getPurchaseTime()
            map["purchaseState"] = purchase.getPurchaseState()
            map["developerPayload"] = purchase.getDeveloperPayload()
            map["token"] = purchase.getToken()
            map["originalJson"] = purchase.getOriginalJson()
            map["signature"] = purchase.getSignature()
            purchases.add(map)
            purchaseCache[purchase.getToken()] = purchase
          }

          settleOnce(true, "", "", mapOf(
            "products" to products,
            "purchases" to purchases,
            "responseCode" to result.response
          ))
        }
      }
    }

    AsyncFunction("purchaseProduct") { sku: String, options: Map<String, Any>?, promise: Promise ->
      val helper = iabHelper ?: run {
        promise.reject("ERR_NOT_CONNECTED", "Call connect() first", null)
        return@AsyncFunction
      }
      val activity = appContext.currentActivity ?: run {
        promise.reject("ERR_NO_ACTIVITY", "Activity not available", null)
        return@AsyncFunction
      }
      val developerPayload = options?.get("developerPayload") as? String

      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String, data: Map<String, Any>?) {
        if (settled) return
        settled = true
        if (success) promise.resolve(data) else promise.reject(code, msg, null)
      }

      handler.post {
        helper.launchPurchaseFlow(
          activity,
          sku,
          { result, purchase ->
            if (result.isFailure || purchase == null) {
              settleOnce(false, "ERR_PURCHASE", result.message ?: "Purchase failed or canceled", null)
              return@launchPurchaseFlow
            }
            purchaseCache[purchase.getToken()] = purchase
            settleOnce(true, "", "", mapOf(
              "sku" to purchase.getSku(),
              "orderId" to purchase.getOrderId(),
              "packageName" to purchase.getPackageName(),
              "purchaseTime" to purchase.getPurchaseTime(),
              "purchaseState" to purchase.getPurchaseState(),
              "developerPayload" to purchase.getDeveloperPayload(),
              "token" to purchase.getToken(),
              "originalJson" to purchase.getOriginalJson(),
              "signature" to purchase.getSignature(),
              "responseCode" to result.response
            ))
          },
          developerPayload ?: ""
        )
      }
    }

    AsyncFunction("consumePurchase") { purchaseToken: String, promise: Promise ->
      val helper = iabHelper ?: run {
        promise.reject("ERR_NOT_CONNECTED", "Call connect() first", null)
        return@AsyncFunction
      }
      val purchase = purchaseCache[purchaseToken] ?: run {
        promise.reject("ERR_PURCHASE_NOT_FOUND", "Purchase not found in local cache for token: $purchaseToken", null)
        return@AsyncFunction
      }

      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String) {
        if (settled) return
        settled = true
        if (success) promise.resolve(null) else promise.reject(code, msg, null)
      }

      handler.post {
        helper.consumeAsync(purchase) { consumedPurchase, result ->
          if (result.isSuccess) {
            purchaseCache.remove(purchaseToken)
            settleOnce(true, "", "")
          } else {
            settleOnce(false, "ERR_CONSUME", result.message ?: "Consume failed")
          }
        }
      }
    }

    AsyncFunction("getPurchasedProducts") { promise: Promise ->
      val helper = iabHelper ?: run {
        promise.reject("ERR_NOT_CONNECTED", "Call connect() first", null)
        return@AsyncFunction
      }
      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String, data: List<Map<String, Any>>?) {
        if (settled) return
        settled = true
        if (success) promise.resolve(data) else promise.reject(code, msg, null)
      }

      handler.post {
        helper.queryInventoryAsync(false, emptyList()) { result, inventory ->
          if (result.isFailure || inventory == null) {
            settleOnce(false, "ERR_QUERY", result.message ?: "Query purchases failed", null)
            return@queryInventoryAsync
          }
          val list = mutableListOf<Map<String, Any>>()
          inventory.getAllPurchases().forEach { purchase ->
            purchaseCache[purchase.getToken()] = purchase
            list.add(mapOf(
              "sku" to purchase.getSku(),
              "orderId" to purchase.getOrderId(),
              "packageName" to purchase.getPackageName(),
              "purchaseTime" to purchase.getPurchaseTime(),
              "purchaseState" to purchase.getPurchaseState(),
              "developerPayload" to purchase.getDeveloperPayload(),
              "token" to purchase.getToken(),
              "originalJson" to purchase.getOriginalJson(),
              "signature" to purchase.getSignature()
            ))
          }
          settleOnce(true, "", "", list)
        }
      }
    }

    AsyncFunction("getInAppSkuDetails") { productIds: List<String>, promise: Promise ->
      val helper = iabHelper ?: run {
        promise.reject("ERR_NOT_CONNECTED", "Call connect() first", null)
        return@AsyncFunction
      }
      var settled = false
      fun settleOnce(success: Boolean, code: String, msg: String, data: List<Map<String, Any>>?) {
        if (settled) return
        settled = true
        if (success) promise.resolve(data) else promise.reject(code, msg, null)
      }

      handler.post {
        helper.queryInventoryAsync(true, productIds) { result, inventory ->
          if (result.isFailure || inventory == null) {
            settleOnce(false, "ERR_SKU", result.message ?: "Get SKU details failed", null)
            return@queryInventoryAsync
          }
          val list = mutableListOf<Map<String, Any>>()
          inventory.getAllProducts().forEach { details ->
            list.add(mapOf(
              "sku" to details.getSku(),
              "title" to details.getTitle(),
              "price" to details.getPrice(),
              "description" to details.getDescription(),
              "type" to details.getType(),
              "itemType" to details.getType(),
              "json" to details.toJson().toString()
            ))
          }
          settleOnce(true, "", "", list)
        }
      }
    }
  }

  private val handler = Handler(Looper.getMainLooper())
}
