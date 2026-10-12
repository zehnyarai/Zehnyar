import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/admin_entities.dart';

final adminStatsProvider = FutureProvider.autoDispose<AdminStats>((ref) {
  return ref.watch(adminRepositoryProvider).stats();
});

final adminAiSettingsProvider = FutureProvider.autoDispose<AiSettings>((ref) {
  return ref.watch(adminRepositoryProvider).aiSettings();
});

final adminAiFeaturesProvider = FutureProvider.autoDispose<List<AiFeature>>((ref) {
  return ref.watch(adminRepositoryProvider).aiFeatures();
});

final adminAiUsageProvider = FutureProvider.autoDispose<List<AiUsageRow>>((ref) {
  return ref.watch(adminRepositoryProvider).aiUsage(days: 7);
});

final adminUsersProvider = FutureProvider.autoDispose.family<List<AdminUser>, String>((ref, query) {
  return ref.watch(adminRepositoryProvider).users(query: query);
});

final adminAuditProvider = FutureProvider.autoDispose<List<AuditEntry>>((ref) {
  return ref.watch(adminRepositoryProvider).audit(limit: 80);
});
