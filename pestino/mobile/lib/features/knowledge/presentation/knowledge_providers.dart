import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../domain/knowledge_entities.dart';

typedef KnowledgeQuery = ({String? kind, String? query});

final knowledgeListProvider = FutureProvider.autoDispose.family<List<KnowledgeSummary>, KnowledgeQuery>((ref, q) {
  return ref.watch(knowledgeRepositoryProvider).list(kind: q.kind, query: q.query);
});

final knowledgeArticleProvider = FutureProvider.autoDispose.family<KnowledgeArticle, String>((ref, slug) {
  return ref.watch(knowledgeRepositoryProvider).get(slug);
});
