import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import 'auth_controller.dart';

/// Arguments passed from the login page.
class OtpArgs {
  const OtpArgs({required this.phone, required this.expiresIn, this.devCode});

  final String phone;
  final int expiresIn;
  final String? devCode;
}

class OtpPage extends ConsumerStatefulWidget {
  const OtpPage({super.key, required this.args});

  final OtpArgs args;

  @override
  ConsumerState<OtpPage> createState() => _OtpPageState();
}

class _OtpPageState extends ConsumerState<OtpPage> {
  static const _resendAfter = 60;

  final _code = TextEditingController();
  Timer? _timer;
  late int _secondsLeft;
  int _sinceSent = 0;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _secondsLeft = widget.args.expiresIn;
    _startTimer();
    if (widget.args.devCode != null) {
      // Development backends echo the code. Pre-fill to speed up testing.
      _code.text = widget.args.devCode!;
    }
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() {
        if (_secondsLeft > 0) _secondsLeft--;
        _sinceSent++;
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _code.dispose();
    super.dispose();
  }

  Future<void> _verify() async {
    final code = Persian.toAscii(_code.text).trim();
    if (!RegExp(r'^\d{6}$').hasMatch(code)) {
      setState(() => _error = 'کد ۶ رقمی را وارد کنید');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await ref.read(authRepositoryProvider).verifyOtp(phone: widget.args.phone, code: code);
      ref.read(authControllerProvider.notifier).signIn(result.user);
      if (!mounted) return;
      context.go(result.user.fullName == null ? '/onboarding' : '/dashboard');
    } catch (e) {
      setState(() => _error = AppFailure.from(e).message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _resend() async {
    try {
      final challenge = await ref.read(authRepositoryProvider).requestOtp(widget.args.phone);
      if (!mounted) return;
      setState(() {
        _secondsLeft = challenge.expiresInSeconds;
        _sinceSent = 0;
        if (challenge.devCode != null) _code.text = challenge.devCode!;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final canResend = _sinceSent >= _resendAfter;
    final mm = (_secondsLeft ~/ 60).toString().padLeft(2, '0');
    final ss = (_secondsLeft % 60).toString().padLeft(2, '0');

    return Scaffold(
      appBar: AppBar(title: const Text('تأیید شماره')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('کد ۶ رقمی ارسال‌شده به', textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
                  const SizedBox(height: 4),
                  Text(Persian.phoneDisplay(widget.args.phone), textAlign: TextAlign.center, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 28),
                  TextField(
                    controller: _code,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    textDirection: TextDirection.ltr,
                    maxLength: 6,
                    autofillHints: const [AutofillHints.oneTimeCode],
                    style: theme.textTheme.headlineSmall?.copyWith(letterSpacing: 10, fontWeight: FontWeight.w700),
                    decoration: InputDecoration(counterText: '', errorText: _error),
                    onChanged: (_) {
                      if (Persian.toAscii(_code.text).length == 6 && !_busy) _verify();
                    },
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _secondsLeft > 0 ? 'اعتبار کد: ${Persian.digits('$mm:$ss')}' : 'کد منقضی شده است',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft),
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: _busy ? null : _verify,
                    child: _busy
                        ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                        : const Text('ورود'),
                  ),
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: canResend ? _resend : null,
                    child: Text(canResend ? 'ارسال مجدد کد' : 'ارسال مجدد تا ${Persian.digits(_resendAfter - _sinceSent)} ثانیه دیگر'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
