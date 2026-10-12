import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/farm_entities.dart';
import 'farm_providers.dart';

class FarmsPage extends ConsumerWidget {
  const FarmsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final farms = ref.watch(farmsListProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('مزرعه‌های من')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await context.push(AppRoutes.farmNew);
          ref.invalidate(farmsListProvider);
        },
        icon: const Icon(Icons.add_rounded),
        label: const Text('باغ جدید'),
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.refresh(farmsListProvider.future),
        child: farms.when(
          loading: () => const LoadingView(),
          error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(farmsListProvider)),
          data: (items) {
            if (items.isEmpty) {
              return ListView(
                children: [
                  SizedBox(
                    height: MediaQuery.sizeOf(context).height * 0.7,
                    child: EmptyState(
                      icon: Icons.agriculture_rounded,
                      title: 'هنوز باغی ثبت نشده است',
                      message: 'اطلاعات باغ خود را ثبت کنید تا تحلیل‌ها دقیق‌تر شوند.',
                      actionLabel: 'ثبت اولین باغ',
                      onAction: () => context.push(AppRoutes.farmNew),
                    ),
                  ),
                ],
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, i) => _FarmCard(farm: items[i]),
            );
          },
        ),
      ),
    );
  }
}

class _FarmCard extends StatelessWidget {
  const _FarmCard({required this.farm});

  final Farm farm;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return PestinoCard(
      onTap: () => context.push(AppRoutes.farm(farm.id)),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(color: AppColors.green100, borderRadius: BorderRadius.circular(16)),
            child: const Icon(Icons.park_rounded, color: AppColors.green700, size: 30),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(farm.name, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text('${farm.province}، ${farm.city}', style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    if (farm.pistachioVariety != null) StatusChip(label: farm.pistachioVariety!, color: AppColors.earth500),
                    if (farm.areaHectares != null)
                      StatusChip(label: '${Persian.number(farm.areaHectares!, decimals: 1)} هکتار', color: AppColors.green700),
                  ],
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_left_rounded, color: AppColors.inkSoft),
        ],
      ),
    );
  }
}
