import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../app/router.dart';
import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/utils/persian.dart';
import '../../../core/widgets/common_widgets.dart';
import '../../farms/presentation/farm_providers.dart';
import '../domain/analysis_entities.dart';
import 'analysis_providers.dart';

/// Capture / pick an image, add context (farm, season, tree age) and run the AI analysis.
class AnalysisPage extends ConsumerStatefulWidget {
  const AnalysisPage({super.key, this.initialFarmId});

  final String? initialFarmId;

  @override
  ConsumerState<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends ConsumerState<AnalysisPage> {
  static const categories = {
    'leaf': ('برگ', Icons.eco_rounded),
    'fruit_cluster': ('خوشه میوه', Icons.grain_rounded),
    'trunk': ('تنه / شاخه', Icons.forest_rounded),
    'pest': ('آفت', Icons.bug_report_rounded),
    'soil': ('خاک', Icons.terrain_rounded),
  };

  static const seasons = {'spring': 'بهار', 'summer': 'تابستان', 'autumn': 'پاییز', 'winter': 'زمستان'};

  final _picker = ImagePicker();
  final _treeAge = TextEditingController();
  final _location = TextEditingController();
  final _notes = TextEditingController();

  String? _imagePath;
  String _category = 'leaf';
  late String _season;
  String? _farmId;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _season = _currentSeason();
    _farmId = widget.initialFarmId;
  }

  @override
  void dispose() {
    _treeAge.dispose();
    _location.dispose();
    _notes.dispose();
    super.dispose();
  }

  /// Persian calendar: 1–3 spring, 4–6 summer, 7–9 autumn, 10–12 winter.
  static String _currentSeason() {
    final month = Persian.toJalali(DateTime.now())[1];
    if (month <= 3) return 'spring';
    if (month <= 6) return 'summer';
    if (month <= 9) return 'autumn';
    return 'winter';
  }

  Future<void> _pick(ImageSource source) async {
    try {
      final file = await _picker.pickImage(source: source, maxWidth: 2048, maxHeight: 2048, imageQuality: 85);
      if (file != null) setState(() => _imagePath = file.path);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('دسترسی به دوربین یا گالری فراهم نیست. آن را در تنظیمات مجاز کنید.')),
      );
    }
  }

  Future<void> _submit() async {
    if (_imagePath == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('ابتدا یک تصویر انتخاب کنید.')));
      return;
    }
    setState(() => _busy = true);
    try {
      final treeAge = int.tryParse(Persian.toAscii(_treeAge.text.trim()));
      final analysis = await ref.read(analysisRepositoryProvider).create(
            NewAnalysisInput(
              filePath: _imagePath!,
              category: _category,
              season: _season,
              farmId: _farmId,
              treeAgeYears: treeAge,
              location: _location.text.trim().isEmpty ? null : _location.text.trim(),
              userNotes: _notes.text.trim().isEmpty ? null : _notes.text.trim(),
            ),
          );
      ref.invalidate(analysisUsageProvider);
      if (!mounted) return;
      context.pushReplacement(AppRoutes.report(analysis.summary.id), extra: analysis);
    } catch (e) {
      if (!mounted) return;
      ref.invalidate(analysisUsageProvider);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(AppFailure.from(e).message)));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final usage = ref.watch(analysisUsageProvider);
    final farms = ref.watch(farmsListProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('تحلیل تصویر')),
      body: Stack(
        children: [
          ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 120),
            children: [
              usage.maybeWhen(
                data: (u) => _UsageBanner(usage: u),
                orElse: () => const SizedBox.shrink(),
              ),
              const SizedBox(height: 12),
              _ImagePickerCard(
                path: _imagePath,
                onCamera: () => _pick(ImageSource.camera),
                onGallery: () => _pick(ImageSource.gallery),
              ),
              const SizedBox(height: 20),
              const _Label('نوع نمونه'),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final e in categories.entries)
                    ChoiceChip(
                      avatar: Icon(e.value.$2, size: 18, color: _category == e.key ? AppColors.green700 : AppColors.inkSoft),
                      label: Text(e.value.$1),
                      selected: _category == e.key,
                      onSelected: (_) => setState(() => _category = e.key),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              const _Label('فصل'),
              Wrap(
                spacing: 8,
                children: [
                  for (final e in seasons.entries)
                    ChoiceChip(
                      label: Text(e.value),
                      selected: _season == e.key,
                      onSelected: (_) => setState(() => _season = e.key),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              const _Label('اطلاعات باغ'),
              farms.when(
                loading: () => const LinearProgressIndicator(),
                error: (_, __) => const SizedBox.shrink(),
                data: (items) => DropdownButtonFormField<String?>(
                  initialValue: items.any((f) => f.id == _farmId) ? _farmId : null,
                  decoration: const InputDecoration(labelText: 'باغ (اختیاری)'),
                  items: [
                    const DropdownMenuItem<String?>(value: null, child: Text('بدون انتخاب باغ')),
                    for (final f in items) DropdownMenuItem<String?>(value: f.id, child: Text(f.name)),
                  ],
                  onChanged: (v) => setState(() => _farmId = v),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _treeAge,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'سن درخت (سال)'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _location,
                      decoration: const InputDecoration(labelText: 'موقعیت (اختیاری)'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _notes,
                maxLines: 3,
                maxLength: 1000,
                decoration: const InputDecoration(
                  labelText: 'توضیحات (علائم مشاهده‌شده، از کی شروع شده، ...)',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 8),
              PestinoCard(
                color: AppColors.earth100,
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    const Icon(Icons.lightbulb_outline_rounded, color: AppColors.earth700),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'برای نتیجه دقیق‌تر: یک عکس نزدیک از نمونه، در نور روز و بدون فلاش بگیرید. برای برگ، پشت برگ را هم عکس بگیرید.',
                        style: theme.textTheme.bodySmall?.copyWith(color: AppColors.earth700),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (_busy) const _AnalyzingOverlay(),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: usage.maybeWhen(
            data: (u) => FilledButton.icon(
              onPressed: (_busy || u.exhausted || _imagePath == null) ? null : _submit,
              icon: const Icon(Icons.auto_awesome_rounded),
              label: Text(u.exhausted ? 'سهمیه ماهانه تمام شده' : 'شروع تحلیل هوشمند'),
            ),
            orElse: () => FilledButton.icon(
              onPressed: (_busy || _imagePath == null) ? null : _submit,
              icon: const Icon(Icons.auto_awesome_rounded),
              label: const Text('شروع تحلیل هوشمند'),
            ),
          ),
        ),
      ),
    );
  }
}

class _Label extends StatelessWidget {
  const _Label(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Text(text, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800)),
      );
}

class _ImagePickerCard extends StatelessWidget {
  const _ImagePickerCard({required this.path, required this.onCamera, required this.onGallery});

  final String? path;
  final VoidCallback onCamera;
  final VoidCallback onGallery;

  @override
  Widget build(BuildContext context) {
    return PestinoCard(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            child: AspectRatio(
              aspectRatio: 4 / 3,
              child: path == null
                  ? Container(
                      color: AppColors.green50,
                      child: const EmptyState(
                        icon: Icons.add_a_photo_rounded,
                        title: 'تصویر نمونه را انتخاب کنید',
                        message: 'عکس از دوربین یا گالری',
                      ),
                    )
                  : Image.file(File(path!), fit: BoxFit.cover),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onCamera,
                    icon: const Icon(Icons.photo_camera_rounded),
                    label: const Text('دوربین'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: onGallery,
                    icon: const Icon(Icons.photo_library_rounded),
                    label: const Text('گالری'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _UsageBanner extends StatelessWidget {
  const _UsageBanner({required this.usage});

  final AnalysisUsage usage;

  @override
  Widget build(BuildContext context) {
    final exhausted = usage.exhausted;
    final color = exhausted ? AppColors.danger : AppColors.green700;
    return PestinoCard(
      color: exhausted ? const Color(0xFFFCEBEA) : AppColors.green50,
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Icon(exhausted ? Icons.lock_rounded : Icons.workspace_premium_rounded, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              usage.isUnlimited
                  ? 'طرح ${usage.planName}: تحلیل نامحدود'
                  : 'طرح ${usage.planName}: ${Persian.digits(usage.remaining ?? 0)} تحلیل باقی‌مانده این ماه',
              style: TextStyle(color: color, fontWeight: FontWeight.w700),
            ),
          ),
          if (exhausted)
            TextButton(onPressed: () => context.push(AppRoutes.paywall), child: const Text('ارتقا')),
        ],
      ),
    );
  }
}

class _AnalyzingOverlay extends StatelessWidget {
  const _AnalyzingOverlay();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black.withValues(alpha: 0.45),
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(32),
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 20),
              Text('در حال تحلیل تصویر…', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              SizedBox(height: 8),
              Text('کارشناس هوشمند پستینو در حال بررسی نشانه‌هاست. چند ثانیه صبر کنید.', textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
