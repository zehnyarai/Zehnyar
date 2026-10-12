import 'knowledge_entities.dart';

abstract interface class KnowledgeRepository {
  Future<List<KnowledgeSummary>> list({String? kind, String? query});
  Future<KnowledgeArticle> get(String slug);
}
