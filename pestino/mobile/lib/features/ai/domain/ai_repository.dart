/// Field-level AI help (farm form, report explanation). Results are text only.
class AiAssistDetails {
  const AiAssistDetails({
    this.province,
    this.city,
    this.pistachioVariety,
    this.treeAgeYears,
    this.irrigationMethod,
    this.soilType,
  });

  final String? province;
  final String? city;
  final String? pistachioVariety;
  final int? treeAgeYears;
  final String? irrigationMethod;
  final String? soilType;

  Map<String, dynamic> toJson() => {
        if (province != null && province!.isNotEmpty) 'province': province,
        if (city != null && city!.isNotEmpty) 'city': city,
        if (pistachioVariety != null) 'pistachioVariety': pistachioVariety,
        if (treeAgeYears != null) 'treeAgeYears': treeAgeYears,
        if (irrigationMethod != null) 'irrigationMethod': irrigationMethod,
        if (soilType != null) 'soilType': soilType,
      };
}

class AiAssistResult {
  const AiAssistResult({
    required this.text,
    required this.disclaimer,
    required this.flags,
    required this.remainingToday,
  });

  final String text;
  final String disclaimer;
  final List<String> flags;
  final int? remainingToday;

  factory AiAssistResult.fromJson(Map<String, dynamic> json) => AiAssistResult(
        text: json['text'] as String,
        disclaimer: (json['disclaimer'] as String?) ?? '',
        flags: ((json['flags'] as List?) ?? const []).cast<String>(),
        remainingToday: (json['remainingToday'] as num?)?.toInt(),
      );
}

abstract interface class AiRepository {
  Future<AiAssistResult> assist({
    required String feature,
    required String field,
    required String value,
    AiAssistDetails? details,
  });
}
