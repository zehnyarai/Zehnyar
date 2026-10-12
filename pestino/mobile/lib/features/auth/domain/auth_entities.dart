class AuthUser {
  const AuthUser({
    required this.id,
    required this.phone,
    this.fullName,
    this.province,
    this.city,
    this.role = 'farmer',
  });

  final String id;
  final String phone;
  final String? fullName;
  final String? province;
  final String? city;
  final String role;

  String get displayName => (fullName == null || fullName!.isEmpty) ? 'کشاورز گرامی' : fullName!;

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        id: json['id'] as String,
        phone: json['phone'] as String,
        fullName: json['fullName'] as String?,
        province: json['province'] as String?,
        city: json['city'] as String?,
        role: (json['role'] as String?) ?? 'farmer',
      );

  AuthUser copyWith({String? fullName, String? province, String? city}) => AuthUser(
        id: id,
        phone: phone,
        fullName: fullName ?? this.fullName,
        province: province ?? this.province,
        city: city ?? this.city,
        role: role,
      );
}

/// Result of step 1 of login (sending the OTP).
class OtpChallenge {
  const OtpChallenge({required this.expiresInSeconds, this.devCode});

  final int expiresInSeconds;

  /// Only present in development builds of the backend. Never shown in production.
  final String? devCode;

  factory OtpChallenge.fromJson(Map<String, dynamic> json) => OtpChallenge(
        expiresInSeconds: (json['expiresIn'] as num?)?.toInt() ?? 120,
        devCode: json['devCode'] as String?,
      );
}
