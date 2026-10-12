import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../auth/domain/auth_entities.dart';
import '../../auth/presentation/auth_controller.dart';

/// Shared form for onboarding and profile editing.
class ProfileForm extends ConsumerStatefulWidget {
  const ProfileForm({super.key, required this.user, required this.submitLabel, required this.onSaved});

  final AuthUser user;
  final String submitLabel;
  final VoidCallback onSaved;

  @override
  ConsumerState<ProfileForm> createState() => _ProfileFormState();
}

class _ProfileFormState extends ConsumerState<ProfileForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name = TextEditingController(text: widget.user.fullName ?? '');
  late final TextEditingController _province = TextEditingController(text: widget.user.province ?? '');
  late final TextEditingController _city = TextEditingController(text: widget.user.city ?? '');
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _province.dispose();
    _city.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _busy = true);
    try {
      final updated = await ref.read(authRepositoryProvider).updateProfile(
            fullName: _name.text.trim(),
            province: _province.text.trim(),
            city: _city.text.trim(),
          );
      ref.read(authControllerProvider.notifier).updateUser(updated);
      widget.onSaved();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _name,
            decoration: const InputDecoration(labelText: 'نام و نام خانوادگی'),
            validator: (v) => (v == null || v.trim().length < 2) ? 'نام را وارد کنید' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _province,
            decoration: const InputDecoration(labelText: 'استان'),
            validator: (v) => (v == null || v.trim().length < 2) ? 'استان را وارد کنید' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _city,
            decoration: const InputDecoration(labelText: 'شهر'),
            validator: (v) => (v == null || v.trim().length < 2) ? 'شهر را وارد کنید' : null,
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _busy ? null : _save,
            child: _busy
                ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                : Text(widget.submitLabel),
          ),
        ],
      ),
    );
  }
}
