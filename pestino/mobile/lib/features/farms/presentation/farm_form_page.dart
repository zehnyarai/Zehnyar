import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../domain/farm_entities.dart';
import '../../ai/domain/ai_repository.dart';
import '../../ai/presentation/ai_assist_sheet.dart';
import 'farm_providers.dart';

/// Create (farmId == null) or edit a farm.
class FarmFormPage extends ConsumerWidget {
  const FarmFormPage({super.key, this.farmId});

  final String? farmId;

  static const irrigationOptions = {
    'drip': 'قطره‌ای',
    'micro_sprinkler': 'میکرو بارانی',
    'sprinkler': 'بارانی',
    'flood': 'غرقابی',
    'rainfed': 'دیم',
    'other': 'سایر',
  };

  static const varieties = ['اوحدی', 'اکبری', 'کله‌قوچی', 'فندقی', 'احمدآقایی', 'سفید', 'سایر'];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (farmId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('ثبت باغ جدید')),
        body: const _FarmForm(initial: null),
      );
    }
    final async = ref.watch(farmDetailProvider(farmId!));
    return Scaffold(
      appBar: AppBar(title: const Text('ویرایش باغ')),
      body: async.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(error: e, onRetry: () => ref.invalidate(farmDetailProvider(farmId!))),
        data: (farm) => _FarmForm(initial: farm),
      ),
    );
  }
}

class _FarmForm extends ConsumerStatefulWidget {
  const _FarmForm({required this.initial});

  final Farm? initial;

  @override
  ConsumerState<_FarmForm> createState() => _FarmFormState();
}

class _FarmFormState extends ConsumerState<_FarmForm> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final TextEditingController _province;
  late final TextEditingController _city;
  late final TextEditingController _area;
  late final TextEditingController _treeAge;
  late final TextEditingController _soilNotes;
  String? _variety;
  String? _irrigation;
  String? _soilType;
  bool _busy = false;

  static const _soilTypes = {'loam': 'لومی', 'clay': 'رسی', 'sandy': 'شنی', 'saline': 'شور', 'calcareous': 'آهکی'};

  @override
  void initState() {
    super.initState();
    final f = widget.initial;
    _name = TextEditingController(text: f?.name ?? '');
    _province = TextEditingController(text: f?.province ?? '');
    _city = TextEditingController(text: f?.city ?? '');
    _area = TextEditingController(text: f?.areaHectares?.toString() ?? '');
    _treeAge = TextEditingController(text: f?.averageTreeAge?.toString() ?? '');
    _soilNotes = TextEditingController(text: f?.soilNotes ?? '');
    _variety = f?.pistachioVariety;
    _irrigation = f?.irrigationMethod;
    _soilType = f?.soilType;
  }

  @override
  void dispose() {
    for (final c in [_name, _province, _city, _area, _treeAge, _soilNotes]) {
      c.dispose();
    }
    super.dispose();
  }

  double? _parseDouble(String s) {
    final v = Persian.toAscii(s.trim());
    return v.isEmpty ? null : double.tryParse(v);
  }

  int? _parseInt(String s) {
    final v = Persian.toAscii(s.trim());
    return v.isEmpty ? null : int.tryParse(v);
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _busy = true);
    final input = FarmInput(
      name: _name.text.trim(),
      province: _province.text.trim(),
      city: _city.text.trim(),
      areaHectares: _parseDouble(_area.text),
      pistachioVariety: _variety,
      averageTreeAge: _parseInt(_treeAge.text),
      irrigationMethod: _irrigation,
      soilType: _soilType,
      soilNotes: _soilNotes.text.trim().isEmpty ? null : _soilNotes.text.trim(),
    );
    try {
      final repo = ref.read(farmRepositoryProvider);
      if (widget.initial == null) {
        await repo.create(input);
      } else {
        await repo.update(widget.initial!.id, input);
        ref.invalidate(farmDetailProvider(widget.initial!.id));
      }
      ref.invalidate(farmsListProvider);
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Keeps an existing (possibly legacy) value selectable so the dropdown never asserts.
  static List<String> _withCurrent(List<String> options, String? current) {
    if (current == null || options.contains(current)) return options;
    return [...options, current];
  }

  String? _required(String? v) => (v == null || v.trim().length < 2) ? 'این فیلد الزامی است' : null;

  String? _optionalNumber(String? v) {
    if (v == null || v.trim().isEmpty) return null;
    return _parseDouble(v) == null ? 'عدد معتبر وارد کنید' : null;
  }

  /// Asks the backend for a short AI hint about one field, with the farm's context.
  Future<void> _help(String field, String? displayValue) async {
    if (displayValue == null || displayValue.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ابتدا برای این فیلد یک مقدار انتخاب کنید.')));
      return;
    }
    await showAiAssistSheet(
      context,
      feature: 'farm_form_help',
      field: field,
      value: displayValue,
      details: AiAssistDetails(
        province: _province.text.trim(),
        city: _city.text.trim(),
        pistachioVariety: _variety,
        treeAgeYears: int.tryParse(_treeAge.text.trim()),
        irrigationMethod: FarmFormPage.irrigationOptions[_irrigation] ?? _irrigation,
        soilType: _soilTypes[_soilType] ?? _soilType,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          const _SectionLabel('اطلاعات باغ'),
          TextFormField(
            controller: _name,
            decoration: const InputDecoration(labelText: 'نام باغ *'),
            validator: _required,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _province,
                  decoration: const InputDecoration(labelText: 'استان *'),
                  validator: _required,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _city,
                  decoration: const InputDecoration(labelText: 'شهر *'),
                  validator: _required,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _area,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'مساحت (هکتار)'),
                  validator: _optionalNumber,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _treeAge,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'میانگین سن درخت'),
                  validator: _optionalNumber,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _variety,
            decoration: InputDecoration(
              labelText: 'رقم پسته',
              suffixIcon: _AiHelpButton(tooltip: 'کمک هوشمند رقم', onPressed: () => _help('رقم پسته', _variety)),
            ),
            items: [
              for (final v in _withCurrent(FarmFormPage.varieties, _variety)) DropdownMenuItem(value: v, child: Text(v)),
            ],
            onChanged: (v) => setState(() => _variety = v),
          ),
          const SizedBox(height: 24),
          const _SectionLabel('آبیاری و خاک'),
          DropdownButtonFormField<String>(
            initialValue: _irrigation,
            decoration: InputDecoration(
              labelText: 'روش آبیاری',
              suffixIcon: _AiHelpButton(
                tooltip: 'کمک هوشمند آبیاری',
                onPressed: () => _help('روش آبیاری', FarmFormPage.irrigationOptions[_irrigation] ?? _irrigation),
              ),
            ),
            items: [for (final e in FarmFormPage.irrigationOptions.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
            onChanged: (v) => setState(() => _irrigation = v),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _soilType,
            decoration: InputDecoration(
              labelText: 'نوع خاک',
              suffixIcon: _AiHelpButton(
                tooltip: 'کمک هوشمند خاک',
                onPressed: () => _help('نوع خاک', _soilTypes[_soilType] ?? _soilType),
              ),
            ),
            items: [
              for (final e in _soilTypes.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
              if (_soilType != null && !_soilTypes.containsKey(_soilType))
                DropdownMenuItem(value: _soilType, child: Text(_soilType!)),
            ],
            onChanged: (v) => setState(() => _soilType = v),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _soilNotes,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'یادداشت خاک (اختیاری)', alignLabelWithHint: true),
          ),
          const SizedBox(height: 28),
          FilledButton(
            onPressed: _busy ? null : _save,
            child: _busy
                ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                : Text(widget.initial == null ? 'ثبت باغ' : 'ذخیره تغییرات'),
          ),
        ],
      ),
    );
  }
}

/// Small sparkle button shown inside a form field.
class _AiHelpButton extends StatelessWidget {
  const _AiHelpButton({required this.tooltip, required this.onPressed});

  final String tooltip;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: tooltip,
      icon: const Icon(Icons.auto_awesome_rounded),
      onPressed: onPressed,
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4, bottom: 12),
      child: Text(text, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
    );
  }
}
