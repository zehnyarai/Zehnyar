import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../../analysis/domain/analysis_entities.dart';
import '../../analysis/presentation/analysis_providers.dart';
import '../../auth/presentation/auth_controller.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final usage = ref.watch(analysisUsageProvider);
    final history = ref.watch(historyProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('سلام، ${user?.displayName ?? ''}'),
        actions: [
          IconButton(
            tooltip: 'طرح اشتراک',
            icon: const Icon(Icons.workspace_premium_rounded),
            onPressed: () => context.push(AppRoutes.paywall),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(analysisUsageProvider);
          ref.invalidate(historyProvider);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
          children: [
            Text(Persian.dateLong(DateTime.now()), style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft)),
            const SizedBox(height: 14),
            _HeroAnalyzeCard(onTap: () => context.push(AppRoutes.analysis)),
            const SizedBox(height: 14),
            usage.when(
              loading: () => const SizedBox(height: 72, child: Center(child: CircularProgressIndicator())),
              error: (e, _) => const SizedBox.shrink(),
              data: (u) => _UsageCard(
                planName: u.planName,
                isUnlimited: u.isUnlimited,
                used: u.used,
                limit: u.monthlyLimit,
                onTap: () => context.push(AppRoutes.paywall),
              ),
            ),
            const SizedBox(height: 22),
            const SectionTitle('دسترسی سریع'),
            const SizedBox(height: 10),
            LayoutBuilder(
              builder: (context, constraints) {
                final cols = constraints.maxWidth > 600 ? 4 : 2;
                return GridView.count(
                  crossAxisCount: cols,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1.15,
                  children: [
                    _QuickCard(
                      icon: Icons.center_focus_strong_rounded,
                      title: 'تحلیل تصویر',
                      subtitle: 'برگ، خوشه، تنه، آفت، خاک',
                      color: AppColors.green700,
                      onTap: () => context.push(AppRoutes.analysis),
                    ),
                    _QuickCard(
                      icon: Icons.agriculture_rounded,
                      title: 'مزرعه‌های من',
                      subtitle: 'مدیریت باغ‌ها و درختان',
                      color: AppColors.earth500,
                      onTap: () => context.go(AppRoutes.farms),
                    ),
                    _QuickCard(
                      icon: Icons.assessment_rounded,
                      title: 'گزارش‌ها',
                      subtitle: 'تاریخچه تحلیل‌ها',
                      color: AppColors.info,
                      onTap: () => context.go(AppRoutes.history),
                    ),
                    _QuickCard(
                      icon: Icons.menu_book_rounded,
                      title: 'دانش کشاورزی',
                      subtitle: 'آفات، بیماری‌ها، تغذیه',
                      color: AppColors.green500,
                      onTap: () => context.push(AppRoutes.knowledge),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 22),
            const SectionTitle('توصیه‌های این فصل'),
            const SizedBox(height: 10),
            _SeasonTipsCard(season: _seasonOf(DateTime.now())),
            const SizedBox(height: 22),
            SectionTitle('آخرین تحلیل‌ها', action: 'همه', onAction: () => context.go(AppRoutes.history)),
            const SizedBox(height: 10),
            history.when(
              loading: () => const LinearProgressIndicator(),
              error: (_, __) => const SizedBox.shrink(),
              data: (state) {
                final recent = state.items.take(3).toList();
                if (recent.isEmpty) {
                  return PestinoCard(
                    child: Text(
                      'هنوز تحلیلی ندارید. با گرفتن اولین عکس از برگ یا تنه درخت شروع کنید.',
                      style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft),
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final a in recent)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _RecentTile(item: a),
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  static String _seasonOf(DateTime now) {
    final m = Persian.toJalali(now)[1];
    if (m <= 3) return 'spring';
    if (m <= 6) return 'summer';
    if (m <= 9) return 'autumn';
    return 'winter';
  }
}

class _HeroAnalyzeCard extends StatelessWidget {
  const _HeroAnalyzeCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(24),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [AppColors.green600, AppColors.green900], begin: Alignment.topRight, end: Alignment.bottomLeft),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('باغ خود را عکس بگیرید', style: theme.textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  Text(
                    'تشخیص آفت، بیماری و کمبود عناصر با هوش مصنوعی و منابع علمی',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.9), height: 1.6),
                  ),
                  const SizedBox(height: 14),
                  const Chip(
                    avatar: Icon(Icons.auto_awesome_rounded, size: 18),
                    label: Text('شروع تحلیل'),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), shape: BoxShape.circle),
              child: const Icon(Icons.photo_camera_rounded, color: Colors.white, size: 40),
            ),
          ],
        ),
      ),
    );
  }
}

class _UsageCard extends StatelessWidget {
  const _UsageCard({required this.planName, required this.isUnlimited, required this.used, this.limit, required this.onTap});

  final String planName;
  final bool isUnlimited;
  final int used;
  final int? limit;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final progress = (isUnlimited || limit == null || limit == 0) ? 1.0 : (used / limit!).clamp(0.0, 1.0);
    final text = isUnlimited
        ? 'تحلیل نامحدود'
        : '${Persian.digits(used)} از ${Persian.digits(limit!)} تحلیل این ماه';
    return PestinoCard(
      onTap: onTap,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('طرح $planName', style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text(text, style: const TextStyle(color: AppColors.inkSoft)),
                if (!isUnlimited) ...[
                  const SizedBox(height: 10),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(value: progress, minHeight: 8, backgroundColor: AppColors.outline),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 12),
          Icon(isUnlimited ? Icons.all_inclusive_rounded : Icons.chevron_left_rounded, color: AppColors.green700),
        ],
      ),
    );
  }
}

class _QuickCard extends StatelessWidget {
  const _QuickCard({required this.icon, required this.title, required this.subtitle, required this.color, required this.onTap});

  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return PestinoCard(
      onTap: onTap,
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
            child: Icon(icon, color: color),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
              const SizedBox(height: 2),
              Text(subtitle, style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft), maxLines: 2),
            ],
          ),
        ],
      ),
    );
  }
}

class _SeasonTipsCard extends StatelessWidget {
  const _SeasonTipsCard({required this.season});

  final String season;

  static const _tips = {
    'spring': [
      'پایش شپشک پسته روی برگ‌ها و زیر برگ از اوایل بهار',
      'بازرسی یخبندان دیررس و پیش‌بینی هوا قبل از باز شدن جوانه‌ها',
      'بررسی زخم و صمغ روی تنه برای بیماری گامیوزیس',
    ],
    'summer': [
      'آبیاری منظم و متناسب با نیاز درخت؛ جلوگیری از تنش خشکی',
      'بازرسی کنه‌ها زیر برگ‌ها در هوای گرم و خشک',
      'کنترل علف‌های هرز حاشیه باغ',
    ],
    'autumn': [
      'جمع‌آوری و خارج کردن بقایای آلوده و برگ‌های ریخته‌شده',
      'بررسی خوشه‌ها و میوه‌ها برای آفات و آلودگی قارچی',
      'برنامه‌ریزی تغذیه و آزمون خاک برای فصل بعد',
    ],
    'winter': [
      'هرس زمستانه برای تهویه و نور بهتر تاج درخت',
      'زهکشی مناسب باغ و پرهیز از ماندگی آب در اطراف طوقه',
      'آزمون خاک و آب برای برنامه‌ریزی کوددهی و شوری',
    ],
  };

  @override
  Widget build(BuildContext context) {
    final tips = _tips[season] ?? _tips['spring']!;
    return PestinoCard(
      color: AppColors.green50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final t in tips)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.spa_rounded, size: 18, color: AppColors.green600),
                  const SizedBox(width: 10),
                  Expanded(child: Text(t, style: const TextStyle(height: 1.6))),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _RecentTile extends StatelessWidget {
  const _RecentTile({required this.item});

  final AnalysisSummary item;

  @override
  Widget build(BuildContext context) {
    final done = item.isCompleted;
    return PestinoCard(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      onTap: done ? () => context.push(AppRoutes.report(item.id)) : null,
      child: Row(
        children: [
          Icon(done ? Icons.check_circle_rounded : Icons.info_rounded, color: done ? AppColors.success : AppColors.warning),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              item.primaryTitle ?? (done ? 'نتیجه تحلیل' : 'تحلیل ناموفق'),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
          if (item.confidence != null) Text(Persian.percent(item.confidence!), style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}
