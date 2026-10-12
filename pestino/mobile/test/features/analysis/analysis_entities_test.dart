import 'package:flutter_test/flutter_test.dart';
import 'package:pestino/features/analysis/domain/analysis_entities.dart';

void main() {
  group('AnalysisUsage', () {
    test('null monthlyLimit means unlimited', () {
      final u = AnalysisUsage.fromJson({
        'plan': 'premium',
        'planName': 'حرفه‌ای',
        'used': 42,
        'monthlyLimit': null,
        'remaining': null,
      });
      expect(u.isUnlimited, isTrue);
      expect(u.exhausted, isFalse);
    });

    test('free plan with no remaining analyses is exhausted', () {
      final u = AnalysisUsage.fromJson({
        'plan': 'free',
        'planName': 'رایگان',
        'used': 5,
        'monthlyLimit': 5,
        'remaining': 0,
      });
      expect(u.isUnlimited, isFalse);
      expect(u.exhausted, isTrue);
    });

    test('free plan with remaining analyses is not exhausted', () {
      final u = AnalysisUsage.fromJson({
        'plan': 'free',
        'planName': 'رایگان',
        'used': 2,
        'monthlyLimit': 5,
        'remaining': 3,
      });
      expect(u.exhausted, isFalse);
    });
  });

  group('AnalysisReport parsing', () {
    test('missing priority defaults to soon', () {
      final a = ReportAction.fromJson({'text': 'بازرسی باغ'});
      expect(a.priority, 'soon');
    });

    test('unverified references are marked as not verified', () {
      final r = ReportReference.fromJson({'citation': 'منبع نمونه', 'verified': false});
      expect(r.verified, isFalse);
    });

    test('report with a failed image quality still parses', () {
      final r = AnalysisReport.fromJson({
        'summary': 'خلاصه',
        'imageQuality': {'usable': false, 'issues': ['تار است']},
        'diagnosis': {'title': 'نامشخص', 'isHealthy': false, 'confidence': 30.4},
        'recommendedActions': [],
        'references': [],
        'disclaimer': 'توجه',
      });
      expect(r.imageUsable, isFalse);
      expect(r.imageIssues, ['تار است']);
      expect(r.confidence, 30);
    });
  });
}
