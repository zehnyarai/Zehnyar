import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/ai_repository.dart';

/// Opens a bottom sheet with an AI hint for one field. Shows the safety disclaimer with every answer.
Future<void> showAiAssistSheet(
  BuildContext context, {
  required String feature,
  required String field,
  required String value,
  AiAssistDetails? details,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => _AiAssistSheet(feature: feature, field: field, value: value, details: details),
  );
}

class _AiAssistSheet extends ConsumerStatefulWidget {
  const _AiAssistSheet({required this.feature, required this.field, required this.value, this.details});

  final String feature;
  final String field;
  final String value;
  final AiAssistDetails? details;

  @override
  ConsumerState<_AiAssistSheet> createState() => _AiAssistSheetState();
}

class _AiAssistSheetState extends ConsumerState<_AiAssistSheet> {
  late Future<AiAssistResult> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<AiAssistResult> _load() {
    return ref.read(aiRepositoryProvider).assist(
          feature: widget.feature,
          field: widget.field,
          value: widget.value,
          details: widget.details,
        );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(20, 4, 20, 20 + MediaQuery.of(context).viewInsets.bottom),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.auto_awesome_rounded, color: AppColors.green700),
                const SizedBox(width: 8),
                Expanded(child: Text('کمک هوشمند: ${widget.field}', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800))),
              ],
            ),
            const SizedBox(height: 4),
            Text('مقدار: ${widget.value}', style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft)),
            const SizedBox(height: 16),
            FutureBuilder<AiAssistResult>(
              future: _future,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 32),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                if (snap.hasError) {
                  return ErrorView(error: snap.error!, onRetry: () => setState(() => _future = _load()));
                }
                final r = snap.data!;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: AppColors.green50, borderRadius: BorderRadius.circular(16)),
                      child: Text(r.text, style: theme.textTheme.bodyLarge?.copyWith(height: 1.8)),
                    ),
                    const SizedBox(height: 12),
                    Text(r.disclaimer, style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft, height: 1.6)),
                    if (r.remainingToday != null) ...[
                      const SizedBox(height: 8),
                      Text('سهمیه‌ی باقی‌مانده امروز: ${r.remainingToday}', style: theme.textTheme.bodySmall),
                    ],
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
