import 'package:flutter/material.dart';

import '../errors/app_failure.dart';
import '../theme/app_colors.dart';
import '../utils/persian.dart';

/// Rounded surface card used across the app.
class PestinoCard extends StatelessWidget {
  const PestinoCard({super.key, required this.child, this.padding = const EdgeInsets.all(16), this.onTap, this.color});

  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final content = Padding(padding: padding, child: child);
    return Card(
      color: color,
      child: onTap == null
          ? content
          : InkWell(
              borderRadius: BorderRadius.circular(20),
              onTap: onTap,
              child: content,
            ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.title, {super.key, this.action, this.onAction});

  final String title;
  final String? action;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
        ),
        if (action != null && onAction != null)
          TextButton(onPressed: onAction, child: Text(action!)),
      ],
    );
  }
}

/// Empty list / no-data placeholder.
class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.icon, required this.title, this.message, this.actionLabel, this.onAction});

  final IconData icon;
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(color: AppColors.green100, shape: BoxShape.circle),
              child: Icon(icon, size: 40, color: AppColors.green700),
            ),
            const SizedBox(height: 16),
            Text(title, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700), textAlign: TextAlign.center),
            if (message != null) ...[
              const SizedBox(height: 8),
              Text(message!, style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft), textAlign: TextAlign.center),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 20),
              FilledButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}

/// Shows a Persian error message with a retry action.
class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.error, this.onRetry});

  final Object error;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final failure = AppFailure.from(error);
    return EmptyState(
      icon: failure.isNetwork ? Icons.wifi_off_rounded : Icons.error_outline_rounded,
      title: 'مشکلی پیش آمد',
      message: failure.message,
      actionLabel: onRetry == null ? null : 'تلاش دوباره',
      onAction: onRetry,
    );
  }
}

class LoadingView extends StatelessWidget {
  const LoadingView({super.key, this.message});

  final String? message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(),
          if (message != null) ...[
            const SizedBox(height: 16),
            Text(message!, style: Theme.of(context).textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }
}

/// Circular confidence indicator (0–100) with Persian percentage.
class ConfidenceRing extends StatelessWidget {
  const ConfidenceRing({super.key, required this.value, this.size = 96});

  final int value;
  final double size;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.confidence(value);
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: size,
            height: size,
            child: CircularProgressIndicator(
              value: value / 100,
              strokeWidth: 8,
              backgroundColor: AppColors.outline,
              color: color,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(Persian.percent(value), style: TextStyle(fontWeight: FontWeight.w800, fontSize: size / 4.6, color: color)),
              Text('اطمینان', style: TextStyle(fontSize: size / 8, color: AppColors.inkSoft)),
            ],
          ),
        ],
      ),
    );
  }
}

/// Coloured label chip, e.g. for priorities or statuses.
class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.label, required this.color, this.icon});

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[Icon(icon, size: 14, color: color), const SizedBox(width: 4)],
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 12)),
        ],
      ),
    );
  }
}
