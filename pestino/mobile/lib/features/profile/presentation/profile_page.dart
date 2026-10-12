import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/config/app_config.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../../analysis/presentation/analysis_providers.dart';
import '../../auth/presentation/auth_controller.dart';
import '../../subscription/presentation/subscription_providers.dart';
import 'profile_form.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final plan = ref.watch(currentPlanProvider);
    final usage = ref.watch(analysisUsageProvider);
    final theme = Theme.of(context);

    if (user == null) return const LoadingView();

    return Scaffold(
      appBar: AppBar(title: const Text('پروفایل')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          PestinoCard(
            color: AppColors.green700,
            child: Row(
              children: [
                const CircleAvatar(radius: 30, backgroundColor: Colors.white, child: Icon(Icons.person_rounded, size: 34, color: AppColors.green700)),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(user.displayName, style: theme.textTheme.titleMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 4),
                      Text(Persian.phoneDisplay(user.phone), style: TextStyle(color: Colors.white.withValues(alpha: 0.9))),
                      if (user.province != null) ...[
                        const SizedBox(height: 2),
                        Text('${user.province}، ${user.city ?? ''}', style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13)),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          PestinoCard(
            onTap: () => context.push(AppRoutes.paywall),
            child: Row(
              children: [
                const Icon(Icons.workspace_premium_rounded, color: AppColors.earth500),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('طرح: ${plan.valueOrNull?.nameFa ?? '...'}', style: const TextStyle(fontWeight: FontWeight.w800)),
                      const SizedBox(height: 4),
                      Text(
                        usage.maybeWhen(
                          data: (u) => u.isUnlimited ? 'تحلیل نامحدود' : '${Persian.digits(u.remaining ?? 0)} تحلیل باقی‌مانده این ماه',
                          orElse: () => '',
                        ),
                        style: const TextStyle(color: AppColors.inkSoft),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_left_rounded),
              ],
            ),
          ),
          const SizedBox(height: 16),
          PestinoCard(
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: const Text('ویرایش اطلاعات', style: TextStyle(fontWeight: FontWeight.w800)),
              childrenPadding: const EdgeInsets.only(top: 8),
              children: [
                ProfileForm(
                  user: user,
                  submitLabel: 'ذخیره',
                  onSaved: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('اطلاعات ذخیره شد'))),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          PestinoCard(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.menu_book_rounded),
                  title: const Text('دانش کشاورزی'),
                  trailing: const Icon(Icons.chevron_left_rounded),
                  onTap: () => context.push(AppRoutes.knowledge),
                ),
                if (user?.role == 'admin') ...[
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.admin_panel_settings_rounded, color: AppColors.earth700),
                    title: const Text('پنل مدیریت'),
                    subtitle: const Text('آمار، هوش مصنوعی، کاربران و ممیزی'),
                    trailing: const Icon(Icons.chevron_left_rounded),
                    onTap: () => context.push(AppRoutes.adminHome),
                  ),
                ],
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.privacy_tip_outlined),
                  title: const Text('حریم خصوصی'),
                  subtitle: Text(AppConfig.privacyPolicyUrl),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.description_outlined),
                  title: const Text('شرایط استفاده'),
                  subtitle: Text(AppConfig.termsUrl),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger, side: const BorderSide(color: AppColors.danger)),
            onPressed: () async {
              final ok = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('خروج از حساب'),
                  content: const Text('آیا می‌خواهید از حساب کاربری خارج شوید؟'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')),
                    FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('خروج')),
                  ],
                ),
              );
              if (ok == true) await ref.read(authControllerProvider.notifier).logout();
            },
            icon: const Icon(Icons.logout_rounded),
            label: const Text('خروج از حساب'),
          ),
        ],
      ),
    );
  }
}
