import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/subscription_entities.dart';
import 'subscription_providers.dart';

class PaywallPage extends ConsumerWidget {
  const PaywallPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plans = ref.watch(plansProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('طرح‌های پستینو')),
      body: plans.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(plansProvider)),
        data: (items) {
          final premium = items.firstWhere((p) => p.code == 'premium', orElse: () => items.first);
          final free = items.firstWhere((p) => p.code == 'free', orElse: () => items.first);
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
            children: [
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [AppColors.earth500, AppColors.earth700]),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.workspace_premium_rounded, color: Colors.white, size: 40),
                    SizedBox(height: 12),
                    Text('مدیریت حرفه‌ای باغ', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
                    SizedBox(height: 6),
                    Text(
                      'تحلیل نامحدود، باغ‌های بیشتر، گزارش‌های پیشرفته و خروجی PDF برای ثبت در پرونده باغ.',
                      style: TextStyle(color: Colors.white, height: 1.7),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              _PlanCard(plan: free, highlighted: false),
              const SizedBox(height: 12),
              _PlanCard(plan: premium, highlighted: true),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () async {
                  try {
                    await ref.read(subscriptionRepositoryProvider).checkout('premium');
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
                    }
                  }
                },
                child: const Text('فعال‌سازی طرح حرفه‌ای'),
              ),
              const SizedBox(height: 10),
              const Text(
                'پرداخت از طریق درگاه امن یا خرید درون‌برنامه‌ای (کافه‌بازار، مایکت، گوگل‌پلی یا اپ‌استور) انجام می‌شود.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.inkSoft, fontSize: 12, height: 1.6),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({required this.plan, required this.highlighted});

  final PlanInfo plan;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: highlighted ? AppColors.earth500 : AppColors.outline, width: highlighted ? 2 : 1),
      ),
      child: PestinoCard(
        color: highlighted ? AppColors.earth100 : null,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(plan.nameFa, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                const Spacer(),
                if (highlighted) const StatusChip(label: 'پیشنهادی', color: AppColors.earth700),
              ],
            ),
            const SizedBox(height: 12),
            _Feature(
              text: plan.monthlyAnalyses == null
                  ? 'تحلیل تصویر نامحدود'
                  : '${Persian.digits(plan.monthlyAnalyses!)} تحلیل تصویر در ماه',
            ),
            _Feature(text: plan.maxFarms == null ? 'باغ نامحدود' : '${Persian.digits(plan.maxFarms!)} باغ'),
            _Feature(text: 'گزارش پیشرفته', enabled: plan.advancedReports),
            _Feature(text: 'خروجی PDF از گزارش', enabled: plan.pdfExport),
          ],
        ),
      ),
    );
  }
}

class _Feature extends StatelessWidget {
  const _Feature({required this.text, this.enabled = true});

  final String text;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(enabled ? Icons.check_circle_rounded : Icons.cancel_rounded, size: 20, color: enabled ? AppColors.success : AppColors.inkSoft),
          const SizedBox(width: 10),
          Expanded(child: Text(text, style: TextStyle(color: enabled ? AppColors.ink : AppColors.inkSoft))),
        ],
      ),
    );
  }
}
