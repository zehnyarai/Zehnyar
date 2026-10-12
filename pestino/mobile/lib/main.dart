import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';
import 'core/config/app_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Release builds must talk to the API over HTTPS. Refuse to start otherwise, so a
  // store build can never ship with the development URL.
  if (kReleaseMode && !AppConfig.apiBaseUrl.startsWith('https://')) {
    throw StateError('Release builds require an https API_BASE_URL (got ${AppConfig.apiBaseUrl}).');
  }

  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  runApp(const ProviderScope(child: PestinoApp()));
}
