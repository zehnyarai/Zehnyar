import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/subscription_entities.dart';

final plansProvider = FutureProvider.autoDispose<List<PlanInfo>>((ref) {
  return ref.watch(subscriptionRepositoryProvider).plans();
});

final currentPlanProvider = FutureProvider.autoDispose<PlanInfo>((ref) {
  return ref.watch(subscriptionRepositoryProvider).currentPlan();
});
