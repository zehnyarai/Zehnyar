import 'package:flutter/material.dart';

/// Pestino colour system: natural green (primary), pistachio/earth tones (secondary).
class AppColors {
  const AppColors._();

  // Primary – natural green
  static const green900 = Color(0xFF1B3D22);
  static const green700 = Color(0xFF2F6B3A);
  static const green600 = Color(0xFF3B8048);
  static const green500 = Color(0xFF4E9A5A);
  static const green100 = Color(0xFFDDEFD9);
  static const green50 = Color(0xFFEFF7EC);

  // Secondary – earth & pistachio shell
  static const earth700 = Color(0xFF6B4E33);
  static const earth500 = Color(0xFF8B6B4A);
  static const earth100 = Color(0xFFEFE4D6);
  static const pistachio = Color(0xFFA7C957);
  static const shell = Color(0xFFD9B98A);

  // Neutrals
  static const sand = Color(0xFFF7F4EC);
  static const surface = Color(0xFFFFFFFF);
  static const ink = Color(0xFF1F2A22);
  static const inkSoft = Color(0xFF5B6660);
  static const outline = Color(0xFFD9DED6);

  // Semantic
  static const success = Color(0xFF2E7D32);
  static const warning = Color(0xFFC77700);
  static const danger = Color(0xFFB3261E);
  static const info = Color(0xFF1565C0);

  static Color confidence(int value) {
    if (value >= 75) return success;
    if (value >= 50) return warning;
    return danger;
  }

  static Color priority(String p) => switch (p) {
        'immediate' => danger,
        'soon' => warning,
        _ => info,
      };
}
