import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/app_config.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/presentation/auth_controller.dart';

class SplashPage extends ConsumerStatefulWidget {
  const SplashPage({super.key});

  @override
  ConsumerState<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends ConsumerState<SplashPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(authControllerProvider.notifier).bootstrap();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [AppColors.green900, AppColors.green700, AppColors.green500],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              children: [
                const Spacer(),
                Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.eco_rounded, size: 72, color: Colors.white),
                ),
                const SizedBox(height: 24),
                Text(
                  AppConfig.appName,
                  style: theme.textTheme.displaySmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Text(
                  'دستیار هوشمند باغ پسته شما',
                  style: theme.textTheme.titleMedium?.copyWith(color: Colors.white.withValues(alpha: 0.9)),
                ),
                const Spacer(),
                if (auth.error != null) ...[
                  Text(auth.error!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white)),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.white), foregroundColor: Colors.white),
                    onPressed: () => ref.read(authControllerProvider.notifier).bootstrap(),
                    child: const Text('تلاش دوباره'),
                  ),
                ] else
                  const CircularProgressIndicator(color: Colors.white),
                const SizedBox(height: 24),
                Text('نسخه ${AppConfig.appNameEn} ۱٫۰٫۰', style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
