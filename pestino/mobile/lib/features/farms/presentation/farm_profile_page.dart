import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/farm_entities.dart';
import 'farm_providers.dart';

class FarmProfilePage extends ConsumerWidget {
  const FarmProfilePage({super.key, required this.farmId});

  final String farmId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final farm = ref.watch(farmDetailProvider(farmId));
    return Scaffold(
      appBar: AppBar(
        title: const Text('پروفایل باغ'),
        actions: [
          IconButton(
            tooltip: 'ویرایش',
            icon: const Icon(Icons.edit_rounded),
            onPressed: () async {
              await context.push(AppRoutes.farmEdit(farmId));
              ref.invalidate(farmDetailProvider(farmId));
            },
          ),
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == 'delete') await _confirmDelete(context, ref);
            },
            itemBuilder: (_) => const [PopupMenuItem(value: 'delete', child: Text('حذف باغ'))],
          ),
        ],
      ),
      body: farm.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(farmDetailProvider(farmId))),
        data: (f) => _FarmBody(farm: f),
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('حذف باغ'),
        content: const Text('باغ حذف می‌شود اما تاریخچه تحلیل‌های قبلی حفظ می‌شود. ادامه می‌دهید؟'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger, minimumSize: const Size(0, 44)),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('حذف'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(farmRepositoryProvider).delete(farmId);
      ref.invalidate(farmsListProvider);
      if (context.mounted) context.pop();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
      }
    }
  }
}

class _FarmBody extends ConsumerWidget {
  const _FarmBody({required this.farm});

  final Farm farm;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trees = ref.watch(farmTreesProvider(farm.id));
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      children: [
        PestinoCard(
          color: AppColors.green700,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.park_rounded, color: Colors.white, size: 36),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(farm.name, style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w800)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text('${farm.province}، ${farm.city}', style: TextStyle(color: Colors.white.withValues(alpha: 0.9))),
            ],
          ),
        ),
        const SizedBox(height: 16),
        PestinoCard(
          child: Column(
            children: [
              _InfoRow(label: 'رقم پسته', value: farm.pistachioVariety ?? '—'),
              _InfoRow(label: 'مساحت', value: farm.areaHectares == null ? '—' : '${Persian.number(farm.areaHectares!, decimals: 1)} هکتار'),
              _InfoRow(label: 'میانگین سن درخت', value: farm.averageTreeAge == null ? '—' : '${Persian.digits(farm.averageTreeAge!)} سال'),
              _InfoRow(label: 'روش آبیاری', value: Persian.irrigation(farm.irrigationMethod)),
              _InfoRow(label: 'نوع خاک', value: farm.soilType ?? '—'),
              if (farm.soilNotes != null && farm.soilNotes!.isNotEmpty) _InfoRow(label: 'یادداشت خاک', value: farm.soilNotes!),
            ],
          ),
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: () => context.push(AppRoutes.analysisForFarm(farm.id)),
          icon: const Icon(Icons.center_focus_strong_rounded),
          label: const Text('تحلیل تصویر برای این باغ'),
        ),
        const SizedBox(height: 24),
        SectionTitle(
          'درختان ثبت‌شده',
          action: 'افزودن درخت',
          onAction: () => _addTree(context, ref),
        ),
        const SizedBox(height: 8),
        trees.when(
          loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
          error: (e, _) => ErrorView(error: e),
          data: (items) {
            if (items.isEmpty) {
              return PestinoCard(
                child: Text(
                  'درختی ثبت نشده است. اختیاری است؛ برای پیگیری دقیق‌تر درختان مشکل‌دار می‌توانید آن‌ها را ثبت کنید.',
                  style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft),
                ),
              );
            }
            return Column(
              children: [
                for (final t in items)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: PestinoCard(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      child: Row(
                        children: [
                          const Icon(Icons.nature_rounded, color: AppColors.green600),
                          const SizedBox(width: 12),
                          Expanded(child: Text(t.label, style: const TextStyle(fontWeight: FontWeight.w700))),
                          if (t.plantedYear != null) Text('کاشت ${Persian.digits(t.plantedYear!)}', style: theme.textTheme.bodySmall),
                          IconButton(
                            tooltip: 'حذف',
                            icon: const Icon(Icons.delete_outline_rounded, color: AppColors.inkSoft),
                            onPressed: () async {
                              await ref.read(farmRepositoryProvider).removeTree(farm.id, t.id);
                              ref.invalidate(farmTreesProvider(farm.id));
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }

  Future<void> _addTree(BuildContext context, WidgetRef ref) async {
    final label = TextEditingController();
    final year = TextEditingController();
    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('افزودن درخت'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: label, decoration: const InputDecoration(labelText: 'نام یا شماره درخت')),
            const SizedBox(height: 12),
            TextField(
              controller: year,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'سال کاشت (اختیاری)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('ثبت')),
        ],
      ),
    );
    if (saved == true && label.text.trim().isNotEmpty) {
      try {
        await ref.read(farmRepositoryProvider).addTree(
              farm.id,
              label: label.text.trim(),
              plantedYear: int.tryParse(Persian.toAscii(year.text.trim())),
            );
        ref.invalidate(farmTreesProvider(farm.id));
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
        }
      }
    }
    label.dispose();
    year.dispose();
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 130, child: Text(label, style: const TextStyle(color: AppColors.inkSoft))),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w600))),
        ],
      ),
    );
  }
}
