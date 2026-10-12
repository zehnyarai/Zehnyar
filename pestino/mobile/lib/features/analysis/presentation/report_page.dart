import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/analysis_entities.dart';
import 'analysis_providers.dart';

/// AI report page. Shows [initial] immediately when available (just after analysis),
/// otherwise loads the analysis by id.
class ReportPage extends ConsumerWidget {
  const ReportPage({super.key, required this.analysisId, this.initial});

  final String analysisId;
  final Analysis? initial;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('گزارش تحلیل'),
        actions: [
          IconButton(
            tooltip: 'حذف',
            icon: const Icon(Icons.delete_outline_rounded),
            onPressed: () => _delete(context, ref),
          ),
        ],
      ),
      body: initial != null
          ? _ReportBody(analysis: initial!)
          : ref.watch(analysisDetailProvider(analysisId)).when(
                loading: () => const LoadingView(message: 'در حال بارگذاری گزارش…'),
                error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(analysisDetailProvider(analysisId))),
                data: (a) => _ReportBody(analysis: a),
              ),
      backgroundColor: theme.scaffoldBackgroundColor,
    );
  }

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('حذف گزارش'),
        content: const Text('این گزارش از تاریخچه شما حذف می‌شود.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('حذف')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(analysisRepositoryProvider).delete(analysisId);
      ref.invalidate(historyProvider);
      if (context.mounted) context.pop();
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
      }
    }
  }
}

class _ReportBody extends StatelessWidget {
  const _ReportBody({required this.analysis});

  final Analysis analysis;

  @override
  Widget build(BuildContext context) {
    final s = analysis.summary;
    if (s.status == 'failed') {
      return EmptyState(
        icon: Icons.cloud_off_rounded,
        title: 'تحلیل انجام نشد',
        message: s.errorMessage ?? 'دوباره تلاش کنید. این تحلیل از سهمیه شما کم نشده است.',
        actionLabel: 'تحلیل جدید',
        onAction: () => context.pushReplacement(AppRoutes.analysis),
      );
    }
    final r = analysis.report;
    if (r == null) {
      return const LoadingView(message: 'گزارش در حال آماده‌سازی است…');
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      children: [
        _HeroCard(report: r, summary: s),
        const SizedBox(height: 16),
        if (!r.imageUsable) ...[
          _WarningCard(
            title: 'کیفیت تصویر برای تشخیص کافی نیست',
            items: r.imageIssues,
          ),
          const SizedBox(height: 16),
        ],
        if (r.observedSymptoms.isNotEmpty) ...[
          const _Heading('نشانه‌های مشاهده‌شده', icon: Icons.visibility_rounded),
          PestinoCard(
            child: Column(
              children: [
                for (final sym in r.observedSymptoms)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.check_circle_rounded, size: 20, color: AppColors.success),
                        const SizedBox(width: 10),
                        Expanded(child: Text(sym, style: const TextStyle(height: 1.6))),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        if (r.summary.isNotEmpty) ...[
          const _Heading('خلاصه تحلیل', icon: Icons.notes_rounded),
          PestinoCard(child: Text(r.summary, style: const TextStyle(height: 1.8))),
          const SizedBox(height: 16),
        ],
        if (r.actions.isNotEmpty) ...[
          const _Heading('اقدامات پیشنهادی', icon: Icons.checklist_rounded),
          for (final a in r.actions) _ActionTile(action: a),
          const SizedBox(height: 16),
        ],
        if (r.alternatives.isNotEmpty) ...[
          const _Heading('سایر احتمالات', icon: Icons.compare_arrows_rounded),
          for (final alt in r.alternatives) _AlternativeTile(alt: alt),
          const SizedBox(height: 16),
        ],
        if (r.additionalInfoNeeded.isNotEmpty) ...[
          _InfoNeededCard(items: r.additionalInfoNeeded, analysisFarmId: s.farmId),
          const SizedBox(height: 16),
        ],
        if (r.knowledgeSlug != null) ...[
          FilledButton.tonalIcon(
            onPressed: () => context.push(AppRoutes.article(r.knowledgeSlug!)),
            icon: const Icon(Icons.menu_book_rounded),
            label: const Text('مطالعه کامل در دانش کشاورزی'),
          ),
          const SizedBox(height: 16),
        ],
        if (r.references.isNotEmpty) ...[
          const _Heading('منابع علمی', icon: Icons.school_rounded),
          PestinoCard(
            child: Column(
              children: [
                for (final reference in r.references)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.menu_book_outlined, size: 18, color: AppColors.earth500),
                        const SizedBox(width: 10),
                        Expanded(child: Text(reference.citation, style: const TextStyle(fontSize: 13, height: 1.6))),
                        if (!reference.verified)
                          const Padding(
                            padding: EdgeInsets.only(right: 6),
                            child: StatusChip(label: 'در انتظار بازبینی', color: AppColors.warning),
                          ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        PestinoCard(
          color: AppColors.earth100,
          child: Text(
            r.disclaimer,
            style: const TextStyle(color: AppColors.earth700, fontSize: 12.5, height: 1.8),
          ),
        ),
      ],
    );
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({required this.report, required this.summary});

  final AnalysisReport report;
  final AnalysisSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final headline = report.isHealthy ? 'وضعیت سالم' : 'احتمال مشکل';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.green700, AppColors.green900],
          begin: Alignment.topRight,
          end: Alignment.bottomLeft,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [BoxShadow(color: AppColors.green900.withValues(alpha: 0.25), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _HeroChip(label: Persian.category(summary.category)),
              _HeroChip(label: Persian.season(summary.season)),
              _HeroChip(label: Persian.dateLong(summary.createdAt)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(headline, style: theme.textTheme.labelLarge?.copyWith(color: Colors.white70)),
                    const SizedBox(height: 4),
                    Text(
                      report.diagnosisTitle,
                      style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w800, height: 1.4),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'تشخیص: ${report.detectedSubject}',
                      style: TextStyle(color: Colors.white.withValues(alpha: 0.85), fontSize: 13),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.all(6),
                decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                child: ConfidenceRing(value: report.confidence, size: 96),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroChip extends StatelessWidget {
  const _HeroChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading(this.text, {required this.icon});

  final String text;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, top: 4),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppColors.green700),
          const SizedBox(width: 8),
          Text(text, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({required this.action});

  final ReportAction action;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (action.priority) {
      'immediate' => ('فوری', AppColors.danger),
      'monitor' => ('پایش', AppColors.info),
      _ => ('به‌زودی', AppColors.warning),
    };
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: PestinoCard(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 4,
              height: 44,
              decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(4)),
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(action.text, style: const TextStyle(height: 1.7))),
            const SizedBox(width: 8),
            StatusChip(label: label, color: color),
          ],
        ),
      ),
    );
  }
}

class _AlternativeTile extends StatelessWidget {
  const _AlternativeTile({required this.alt});

  final ReportAlternative alt;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.confidence(alt.confidence);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: PestinoCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(alt.title, style: const TextStyle(fontWeight: FontWeight.w800))),
                Text(Persian.percent(alt.confidence), style: TextStyle(color: color, fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: alt.confidence / 100,
                minHeight: 8,
                color: color,
                backgroundColor: AppColors.outline,
              ),
            ),
            if (alt.reason.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(alt.reason, style: const TextStyle(color: AppColors.inkSoft, height: 1.6, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }
}

class _WarningCard extends StatelessWidget {
  const _WarningCard({required this.title, required this.items});

  final String title;
  final List<String> items;

  @override
  Widget build(BuildContext context) {
    return PestinoCard(
      color: const Color(0xFFFFF4E0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: AppColors.warning),
              const SizedBox(width: 8),
              Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.warning))),
            ],
          ),
          for (final i in items) Padding(padding: const EdgeInsets.only(top: 6), child: Text('• $i')),
        ],
      ),
    );
  }
}

class _InfoNeededCard extends StatelessWidget {
  const _InfoNeededCard({required this.items, this.analysisFarmId});

  final List<String> items;
  final String? analysisFarmId;

  @override
  Widget build(BuildContext context) {
    return PestinoCard(
      color: AppColors.green50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.add_a_photo_rounded, color: AppColors.green700),
              SizedBox(width: 8),
              Text('برای تشخیص دقیق‌تر، این موارد را بفرستید', style: TextStyle(fontWeight: FontWeight.w800)),
            ],
          ),
          const SizedBox(height: 10),
          for (final i in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('✓ ', style: TextStyle(color: AppColors.green700, fontWeight: FontWeight.w900)),
                  Expanded(child: Text(i, style: const TextStyle(height: 1.6))),
                ],
              ),
            ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => context.push(
              analysisFarmId == null ? AppRoutes.analysis : AppRoutes.analysisForFarm(analysisFarmId!),
            ),
            icon: const Icon(Icons.photo_camera_rounded),
            label: const Text('ثبت تحلیل تکمیلی'),
          ),
        ],
      ),
    );
  }
}
