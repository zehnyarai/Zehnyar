import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/farm_entities.dart';

final farmsListProvider = FutureProvider.autoDispose<List<Farm>>((ref) {
  return ref.watch(farmRepositoryProvider).list();
});

final farmDetailProvider = FutureProvider.autoDispose.family<Farm, String>((ref, id) {
  return ref.watch(farmRepositoryProvider).get(id);
});

final farmTreesProvider = FutureProvider.autoDispose.family<List<Tree>, String>((ref, farmId) {
  return ref.watch(farmRepositoryProvider).trees(farmId);
});
