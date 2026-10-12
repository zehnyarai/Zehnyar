import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/presentation/auth_controller.dart';
import 'profile_form.dart';

/// First-time setup after login: name and location (used to tailor advice).
class OnboardingPage extends ConsumerWidget {
  const OnboardingPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    return Scaffold(
      appBar: AppBar(
        title: const Text('تکمیل اطلاعات'),
        actions: [TextButton(onPressed: () => context.go(AppRoutes.dashboard), child: const Text('بعداً'))],
      ),
      body: user == null
          ? const SizedBox.shrink()
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                const Icon(Icons.person_pin_circle_rounded, size: 56, color: AppColors.green700),
                const SizedBox(height: 12),
                Text(
                  'به پستینو خوش آمدید',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                const Text(
                  'با ثبت نام و موقعیت، توصیه‌ها برای منطقه شما دقیق‌تر می‌شود.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.inkSoft, height: 1.7),
                ),
                const SizedBox(height: 28),
                ProfileForm(
                  user: user,
                  submitLabel: 'ادامه',
                  onSaved: () => context.go(AppRoutes.dashboard),
                ),
              ],
            ),
    );
  }
}
