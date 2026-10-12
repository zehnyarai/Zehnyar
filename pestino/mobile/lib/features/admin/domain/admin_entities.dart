/// Admin panel entities. These mirror the admin API in pestino/docs/ADMIN_AI.md.
/// The Gemini key itself is never part of any entity: the API only returns a masked hint.

int _int(Object? v) => (v as num?)?.toInt() ?? 0;

class AdminStats {
  const AdminStats({
    required this.usersTotal,
    required this.usersNewLast7Days,
    required this.analyses24h,
    required this.analyses7d,
    required this.analysesFailed7d,
    required this.premiumActive,
    required this.aiCalls7d,
    required this.aiErrors7d,
    required this.aiTokens7d,
  });

  final int usersTotal;
  final int usersNewLast7Days;
  final int analyses24h;
  final int analyses7d;
  final int analysesFailed7d;
  final int premiumActive;
  final int aiCalls7d;
  final int aiErrors7d;
  final int aiTokens7d;

  factory AdminStats.fromJson(Map<String, dynamic> json) {
    final u = (json['users'] as Map?) ?? const {};
    final a = (json['analyses'] as Map?) ?? const {};
    final s = (json['subscriptions'] as Map?) ?? const {};
    final ai = (json['ai'] as Map?) ?? const {};
    return AdminStats(
      usersTotal: _int(u['total']),
      usersNewLast7Days: _int(u['newLast7Days']),
      analyses24h: _int(a['last24Hours']),
      analyses7d: _int(a['last7Days']),
      analysesFailed7d: _int(a['failedLast7Days']),
      premiumActive: _int(s['premiumActive']),
      aiCalls7d: _int(ai['callsLast7Days']),
      aiErrors7d: _int(ai['errorsLast7Days']),
      aiTokens7d: _int(ai['tokensLast7Days']),
    );
  }
}

class AiSettings {
  const AiSettings({
    required this.keySource,
    required this.keyConfigured,
    required this.keyHint,
    required this.defaultModel,
    required this.timeoutMs,
    required this.aiEnabled,
    required this.keyEncryptionConfigured,
  });

  /// `database` | `environment` | `none`
  final String keySource;
  final bool keyConfigured;
  final String? keyHint;
  final String defaultModel;
  final int timeoutMs;
  final bool aiEnabled;
  final bool keyEncryptionConfigured;

  factory AiSettings.fromJson(Map<String, dynamic> json) => AiSettings(
        keySource: (json['keySource'] as String?) ?? 'none',
        keyConfigured: json['keyConfigured'] as bool? ?? false,
        keyHint: json['keyHint'] as String?,
        defaultModel: (json['defaultModel'] as String?) ?? '',
        timeoutMs: _int(json['timeoutMs']),
        aiEnabled: json['aiEnabled'] as bool? ?? true,
        keyEncryptionConfigured: json['keyEncryptionConfigured'] as bool? ?? false,
      );
}

class AiConnectionTest {
  const AiConnectionTest({required this.ok, required this.model, required this.latencyMs, this.errorCode});

  final bool ok;
  final String model;
  final int latencyMs;
  final String? errorCode;

  factory AiConnectionTest.fromJson(Map<String, dynamic> json) => AiConnectionTest(
        ok: json['ok'] as bool? ?? false,
        model: (json['model'] as String?) ?? '',
        latencyMs: _int(json['latencyMs']),
        errorCode: json['errorCode'] as String?,
      );
}

class AiFeature {
  const AiFeature({
    required this.key,
    required this.titleFa,
    required this.descriptionFa,
    required this.kind,
    required this.enabled,
    required this.model,
    required this.editablePrompt,
    required this.systemPrompt,
    required this.maxOutputTokens,
    required this.temperature,
    required this.dailyLimitFree,
    required this.dailyLimitPremium,
  });

  final String key;
  final String titleFa;
  final String descriptionFa;
  final String kind;
  final bool enabled;
  final String? model;
  final bool editablePrompt;
  final String? systemPrompt;
  final int maxOutputTokens;
  final double temperature;
  final int dailyLimitFree;
  final int dailyLimitPremium;

  factory AiFeature.fromJson(Map<String, dynamic> json) => AiFeature(
        key: json['key'] as String,
        titleFa: (json['titleFa'] as String?) ?? '',
        descriptionFa: (json['descriptionFa'] as String?) ?? '',
        kind: (json['kind'] as String?) ?? 'text',
        enabled: json['enabled'] as bool? ?? true,
        model: json['model'] as String?,
        editablePrompt: json['editablePrompt'] as bool? ?? false,
        systemPrompt: json['systemPrompt'] as String?,
        maxOutputTokens: _int(json['maxOutputTokens']),
        temperature: (json['temperature'] as num?)?.toDouble() ?? 0.2,
        dailyLimitFree: _int(json['dailyLimitFree']),
        dailyLimitPremium: _int(json['dailyLimitPremium']),
      );
}

class AiUsageRow {
  const AiUsageRow({
    required this.feature,
    required this.status,
    required this.calls,
    required this.inputTokens,
    required this.outputTokens,
    required this.avgLatencyMs,
  });

  final String feature;
  final String status;
  final int calls;
  final int inputTokens;
  final int outputTokens;
  final int avgLatencyMs;

  factory AiUsageRow.fromJson(Map<String, dynamic> json) => AiUsageRow(
        feature: json['feature'] as String,
        status: json['status'] as String,
        calls: _int(json['calls']),
        inputTokens: _int(json['inputTokens']),
        outputTokens: _int(json['outputTokens']),
        avgLatencyMs: _int(json['avgLatencyMs']),
      );
}

class AdminUser {
  const AdminUser({
    required this.id,
    required this.phone,
    required this.fullName,
    required this.role,
    required this.isActive,
    required this.createdAt,
    required this.lastLoginAt,
  });

  final String id;
  final String phone;
  final String? fullName;
  final String role;
  final bool isActive;
  final DateTime createdAt;
  final DateTime? lastLoginAt;

  factory AdminUser.fromJson(Map<String, dynamic> json) => AdminUser(
        id: json['id'] as String,
        phone: json['phone'] as String,
        fullName: json['fullName'] as String?,
        role: (json['role'] as String?) ?? 'farmer',
        isActive: json['isActive'] as bool? ?? true,
        createdAt: DateTime.parse(json['createdAt'] as String),
        lastLoginAt: json['lastLoginAt'] == null ? null : DateTime.parse(json['lastLoginAt'] as String),
      );
}

class AuditEntry {
  const AuditEntry({required this.id, required this.action, required this.target, required this.createdAt});

  final int id;
  final String action;
  final String? target;
  final DateTime createdAt;

  factory AuditEntry.fromJson(Map<String, dynamic> json) => AuditEntry(
        id: _int(json['id']),
        action: json['action'] as String,
        target: json['target'] as String?,
        createdAt: DateTime.parse(json['createdAt'] as String),
      );
}
