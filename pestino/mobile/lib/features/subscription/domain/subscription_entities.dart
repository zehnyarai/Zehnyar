class PlanInfo {
  const PlanInfo({
    required this.code,
    required this.nameFa,
    required this.monthlyAnalyses,
    required this.maxFarms,
    required this.advancedReports,
    required this.pdfExport,
  });

  final String code;
  final String nameFa;

  /// null = unlimited
  final int? monthlyAnalyses;

  /// null = unlimited
  final int? maxFarms;
  final bool advancedReports;
  final bool pdfExport;

  factory PlanInfo.fromJson(Map<String, dynamic> json) => PlanInfo(
        code: json['code'] as String,
        nameFa: json['nameFa'] as String,
        monthlyAnalyses: (json['monthlyAnalyses'] as num?)?.toInt(),
        maxFarms: (json['maxFarms'] as num?)?.toInt(),
        advancedReports: json['advancedReports'] as bool? ?? false,
        pdfExport: json['pdfExport'] as bool? ?? false,
      );
}
