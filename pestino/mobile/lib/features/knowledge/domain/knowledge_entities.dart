class KnowledgeSummary {
  const KnowledgeSummary({required this.slug, required this.kind, required this.titleFa, required this.titleEn, required this.summaryFa});

  final String slug;
  final String kind; // pest | disease | nutrient | environmental
  final String titleFa;
  final String titleEn;
  final String summaryFa;

  factory KnowledgeSummary.fromJson(Map<String, dynamic> json) => KnowledgeSummary(
        slug: json['slug'] as String,
        kind: json['kind'] as String,
        titleFa: json['titleFa'] as String,
        titleEn: json['titleEn'] as String,
        summaryFa: json['summaryFa'] as String,
      );
}

class KnowledgeArticle {
  const KnowledgeArticle({
    required this.summary,
    required this.symptoms,
    required this.causes,
    required this.management,
    required this.references,
    this.attributes = const {},
  });

  final KnowledgeSummary summary;
  final List<String> symptoms;
  final List<String> causes;
  final List<String> management;
  final List<KnowledgeReference> references;

  /// Kind-specific attributes (scientificName, damageType, pathogen, ...). Values may be null.
  final Map<String, String?> attributes;

  factory KnowledgeArticle.fromJson(Map<String, dynamic> json) {
    List<String> list(String key) => (json[key] as List? ?? const []).map((e) => e.toString()).toList();
    final attrs = (json['attributes'] as Map?) ?? const {};
    return KnowledgeArticle(
      summary: KnowledgeSummary.fromJson(json),
      symptoms: list('symptoms'),
      causes: list('causes'),
      management: list('management'),
      references: (json['references'] as List? ?? const [])
          .map((e) => KnowledgeReference.fromJson(e as Map<String, dynamic>))
          .toList(),
      attributes: {for (final e in attrs.entries) e.key.toString(): e.value as String?},
    );
  }
}

class KnowledgeReference {
  const KnowledgeReference({required this.citation, this.url, this.doi, this.year, this.verified = false});

  final String citation;
  final String? url;
  final String? doi;
  final int? year;
  final bool verified;

  factory KnowledgeReference.fromJson(Map<String, dynamic> json) => KnowledgeReference(
        citation: json['citation'] as String,
        url: json['url'] as String?,
        doi: json['doi'] as String?,
        year: (json['year'] as num?)?.toInt(),
        verified: json['verified'] as bool? ?? false,
      );
}
