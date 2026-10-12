import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../../analysis/domain/analysis_entities.dart';
import '../../analysis/presentation/analysis_providers.dart';

class HistoryPage extends ConsumerStatefulWidget {
  const HistoryPage({super.key});

  @override
  ConsumerState<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends ConsumerState<HistoryPage> {
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _scroll.addListener(() {
      if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 300) {
        ref.read(historyProvider.notifier).loadMore();
      }
    });
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final history = ref.watch(historyProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('گزارش‌ها و تاریخچه')),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(historyProvider.future),
        child: history.when(
          loading: () => const LoadingView(),
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(historyProvider)),
          data: (state) {
            if (state.items.isEmpty) {
              return ListView(
                children: [
                  SizedBox(
                    height: MediaQuery.sizeOf(context).height * 0.7,
                    child: EmptyState(
                      icon: Icons.history_rounded,
                      title: 'هنوز تحلیلی انجام نشده است',
                      message: 'نخستین تحلیل تصویر خود را انجام دهید تا گزارش‌ها اینجا ذخیره شوند.',
                      actionLabel: 'تحلیل تصویر',
                      onAction: () => context.push(AppRoutes.analysis),
                    ),
                  ),
                ],
              );
            }
            return ListView.separated(
              controller: _scroll,
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              itemCount: state.items.length + 1,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                if (i == state.items.length) {
                  if (state.loadingMore) {
                    return const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()));
                  }
                  if (state.nextCursor != null) {
                    return Center(
                      child: TextButton(
                        onPressed: () => ref.read(historyProvider.notifier).loadMore(),
                        child: const Text('نمایش بیشتر'),
                      ),
                    );
                  }
                  return const SizedBox.shrink();
                }
                return _HistoryTile(item: state.items[i]);
              },
            );
          },
        ),
      ),
    );
  }
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({required this.item});

  final AnalysisSummary item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final failed = item.status == 'failed';
    final pending = item.status == 'pending';
    final color = failed
        ? AppColors.danger
        : pending
            ? AppColors.info
            : AppColors.confidence(item.confidence ?? 0);

    return PestinoCard(
      onTap: failed || pending ? null : () => context.push(AppRoutes.report(item.id)),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16)),
            child: Icon(
              failed ? Icons.error_outline_rounded : (pending ? Icons.hourglass_top_rounded : Icons.biotech_rounded),
              color: color,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  failed ? 'تحلیل ناموفق' : (item.primaryTitle ?? 'نتیجه تحلیل'),
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  '${Persian.category(item.category)} • ${Persian.season(item.season)} • ${Persian.dateTime(item.createdAt)}',
                  style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft),
                ),
              ],
            ),
          ),
          if (item.confidence != null && item.isCompleted)
            Text(Persian.percent(item.confidence!), style: TextStyle(color: color, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}
