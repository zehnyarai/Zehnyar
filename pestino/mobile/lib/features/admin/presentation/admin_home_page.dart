import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/common_widgets.dart';
import '../../auth/presentation/auth_controller.dart';
import '../domain/admin_entities.dart';
import 'admin_providers.dart';

/// Admin panel: statistics, AI controls, users and audit log.
/// The role is checked here for navigation only. Every admin API call is enforced again on the server.
class AdminHomePage extends ConsumerWidget {
  const AdminHomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    if (user == null || user.role != 'admin') {
      return Scaffold(
        appBar: AppBar(title: const Text('پنل مدیریت')),
        body: EmptyState(
          icon: Icons.lock_outline_rounded,
          title: 'دسترسی ندارید',
          message: 'این بخش فقط برای مدیران پستینو است.',
          actionLabel: 'بازگشت',
          onAction: () => context.go(AppRoutes.dashboard),
        ),
      );
    }

    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('پنل مدیریت'),
          actions: [
            IconButton(
              tooltip: 'خروج از حساب مدیر',
              icon: const Icon(Icons.logout_rounded),
              onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            ),
          ],
          bottom: const TabBar(
            isScrollable: true,
            tabs: [
              Tab(icon: Icon(Icons.insights_rounded), text: 'آمار'),
              Tab(icon: Icon(Icons.auto_awesome_rounded), text: 'هوش مصنوعی'),
              Tab(icon: Icon(Icons.people_alt_rounded), text: 'کاربران'),
              Tab(icon: Icon(Icons.fact_check_rounded), text: 'ممیزی'),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            const _StatsTab(),
            const _AiTab(),
            _UsersTab(currentUserId: user.id),
            const _AuditTab(),
          ],
        ),
      ),
    );
  }
}

/// Shared helper: runs an admin action, shows Persian errors, and refreshes the affected providers.
Future<void> _run(BuildContext context, Future<void> Function() action, {String? success}) async {
  try {
    await action();
    if (context.mounted && success != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(success)));
    }
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    }
  }
}

// ---------------------------------------------------------------------------
// Statistics
// ---------------------------------------------------------------------------

class _StatsTab extends ConsumerWidget {
  const _StatsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(adminStatsProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.refresh(adminStatsProvider.future),
      child: stats.when(
        loading: () => const LoadingView(),
        error: (e, _) => ListView(children: [ErrorView(error: e, onRetry: () => ref.invalidate(adminStatsProvider))]),
        data: (s) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const SectionTitle('کاربران و اشتراک'),
            const SizedBox(height: 8),
            _pair(_StatTile('کل کاربران', s.usersTotal, Icons.people_outline), _StatTile('ثبت‌نام ۷ روز اخیر', s.usersNewLast7Days, Icons.person_add_alt_1_outlined)),
            const SizedBox(height: 12),
            _pair(_StatTile('اشتراک فعال حرفه‌ای', s.premiumActive, Icons.workspace_premium_outlined), const SizedBox()),
            const SizedBox(height: 20),
            const SectionTitle('تحلیل تصویر'),
            const SizedBox(height: 8),
            _pair(_StatTile('تحلیل ۲۴ ساعت اخیر', s.analyses24h, Icons.camera_alt_outlined), _StatTile('تحلیل ۷ روز اخیر', s.analyses7d, Icons.analytics_outlined)),
            const SizedBox(height: 12),
            _pair(_StatTile('ناموفق در ۷ روز', s.analysesFailed7d, Icons.error_outline_rounded, warn: s.analysesFailed7d > 0), const SizedBox()),
            const SizedBox(height: 20),
            const SectionTitle('هوش مصنوعی (۷ روز)'),
            const SizedBox(height: 8),
            _pair(_StatTile('تعداد فراخوانی', s.aiCalls7d, Icons.auto_awesome_outlined), _StatTile('خطا', s.aiErrors7d, Icons.report_gmailerrorred_rounded, warn: s.aiErrors7d > 0)),
            const SizedBox(height: 12),
            _pair(_StatTile('مجموع توکن', s.aiTokens7d, Icons.data_usage_rounded), const SizedBox()),
          ],
        ),
      ),
    );
  }

  static Widget _pair(Widget a, Widget b) => Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [Expanded(child: a), const SizedBox(width: 12), Expanded(child: b)],
      );
}

class _StatTile extends StatelessWidget {
  const _StatTile(this.label, this.value, this.icon, {this.warn = false});

  final String label;
  final int value;
  final IconData icon;
  final bool warn;

  @override
  Widget build(BuildContext context) {
    final color = warn ? AppColors.warning : AppColors.green700;
    return PestinoCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color),
          const SizedBox(height: 10),
          Text(_fa(value), style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800, color: color)),
          const SizedBox(height: 4),
          Text(label, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.inkSoft)),
        ],
      ),
    );
  }

  static String _fa(int n) {
    const digits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return n.toString().split('').map((c) => digits[int.parse(c)]).join();
  }
}

// ---------------------------------------------------------------------------
// AI controls
// ---------------------------------------------------------------------------

class _AiTab extends ConsumerWidget {
  const _AiTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(adminAiSettingsProvider);
    final features = ref.watch(adminAiFeaturesProvider);
    final usage = ref.watch(adminAiUsageProvider);

    Future<void> refreshAll() async {
      ref.invalidate(adminAiSettingsProvider);
      ref.invalidate(adminAiFeaturesProvider);
      ref.invalidate(adminAiUsageProvider);
    }

    return RefreshIndicator(
      onRefresh: () async => refreshAll(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          settings.when(
            loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
            error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(adminAiSettingsProvider)),
            data: (s) => _AiSettingsEditor(settings: s),
          ),
          const SizedBox(height: 20),
          const SectionTitle('قابلیت‌های هوش مصنوعی'),
          const SizedBox(height: 8),
          features.when(
            loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
            error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(adminAiFeaturesProvider)),
            data: (items) => Column(children: [for (final f in items) _FeatureCard(feature: f)]),
          ),
          const SizedBox(height: 20),
          const SectionTitle('مصرف ۷ روز اخیر'),
          const SizedBox(height: 8),
          usage.when(
            loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
            error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(adminAiUsageProvider)),
            data: (rows) => rows.isEmpty
                ? const Padding(padding: EdgeInsets.all(12), child: Text('هنوز فراخوانی ثبت نشده است.'))
                : PestinoCard(
                    padding: EdgeInsets.zero,
                    child: Column(
                      children: [
                        for (var i = 0; i < rows.length; i++) ...[
                          if (i > 0) const Divider(height: 1),
                          ListTile(
                            dense: true,
                            leading: Icon(
                              rows[i].status == 'error' ? Icons.error_outline_rounded : Icons.check_circle_outline_rounded,
                              color: rows[i].status == 'error' ? AppColors.danger : AppColors.success,
                            ),
                            title: Text('${_featureName(rows[i].feature)} · ${_statusName(rows[i].status)}'),
                            subtitle: Text(
                              '${rows[i].calls} فراخوانی · ${rows[i].inputTokens + rows[i].outputTokens} توکن · میانگین ${rows[i].avgLatencyMs} ms',
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  static String _featureName(String key) => switch (key) {
        'image_analysis' => 'تحلیل تصویر',
        'farm_form_help' => 'کمک فرم مزرعه',
        'report_explain' => 'توضیح گزارش',
        'admin_connection_test' => 'تست اتصال مدیر',
        _ => key,
      };

  static String _statusName(String status) => switch (status) {
        'ok' => 'موفق',
        'error' => 'خطا',
        'blocked' => 'مسدود شده توسط مدل',
        'unsafe_replaced' => 'پاسخ ایمن‌سازی شد',
        _ => status,
      };
}

class _AiSettingsEditor extends ConsumerStatefulWidget {
  const _AiSettingsEditor({required this.settings});

  final AiSettings settings;

  @override
  ConsumerState<_AiSettingsEditor> createState() => _AiSettingsEditorState();
}

class _AiSettingsEditorState extends ConsumerState<_AiSettingsEditor> {
  final _apiKey = TextEditingController();
  late final TextEditingController _model;
  late final TextEditingController _timeout;
  bool _busy = false;
  bool _obscureKey = true;

  @override
  void initState() {
    super.initState();
    _model = TextEditingController(text: widget.settings.defaultModel);
    _timeout = TextEditingController(text: widget.settings.timeoutMs.toString());
  }

  @override
  void dispose() {
    _apiKey.dispose();
    _model.dispose();
    _timeout.dispose();
    super.dispose();
  }

  void _invalidate() {
    ref.invalidate(adminAiSettingsProvider);
  }

  Future<void> _saveKey() async {
    final key = _apiKey.text.trim();
    if (key.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('کلید جدید را وارد کنید.')));
      return;
    }
    setState(() => _busy = true);
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).updateAiSettings(apiKey: key);
      _apiKey.clear();
      _invalidate();
    }, success: 'کلید ذخیره شد و فقط به‌صورت رمزنگاری‌شده نگهداری می‌شود.');
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _clearKey() async {
    final ok = await _confirm(context, 'حذف کلید ذخیره‌شده', 'کلید از پنل حذف می‌شود و سرور از کلید تنظیمات محیطی استفاده می‌کند. ادامه می‌دهید؟');
    if (!ok || !mounted) return;
    setState(() => _busy = true);
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).updateAiSettings(clearApiKey: true);
      _invalidate();
    }, success: 'کلید حذف شد.');
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _saveRuntime() async {
    final timeout = int.tryParse(_timeout.text.trim());
    if (timeout == null || timeout < 5000 || timeout > 120000) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('مهلت پاسخ باید بین ۵۰۰۰ تا ۱۲۰۰۰۰ میلی‌ثانیه باشد.')));
      return;
    }
    final model = _model.text.trim();
    setState(() => _busy = true);
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).updateAiSettings(
            defaultModel: model.isEmpty ? null : model,
            timeoutMs: timeout,
          );
      _invalidate();
    }, success: 'تنظیمات مدل ذخیره شد.');
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _toggleEnabled(bool value) async {
    if (!value) {
      final ok = await _confirm(context, 'خاموش کردن کل هوش مصنوعی', 'همه‌ی قابلیت‌های هوش مصنوعی (از جمله تحلیل تصویر) متوقف می‌شوند. ادامه می‌دهید؟');
      if (!ok || !mounted) return;
    }
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).updateAiSettings(aiEnabled: value);
      _invalidate();
    }, success: value ? 'هوش مصنوعی روشن شد.' : 'هوش مصنوعی خاموش شد.');
  }

  Future<void> _test() async {
    setState(() => _busy = true);
    await _run(context, () async {
      final result = await ref.read(adminRepositoryProvider).testAi();
      if (!mounted) return;
      final message = result.ok
          ? 'اتصال برقرار است · مدل ${result.model} · ${result.latencyMs} ms'
          : 'اتصال ناموفق بود (${result.errorCode ?? 'UNKNOWN'})';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    });
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.settings;
    final theme = Theme.of(context);
    final keyStatus = switch (s.keySource) {
      'database' => 'ذخیره‌شده در پنل (رمزنگاری‌شده) · ****${s.keyHint ?? ''}',
      'environment' => 'از تنظیمات سرور (متغیر محیطی)',
      _ => 'تنظیم نشده',
    };

    return PestinoCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.vpn_key_rounded, color: AppColors.green700),
              const SizedBox(width: 8),
              Expanded(child: Text('کلید و مدل Gemini', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800))),
              Switch(value: s.aiEnabled, onChanged: _busy ? null : _toggleEnabled),
            ],
          ),
          Text('وضعیت: ${s.aiEnabled ? 'روشن' : 'خاموش'} · $keyStatus', style: theme.textTheme.bodySmall),
          if (!s.keyEncryptionConfigured) ...[
            const SizedBox(height: 8),
            const _Notice(
              text: 'متغیر AI_SETTINGS_ENCRYPTION_KEY روی سرور تنظیم نشده است، بنابراین ذخیره‌ی کلید از پنل ممکن نیست.',
            ),
          ],
          const SizedBox(height: 16),
          TextField(
            controller: _apiKey,
            obscureText: _obscureKey,
            textDirection: TextDirection.ltr,
            decoration: InputDecoration(
              labelText: 'کلید جدید Gemini',
              helperText: 'کلید پس از ذخیره دیگر نمایش داده نمی‌شود.',
              suffixIcon: IconButton(
                icon: Icon(_obscureKey ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                onPressed: () => setState(() => _obscureKey = !_obscureKey),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton.icon(
                onPressed: _busy || !s.keyEncryptionConfigured ? null : _saveKey,
                icon: const Icon(Icons.save_outlined),
                label: const Text('ذخیره کلید'),
              ),
              if (s.keySource == 'database')
                OutlinedButton.icon(
                  onPressed: _busy ? null : _clearKey,
                  icon: const Icon(Icons.delete_outline_rounded),
                  label: const Text('حذف کلید'),
                ),
              OutlinedButton.icon(
                onPressed: _busy ? null : _test,
                icon: const Icon(Icons.network_check_rounded),
                label: const Text('تست اتصال'),
              ),
            ],
          ),
          const Divider(height: 32),
          TextField(
            controller: _model,
            textDirection: TextDirection.ltr,
            decoration: const InputDecoration(labelText: 'مدل پیش‌فرض', helperText: 'مثال: gemini-2.5-flash'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _timeout,
            keyboardType: TextInputType.number,
            textDirection: TextDirection.ltr,
            decoration: const InputDecoration(labelText: 'مهلت پاسخ (میلی‌ثانیه)'),
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: _busy ? null : _saveRuntime,
            child: const Text('ذخیره تنظیمات مدل'),
          ),
        ],
      ),
    );
  }
}

class _FeatureCard extends ConsumerStatefulWidget {
  const _FeatureCard({required this.feature});

  final AiFeature feature;

  @override
  ConsumerState<_FeatureCard> createState() => _FeatureCardState();
}

class _FeatureCardState extends ConsumerState<_FeatureCard> {
  bool _busy = false;

  Future<void> _patch(Map<String, dynamic> changes, String success) async {
    setState(() => _busy = true);
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).updateAiFeature(widget.feature.key, changes);
      ref.invalidate(adminAiFeaturesProvider);
    }, success: success);
    if (mounted) setState(() => _busy = false);
  }

  Future<void> _editLimits() async {
    final f = widget.feature;
    final free = TextEditingController(text: '${f.dailyLimitFree}');
    final premium = TextEditingController(text: '${f.dailyLimitPremium}');
    final model = TextEditingController(text: f.model ?? '');
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('تنظیمات ${f.titleFa}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: free,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'سقف روزانه پلن رایگان'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: premium,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'سقف روزانه پلن حرفه‌ای'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: model,
                textDirection: TextDirection.ltr,
                decoration: const InputDecoration(labelText: 'مدل این قابلیت (خالی = پیش‌فرض)'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('انصراف')),
          FilledButton(
            onPressed: () {
              final freeN = int.tryParse(free.text.trim());
              final premiumN = int.tryParse(premium.text.trim());
              if (freeN == null || premiumN == null || freeN < 0 || premiumN < 0) return;
              final m = model.text.trim();
              Navigator.pop(ctx, {'dailyLimitFree': freeN, 'dailyLimitPremium': premiumN, 'model': m.isEmpty ? null : m});
            },
            child: const Text('ذخیره'),
          ),
        ],
      ),
    );
    free.dispose();
    premium.dispose();
    model.dispose();
    if (result != null) await _patch(result, 'محدودیت‌ها ذخیره شد.');
  }

  Future<void> _editPrompt() async {
    final f = widget.feature;
    final controller = TextEditingController(text: f.systemPrompt ?? '');
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('دستورالعمل سیستمی'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'قوانین ایمنی (بدون دوز سم، بدون ادعای ۱۰۰٪، بدون منبع ساختگی) همیشه به این متن اضافه می‌شود. برای بازگشت به متن پیش‌فرض، فیلد را خالی کنید.',
                style: TextStyle(fontSize: 12),
              ),
              const SizedBox(height: 12),
              TextField(controller: controller, maxLines: 8, decoration: const InputDecoration(alignLabelWithHint: true)),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('انصراف')),
          FilledButton(onPressed: () => Navigator.pop(ctx, controller.text.trim()), child: const Text('ذخیره')),
        ],
      ),
    );
    controller.dispose();
    if (result != null) {
      await _patch({'systemPrompt': result.isEmpty ? null : result}, 'دستورالعمل ذخیره شد.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final f = widget.feature;
    final theme = Theme.of(context);
    return PestinoCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(f.titleFa, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800))),
              Switch(value: f.enabled, onChanged: _busy ? null : (v) => _patch({'enabled': v}, v ? 'قابلیت روشن شد.' : 'قابلیت خاموش شد.')),
            ],
          ),
          Text(f.descriptionFa, style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft)),
          const SizedBox(height: 8),
          Text(
            'سقف روزانه: رایگان ${f.dailyLimitFree} · حرفه‌ای ${f.dailyLimitPremium} · مدل: ${f.model ?? 'پیش‌فرض'}',
            style: theme.textTheme.bodySmall,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              OutlinedButton(onPressed: _busy ? null : _editLimits, child: const Text('محدودیت و مدل')),
              if (f.editablePrompt) OutlinedButton(onPressed: _busy ? null : _editPrompt, child: const Text('دستورالعمل')),
            ],
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------

class _UsersTab extends ConsumerStatefulWidget {
  const _UsersTab({required this.currentUserId});

  final String currentUserId;

  @override
  ConsumerState<_UsersTab> createState() => _UsersTabState();
}

class _UsersTabState extends ConsumerState<_UsersTab> {
  final _search = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final users = ref.watch(adminUsersProvider(_query));
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: TextField(
            controller: _search,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: 'جستجوی شماره یا نام',
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: IconButton(
                icon: const Icon(Icons.close_rounded),
                onPressed: () {
                  _search.clear();
                  setState(() => _query = '');
                },
              ),
            ),
            onSubmitted: (v) => setState(() => _query = v.trim()),
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () async => ref.refresh(adminUsersProvider(_query).future),
            child: users.when(
              loading: () => const LoadingView(),
              error: (e, _) => ListView(children: [ErrorView(error: e, onRetry: () => ref.invalidate(adminUsersProvider(_query)))]),
              data: (items) => items.isEmpty
                  ? ListView(children: const [Padding(padding: EdgeInsets.all(24), child: Center(child: Text('کاربری پیدا نشد.')))])
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                      itemCount: items.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (_, i) {
                        final u = items[i];
                        final isMe = u.id == widget.currentUserId;
                        return PestinoCard(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${u.fullName?.isNotEmpty == true ? u.fullName : 'کاربر بدون نام'}${u.role == 'admin' ? ' · مدیر' : ''}${isMe ? ' (شما)' : ''}',
                                      style: const TextStyle(fontWeight: FontWeight.w700),
                                    ),
                                    Text(u.phone, textDirection: TextDirection.ltr, style: const TextStyle(color: AppColors.inkSoft)),
                                    Text(
                                      u.lastLoginAt == null ? 'بدون ورود' : 'آخرین ورود: ${_date(u.lastLoginAt!)}',
                                      style: Theme.of(context).textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ),
                              Switch(
                                value: u.isActive,
                                onChanged: isMe ? null : (v) => _toggle(u, v),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _toggle(AdminUser u, bool active) async {
    if (!active) {
      final ok = await _confirm(context, 'غیرفعال‌سازی کاربر', 'کاربر ${u.phone} از ورود و ادامه‌ی نشست خارج می‌شود. ادامه می‌دهید؟');
      if (!ok || !mounted) return;
    }
    await _run(context, () async {
      await ref.read(adminRepositoryProvider).setUserActive(u.id, active: active);
      ref.invalidate(adminUsersProvider(_query));
    }, success: active ? 'کاربر فعال شد.' : 'کاربر غیرفعال شد.');
  }

  static String _date(DateTime d) {
    final l = d.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${l.year}/${two(l.month)}/${two(l.day)} ${two(l.hour)}:${two(l.minute)}';
  }
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

class _AuditTab extends ConsumerWidget {
  const _AuditTab();

  static const _labels = {
    'ai_settings.update': 'تغییر تنظیمات هوش مصنوعی',
    'ai_settings.test': 'تست اتصال هوش مصنوعی',
    'ai_feature.update': 'تغییر قابلیت هوش مصنوعی',
    'admin.login': 'ورود مدیر',
    'admin.login_failed': 'ورود ناموفق مدیر',
    'admin.login_locked': 'قفل شدن حساب مدیر',
    'user.activate': 'فعال‌سازی کاربر',
    'user.deactivate': 'غیرفعال‌سازی کاربر',
    'role.grant_admin': 'اعطای نقش مدیر',
    'role.revoke_admin': 'لغو نقش مدیر',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final audit = ref.watch(adminAuditProvider);
    return RefreshIndicator(
      onRefresh: () async => ref.refresh(adminAuditProvider.future),
      child: audit.when(
        loading: () => const LoadingView(),
        error: (e, _) => ListView(children: [ErrorView(error: e, onRetry: () => ref.invalidate(adminAuditProvider))]),
        data: (items) => ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (_, i) {
            final e = items[i];
            final l = e.createdAt.toLocal();
            String two(int n) => n.toString().padLeft(2, '0');
            return ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.history_rounded),
              title: Text(_labels[e.action] ?? e.action),
              subtitle: Text('${l.year}/${two(l.month)}/${two(l.day)} ${two(l.hour)}:${two(l.minute)}'),
            );
          },
        ),
      ),
    );
  }
}

Future<bool> _confirm(BuildContext context, String title, String message) async {
  final ok = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('انصراف')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('تأیید')),
      ],
    ),
  );
  return ok ?? false;
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: const Color(0xFFFFF4E0), borderRadius: BorderRadius.circular(12)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline_rounded, size: 18, color: AppColors.warning),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 12))),
        ],
      ),
    );
  }
}
