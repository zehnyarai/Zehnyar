import 'subscription_entities.dart';

abstract interface class SubscriptionRepository {
  Future<List<PlanInfo>> plans();
  Future<PlanInfo> currentPlan();

  /// Starts a purchase. Throws AppFailure(PAYMENT_NOT_CONFIGURED) until a provider is enabled.
  Future<void> checkout(String planCode);
}
