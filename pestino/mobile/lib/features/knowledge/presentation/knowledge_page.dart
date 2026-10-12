import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/knowledge_entities.dart';
import 'knowledge_providers.dart';

class KnowledgePage extends ConsumerStatefulWidget {
  const KnowledgePage({super.key});

  @override
  ConsumerState<KnowledgePage> createState() => _KnowledgePageState();
}

class _KnowledgePageState extends ConsumerState<KnowledgePage> {
  static const kinds = <String?, String>{
    null: 'همه',
    'pest': 'آفات',
    'disease': 'بیماری‌ها',
    'nutrient': 'تغذیه',
    'environmental': 'تنش‌های محیطی',
  };

  String? _kind;
  final _search = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final list = ref.watch(knowledgeListProvider((kind: _kind, query: _query.isEmpty ? null : _query)));
    return Scaffold(
      appBar: AppBar(title: const Text('دانش کشاورزی پسته')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              controller: _search,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: 'جستجو: شپشک، صمغ، کمبود آهن ...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () {
                          _search.clear();
                          setState(() => _query = '');
                        },
                      ),
              ),
              onSubmitted: (v) => setState(() => _query = v.trim()),
            ),
          ),
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                for (final e in kinds.entries)
                  Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: ChoiceChip(
                      label: Text(e.value),
                      selected: _kind == e.key,
                      onSelected: (_) => setState(() => _kind = e.key),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: list.when(
              loading: () => const LoadingView(),
              error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(knowledgeListProvider)),
              data: (items) {
                if (items.isEmpty) {
                  return const EmptyState(icon: Icons.search_off_rounded, title: 'موردی پیدا نشد');
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, i) => _ArticleCard(item: items[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ArticleCard extends StatelessWidget {
  const _ArticleCard({required this.item});

  final KnowledgeSummary item;

  static const _kindLabel = {
    'pest': ('آفت', AppColors.earth500),
    'disease': ('بیماری', AppColors.danger),
    'nutrient': ('تغذیه', AppColors.green600),
    'environmental': ('تنش محیطی', AppColors.info),
  };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (label, color) = _kindLabel[item.kind] ?? ('دانش', AppColors.green700);
    return PestinoCard(
      onTap: () => context.push(AppRoutes.article(item.slug)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              StatusChip(label: label, color: color),
              const Spacer(),
              Text(item.titleEn, style: theme.textTheme.labelSmall?.copyWith(color: AppColors.inkSoft)),
            ],
          ),
          const SizedBox(height: 10),
          Text(item.titleFa, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(item.summaryFa, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: AppColors.inkSoft, height: 1.7)),
        ],
      ),
    );
  }
}
