import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';
import '../storage/token_store.dart';
import '../../features/auth/data/auth_repository_impl.dart';
import '../../features/auth/domain/auth_repository.dart';
import '../../features/auth/presentation/auth_controller.dart';
import '../../features/analysis/data/analysis_repository_impl.dart';
import '../../features/analysis/domain/analysis_repository.dart';
import '../../features/farms/data/farm_repository_impl.dart';
import '../../features/farms/domain/farm_repository.dart';
import '../../features/knowledge/data/knowledge_repository_impl.dart';
import '../../features/knowledge/domain/knowledge_repository.dart';
import '../../features/subscription/data/subscription_repository_impl.dart';
import '../../features/subscription/domain/subscription_repository.dart';

/// Composition root: every dependency is wired here, so features only depend on abstractions.

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(
    tokens: ref.watch(tokenStoreProvider),
    onSessionExpired: () => ref.read(authControllerProvider.notifier).sessionExpired(),
  );
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(api: ref.watch(apiClientProvider), tokens: ref.watch(tokenStoreProvider));
});

final farmRepositoryProvider = Provider<FarmRepository>((ref) {
  return FarmRepositoryImpl(ref.watch(apiClientProvider));
});

final analysisRepositoryProvider = Provider<AnalysisRepository>((ref) {
  return AnalysisRepositoryImpl(ref.watch(apiClientProvider));
});

final knowledgeRepositoryProvider = Provider<KnowledgeRepository>((ref) {
  return KnowledgeRepositoryImpl(ref.watch(apiClientProvider));
});

final subscriptionRepositoryProvider = Provider<SubscriptionRepository>((ref) {
  return SubscriptionRepositoryImpl(ref.watch(apiClientProvider));
});
