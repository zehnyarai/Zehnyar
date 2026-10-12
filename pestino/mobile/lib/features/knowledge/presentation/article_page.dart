import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/knowledge_entities.dart';
import 'knowledge_providers.dart';

class ArticlePage extends ConsumerWidget {
  const ArticlePage({super.key, required this.slug});

  final String slug;

  static const _attributeLabels = {
    'scientificName': 'نام علمی',
    'damageType': 'نوع خسارت',
    'monitoringMethod': 'روش پایش',
    'pathogen': 'عامل بیماری‌زا',
    'pathogenType': 'نوع عامل',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final article = ref.watch(knowledgeArticleProvider(slug));
    return Scaffold(
      appBar: AppBar(title: const Text('دانش کشاورزی')),
      body: article.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(knowledgeArticleProvider(slug))),
        data: (a) => _ArticleBody(article: a),
      ),
    );
  }
}

class _ArticleBody extends StatelessWidget {
  const _ArticleBody({required this.article});

  final KnowledgeArticle article;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final s = article.summary;
    final attrs = article.attributes.entries.where((e) => e.value != null && e.value!.isNotEmpty).toList();

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
      children: [
        Text(s.titleFa, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 4),
        Text(s.titleEn, style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft)),
        const SizedBox(height: 16),
        PestinoCard(child: Text(s.summaryFa, style: const TextStyle(height: 1.9, fontSize: 15))),
        if (attrs.isNotEmpty) ...[
          const SizedBox(height: 12),
          PestinoCard(
            color: AppColors.green50,
            child: Column(
              children: [
                for (final e in attrs)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          width: 110,
                          child: Text(ArticlePage._attributeLabels[e.key] ?? e.key, style: const TextStyle(color: AppColors.inkSoft)),
                        ),
                        Expanded(child: Text(e.value!, style: const TextStyle(fontWeight: FontWeight.w700, height: 1.6))),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 20),
        _Section(title: 'علائم و نشانه‌ها', items: article.symptoms, icon: Icons.visibility_rounded),
        _Section(title: 'علل و عوامل مستعد‌کننده', items: article.causes, icon: Icons.warning_amber_rounded),
        _Section(title: 'اصول مدیریت', items: article.management, icon: Icons.shield_rounded, numbered: true),
        const SizedBox(height: 8),
        PestinoCard(
          color: AppColors.earth100,
          child: const Text(
            'اطلاعات این بخش برای آگاهی عمومی است. انتخاب سم، دوز و زمان‌بندی مصرف را فقط با نظر کارشناس گیاه‌پزشکی انجام دهید.',
            style: TextStyle(color: AppColors.earth700, height: 1.8, fontSize: 13),
          ),
        ),
        if (article.references.isNotEmpty) ...[
          const SizedBox(height: 20),
          Text('منابع علمی', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          for (final r in article.references)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: PestinoCard(
                padding: const EdgeInsets.all(14),
                child: Text(r.citation, style: const TextStyle(fontSize: 13, height: 1.7)),
              ),
            ),
        ],
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.items, required this.icon, this.numbered = false});

  final String title;
  final List<String> items;
  final IconData icon;
  final bool numbered;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: PestinoCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.green700, size: 20),
                const SizedBox(width: 8),
                Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
              ],
            ),
            const SizedBox(height: 10),
            for (var i = 0; i < items.length; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    numbered
                        ? Text('${i + 1}. ', style: const TextStyle(color: AppColors.green700, fontWeight: FontWeight.w800))
                        : const Text('• ', style: TextStyle(color: AppColors.green700, fontWeight: FontWeight.w900)),
                    Expanded(child: Text(items[i], style: const TextStyle(height: 1.7))),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
