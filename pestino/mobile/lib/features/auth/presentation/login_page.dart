import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/app_config.dart';
import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../app/router.dart';
import 'otp_page.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _phone = TextEditingController();
  bool _busy = false;

  static final _iranMobile = RegExp(r'^09\d{9}$');

  @override
  void dispose() {
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _busy = true);
    final phone = Persian.toAscii(_phone.text).replaceAll(RegExp(r'[\s\-]'), '');
    try {
      final challenge = await ref.read(authRepositoryProvider).requestOtp(phone);
      if (!mounted) return;
      context.push(
        AppRoutes.otp,
        extra: OtpArgs(phone: phone, expiresIn: challenge.expiresInSeconds, devCode: challenge.devCode),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 24),
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(colors: [AppColors.green600, AppColors.green900], begin: Alignment.topLeft, end: Alignment.bottomRight),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.eco_rounded, size: 56, color: Colors.white),
                    ),
                    const SizedBox(height: 24),
                    Text('ورود به ${AppConfig.appName}', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800), textAlign: TextAlign.center),
                    const SizedBox(height: 8),
                    Text(
                      'شماره موبایل خود را وارد کنید تا کد ورود برایتان پیامک شود.',
                      style: theme.textTheme.bodyMedium?.copyWith(color: AppColors.inkSoft),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    TextFormField(
                      controller: _phone,
                      keyboardType: TextInputType.phone,
                      textDirection: TextDirection.ltr,
                      textAlign: TextAlign.center,
                      autofillHints: const [AutofillHints.telephoneNumber],
                      decoration: const InputDecoration(labelText: 'شماره موبایل', hintText: '۰۹۱۲۳۴۵۶۷۸۹', prefixIcon: Icon(Icons.phone_iphone_rounded)),
                      validator: (value) {
                        final v = Persian.toAscii(value ?? '').replaceAll(RegExp(r'[\s\-]'), '');
                        if (!_iranMobile.hasMatch(v)) return 'شماره موبایل معتبر وارد کنید';
                        return null;
                      },
                      onFieldSubmitted: (_) => _submit(),
                    ),
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: _busy
                          ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                          : const Text('دریافت کد ورود'),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'با ورود به پستینو، شرایط استفاده و سیاست حریم خصوصی را می‌پذیرید.',
                      style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
