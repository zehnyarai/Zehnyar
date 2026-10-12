import 'analysis_entities.dart';

abstract interface class AnalysisRepository {
  Future<AnalysisUsage> usage();

  /// Returns one page of summaries. Pass the previous page's [AnalysisPage.nextCursor] to continue.
  Future<AnalysisPage> list({String? cursor, String? farmId, int limit = 20});

  Future<Analysis> get(String id);

  /// Uploads the image and runs the AI analysis. Can take up to ~30 seconds.
  Future<Analysis> create(NewAnalysisInput input);

  Future<void> delete(String id);
}

class AnalysisPage {
  const AnalysisPage({required this.items, this.nextCursor});

  final List<AnalysisSummary> items;
  final String? nextCursor;
}
