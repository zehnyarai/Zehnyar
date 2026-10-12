class Farm {
  const Farm({
    required this.id,
    required this.name,
    required this.province,
    required this.city,
    this.latitude,
    this.longitude,
    this.areaHectares,
    this.pistachioVariety,
    this.averageTreeAge,
    this.irrigationMethod,
    this.soilType,
    this.soilNotes,
  });

  final String id;
  final String name;
  final String province;
  final String city;
  final double? latitude;
  final double? longitude;
  final double? areaHectares;
  final String? pistachioVariety;
  final int? averageTreeAge;
  final String? irrigationMethod;
  final String? soilType;
  final String? soilNotes;

  factory Farm.fromJson(Map<String, dynamic> json) => Farm(
        id: json['id'] as String,
        name: json['name'] as String,
        province: json['province'] as String,
        city: json['city'] as String,
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
        areaHectares: (json['areaHectares'] as num?)?.toDouble(),
        pistachioVariety: json['pistachioVariety'] as String?,
        averageTreeAge: (json['averageTreeAge'] as num?)?.toInt(),
        irrigationMethod: json['irrigationMethod'] as String?,
        soilType: json['soilType'] as String?,
        soilNotes: json['soilNotes'] as String?,
      );
}

/// Payload for creating / updating a farm. Null means "not set".
class FarmInput {
  const FarmInput({
    required this.name,
    required this.province,
    required this.city,
    this.areaHectares,
    this.pistachioVariety,
    this.averageTreeAge,
    this.irrigationMethod,
    this.soilType,
    this.soilNotes,
  });

  final String name;
  final String province;
  final String city;
  final double? areaHectares;
  final String? pistachioVariety;
  final int? averageTreeAge;
  final String? irrigationMethod;
  final String? soilType;
  final String? soilNotes;

  Map<String, dynamic> toJson() => {
        'name': name,
        'province': province,
        'city': city,
        'areaHectares': areaHectares,
        'pistachioVariety': pistachioVariety,
        'averageTreeAge': averageTreeAge,
        'irrigationMethod': irrigationMethod,
        'soilType': soilType,
        'soilNotes': soilNotes,
      };
}

class Tree {
  const Tree({required this.id, required this.label, this.plantedYear, this.variety});

  final String id;
  final String label;
  final int? plantedYear;
  final String? variety;

  factory Tree.fromJson(Map<String, dynamic> json) => Tree(
        id: json['id'] as String,
        label: json['label'] as String,
        plantedYear: (json['plantedYear'] as num?)?.toInt(),
        variety: json['variety'] as String?,
      );
}
