class AnalysisSummary {
  const AnalysisSummary({
    required this.id,
    required this.status,
    required this.category,
    required this.season,
    required this.createdAt,
    this.farmId,
    this.primaryTitle,
    this.confidence,
    this.errorMessage,
  });

  final String id;
  final String status; // pending | completed | failed
  final String category;
  final String season;
  final DateTime createdAt;
  final String? farmId;
  final String? primaryTitle;
  final int? confidence;
  final String? errorMessage;

  bool get isCompleted => status == 'completed';

  factory AnalysisSummary.fromJson(Map<String, dynamic> json) => AnalysisSummary(
        id: json['id'] as String,
        status: json['status'] as String,
        category: json['category'] as String,
        season: json['season'] as String,
        createdAt: DateTime.parse(json['createdAt'] as String),
        farmId: json['farmId'] as String?,
        primaryTitle: json['primaryTitle'] as String?,
        confidence: (json['confidence'] as num?)?.toInt(),
        errorMessage: json['errorMessage'] as String?,
      );
}

class Analysis {
  const Analysis({required this.summary, this.report});

  final AnalysisSummary summary;
  final AnalysisReport? report;

  factory Analysis.fromJson(Map<String, dynamic> json) {
    final reportJson = json['report'] as Map<String, dynamic>?;
    return Analysis(
      summary: AnalysisSummary.fromJson(json),
      report: reportJson == null ? null : AnalysisReport.fromJson(reportJson),
    );
  }
}

class AnalysisReport {
  const AnalysisReport({
    required this.summary,
    required this.detectedSubject,
    required this.imageUsable,
    required this.imageIssues,
    required this.diagnosisTitle,
    required this.knowledgeSlug,
    required this.isHealthy,
    required this.confidence,
    required this.observedSymptoms,
    required this.alternatives,
    required this.actions,
    required this.additionalInfoNeeded,
    required this.references,
    required this.disclaimer,
  });

  final String summary;
  final String detectedSubject;
  final bool imageUsable;
  final List<String> imageIssues;
  final String diagnosisTitle;
  final String? knowledgeSlug;
  final bool isHealthy;
  final int confidence;
  final List<String> observedSymptoms;
  final List<ReportAlternative> alternatives;
  final List<ReportAction> actions;
  final List<String> additionalInfoNeeded;
  final List<ReportReference> references;
  final String disclaimer;

  static List<String> _strings(Object? v) => (v as List? ?? const []).map((e) => e.toString()).toList();

  factory AnalysisReport.fromJson(Map<String, dynamic> json) {
    final q = (json['imageQuality'] as Map?) ?? const {};
    final d = (json['diagnosis'] as Map?) ?? const {};
    return AnalysisReport(
      summary: json['summary'] as String? ?? '',
      detectedSubject: json['detectedSubject'] as String? ?? '',
      imageUsable: q['usable'] as bool? ?? true,
      imageIssues: _strings(q['issues']),
      diagnosisTitle: d['title'] as String? ?? 'نامشخص',
      knowledgeSlug: d['knowledgeSlug'] as String?,
      isHealthy: d['isHealthy'] as bool? ?? false,
      confidence: (d['confidence'] as num? ?? 0).round(),
      observedSymptoms: _strings(json['observedSymptoms']),
      alternatives: (json['alternatives'] as List? ?? const [])
          .map((e) => ReportAlternative.fromJson(e as Map<String, dynamic>))
          .toList(),
      actions: (json['recommendedActions'] as List? ?? const [])
          .map((e) => ReportAction.fromJson(e as Map<String, dynamic>))
          .toList(),
      additionalInfoNeeded: _strings(json['additionalInfoNeeded']),
      references: (json['references'] as List? ?? const [])
          .map((e) => ReportReference.fromJson(e as Map<String, dynamic>))
          .toList(),
      disclaimer: json['disclaimer'] as String? ?? '',
    );
  }
}

class ReportAlternative {
  const ReportAlternative({required this.title, required this.confidence, required this.reason});

  final String title;
  final int confidence;
  final String reason;

  factory ReportAlternative.fromJson(Map<String, dynamic> json) => ReportAlternative(
        title: json['title'] as String,
        confidence: (json['confidence'] as num).round(),
        reason: json['reason'] as String? ?? '',
      );
}

class ReportAction {
  const ReportAction({required this.text, required this.priority});

  final String text;

  /// immediate | soon | monitor
  final String priority;

  factory ReportAction.fromJson(Map<String, dynamic> json) => ReportAction(
        text: json['text'] as String,
        priority: json['priority'] as String? ?? 'soon',
      );
}

class ReportReference {
  const ReportReference({required this.citation, this.url, this.year, this.verified = false});

  final String citation;
  final String? url;
  final int? year;
  final bool verified;

  factory ReportReference.fromJson(Map<String, dynamic> json) => ReportReference(
        citation: json['citation'] as String,
        url: json['url'] as String?,
        year: (json['year'] as num?)?.toInt(),
        verified: json['verified'] as bool? ?? false,
      );
}

class AnalysisUsage {
  const AnalysisUsage({
    required this.plan,
    required this.planName,
    required this.used,
    this.monthlyLimit,
    this.remaining,
  });

  final String plan;
  final String planName;
  final int used;

  /// null = unlimited
  final int? monthlyLimit;
  final int? remaining;

  bool get isUnlimited => monthlyLimit == null;
  bool get exhausted => !isUnlimited && (remaining ?? 0) <= 0;

  factory AnalysisUsage.fromJson(Map<String, dynamic> json) => AnalysisUsage(
        plan: json['plan'] as String,
        planName: json['planName'] as String,
        used: (json['used'] as num).toInt(),
        monthlyLimit: (json['monthlyLimit'] as num?)?.toInt(),
        remaining: (json['remaining'] as num?)?.toInt(),
      );
}

class NewAnalysisInput {
  const NewAnalysisInput({
    required this.filePath,
    required this.category,
    required this.season,
    this.farmId,
    this.treeAgeYears,
    this.location,
    this.userNotes,
  });

  final String filePath;
  final String category;
  final String season;
  final String? farmId;
  final int? treeAgeYears;
  final String? location;
  final String? userNotes;
}
