import '../../auth/domain/auth_entities.dart';
import 'admin_entities.dart';

/// Contract for the admin panel. Every method requires an admin session except [login].
abstract interface class AdminRepository {
  /// Password login for admin accounts. Stores the session on success.
  Future<AuthUser> login({required String phone, required String password});

  Future<AdminStats> stats();

  Future<AiSettings> aiSettings();

  /// Pass only the fields to change. Use [clearApiKey] to remove the stored key.
  Future<AiSettings> updateAiSettings({
    String? apiKey,
    bool clearApiKey = false,
    String? defaultModel,
    int? timeoutMs,
    bool? aiEnabled,
  });

  Future<AiConnectionTest> testAi();

  Future<List<AiFeature>> aiFeatures();

  Future<AiFeature> updateAiFeature(String key, Map<String, dynamic> changes);

  Future<List<AiUsageRow>> aiUsage({int days = 7});

  Future<List<AdminUser>> users({String query = ''});

  Future<void> setUserActive(String userId, {required bool active});

  Future<List<AuditEntry>> audit({int limit = 50});
}
