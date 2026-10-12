import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/analysis_entities.dart';

final analysisUsageProvider = FutureProvider.autoDispose<AnalysisUsage>((ref) {
  return ref.watch(analysisRepositoryProvider).usage();
});

final analysisDetailProvider = FutureProvider.autoDispose.family<Analysis, String>((ref, id) {
  return ref.watch(analysisRepositoryProvider).get(id);
});

class HistoryState {
  const HistoryState({required this.items, this.nextCursor, this.loadingMore = false});

  final List<AnalysisSummary> items;
  final String? nextCursor;
  final bool loadingMore;

  HistoryState copyWith({List<AnalysisSummary>? items, String? nextCursor, bool? loadingMore, bool clearCursor = false}) {
    return HistoryState(
      items: items ?? this.items,
      nextCursor: clearCursor ? null : (nextCursor ?? this.nextCursor),
      loadingMore: loadingMore ?? this.loadingMore,
    );
  }
}

/// Paginated analysis history (cursor-based).
class HistoryController extends AutoDisposeAsyncNotifier<HistoryState> {
  @override
  Future<HistoryState> build() async {
    final page = await ref.watch(analysisRepositoryProvider).list();
    return HistoryState(items: page.items, nextCursor: page.nextCursor);
  }

  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || current.nextCursor == null || current.loadingMore) return;
    state = AsyncData(current.copyWith(loadingMore: true));
    try {
      final page = await ref.read(analysisRepositoryProvider).list(cursor: current.nextCursor);
      state = AsyncData(current.copyWith(
        items: [...current.items, ...page.items],
        nextCursor: page.nextCursor,
        clearCursor: page.nextCursor == null,
        loadingMore: false,
      ));
    } catch (_) {
      state = AsyncData(current.copyWith(loadingMore: false));
      rethrow;
    }
  }

  Future<void> removeLocal(String id) async {
    final current = state.valueOrNull;
    if (current == null) return;
    state = AsyncData(current.copyWith(items: current.items.where((e) => e.id != id).toList()));
  }
}

final historyProvider = AsyncNotifierProvider.autoDispose<HistoryController, HistoryState>(HistoryController.new);
