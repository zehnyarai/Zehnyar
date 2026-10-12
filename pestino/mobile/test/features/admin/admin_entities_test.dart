import 'package:flutter_test/flutter_test.dart';
import 'package:pestino/features/ai/domain/ai_repository.dart';
import 'package:pestino/features/admin/domain/admin_entities.dart';

void main() {
  test('AdminStats parses the nested admin API payload', () {
    final s = AdminStats.fromJson({
      'users': {'total': 12, 'newLast7Days': 3},
      'analyses': {'last24Hours': 2, 'last7Days': 9, 'failedLast7Days': 1},
      'subscriptions': {'premiumActive': 4},
      'ai': {'callsLast7Days': 20, 'errorsLast7Days': 0, 'tokensLast7Days': 5000},
    });
    expect(s.usersTotal, 12);
    expect(s.analysesFailed7d, 1);
    expect(s.aiTokens7d, 5000);
  });

  test('AiSettings never expects a full key, only a hint', () {
    final s = AiSettings.fromJson({
      'keySource': 'database',
      'keyConfigured': true,
      'keyHint': '1234',
      'defaultModel': 'gemini-2.5-flash',
      'timeoutMs': 45000,
      'aiEnabled': true,
      'keyEncryptionConfigured': true,
    });
    expect(s.keyHint, '1234');
    expect(s.keySource, 'database');
  });

  test('AiFeature keeps null model and prompt as "default"', () {
    final f = AiFeature.fromJson({
      'key': 'farm_form_help',
      'titleFa': 'کمک فرم',
      'descriptionFa': '',
      'kind': 'text',
      'enabled': true,
      'model': null,
      'editablePrompt': true,
      'systemPrompt': null,
      'maxOutputTokens': 512,
      'temperature': 0.2,
      'dailyLimitFree': 5,
      'dailyLimitPremium': 100,
    });
    expect(f.model, isNull);
    expect(f.systemPrompt, isNull);
    expect(f.temperature, closeTo(0.2, 1e-9));
  });

  test('AiAssistDetails omits empty values from the request', () {
    const d = AiAssistDetails(province: '', city: 'کرمان', treeAgeYears: 12);
    expect(d.toJson(), {'city': 'کرمان', 'treeAgeYears': 12});
  });

  test('AiAssistResult reads flags and remaining quota', () {
    final r = AiAssistResult.fromJson({
      'text': 'متن',
      'disclaimer': 'د',
      'flags': ['UNSAFE_ADVICE_REPLACED'],
      'remainingToday': 2,
    });
    expect(r.flags, ['UNSAFE_ADVICE_REPLACED']);
    expect(r.remainingToday, 2);
  });
}
