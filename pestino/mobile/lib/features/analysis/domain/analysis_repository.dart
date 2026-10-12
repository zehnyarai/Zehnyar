import 'analysis_entities.dart';

abstract interface class AnalysisRepository {
  Future<AnalysisUsage> usage();

  /// Returns one page of summaries. Pass the previous page's [AnalysisListPage.nextCursor] to continue.
  Future<AnalysisListPage> list({String? cursor, String? farmId, int limit = 20});

  Future<Analysis> get(String id);

  /// Uploads the image and runs the AI analysis. Can take up to ~30 seconds.
  Future<Analysis> create(NewAnalysisInput input);

  Future<void> delete(String id);
}

class AnalysisListPage {
  const AnalysisListPage({required this.items, this.nextCursor});

  final List<AnalysisSummary> items;
  final String? nextCursor;
}
