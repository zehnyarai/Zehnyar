import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/analysis/domain/analysis_entities.dart';
import '../features/analysis/presentation/analysis_page.dart';
import '../features/analysis/presentation/report_page.dart';
import '../features/auth/presentation/auth_controller.dart';
import '../features/auth/presentation/login_page.dart';
import '../features/auth/presentation/otp_page.dart';
import '../features/dashboard/presentation/dashboard_page.dart';
import '../features/farms/presentation/farm_form_page.dart';
import '../features/farms/presentation/farm_profile_page.dart';
import '../features/farms/presentation/farms_page.dart';
import '../features/history/presentation/history_page.dart';
import '../features/knowledge/presentation/article_page.dart';
import '../features/knowledge/presentation/knowledge_page.dart';
import '../features/profile/presentation/onboarding_page.dart';
import '../features/profile/presentation/profile_page.dart';
import '../features/shell/presentation/main_shell.dart';
import '../features/splash/presentation/splash_page.dart';
import '../features/subscription/presentation/paywall_page.dart';

/// Route paths. Use these helpers instead of string literals across the app.
class AppRoutes {
  const AppRoutes._();

  static const splash = '/splash';
  static const login = '/login';
  static const otp = '/otp';
  static const onboarding = '/onboarding';
  static const dashboard = '/dashboard';
  static const farms = '/farms';
  static const farmNew = '/farms/new';
  static const analysis = '/analysis/new';
  static const history = '/history';
  static const profile = '/profile';
  static const knowledge = '/knowledge';
  static const paywall = '/paywall';

  static String farm(String id) => '/farms/$id';
  static String farmEdit(String id) => '/farms/$id/edit';
  static String report(String id) => '/reports/$id';
  static String article(String slug) => '/knowledge/$slug';

  static String analysisForFarm(String farmId) => '$analysis?farmId=$farmId';
}

final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen<AuthState>(authControllerProvider, (_, __) => refresh.value++);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final loc = state.matchedLocation;
      final onSplash = loc == AppRoutes.splash;
      final onAuthFlow = loc == AppRoutes.login || loc == AppRoutes.otp;

      switch (auth.status) {
        case AuthStatus.unknown:
          return onSplash ? null : AppRoutes.splash;
        case AuthStatus.unauthenticated:
          return onAuthFlow ? null : AppRoutes.login;
        case AuthStatus.authenticated:
          if (!(onSplash || onAuthFlow)) return null;
          final needsSetup = (auth.user?.province ?? '').isEmpty;
          return needsSetup ? AppRoutes.onboarding : AppRoutes.dashboard;
      }
    },
    routes: [
      GoRoute(path: AppRoutes.splash, builder: (_, __) => const SplashPage()),
      GoRoute(path: AppRoutes.login, builder: (_, __) => const LoginPage()),
      GoRoute(
        path: AppRoutes.otp,
        builder: (_, state) => OtpPage(args: state.extra as OtpArgs),
      ),
      GoRoute(path: AppRoutes.onboarding, builder: (_, __) => const OnboardingPage()),
      GoRoute(path: AppRoutes.paywall, builder: (_, __) => const PaywallPage()),
      GoRoute(
        path: AppRoutes.analysis,
        builder: (_, state) => AnalysisPage(initialFarmId: state.uri.queryParameters['farmId']),
      ),
      GoRoute(path: AppRoutes.farmNew, builder: (_, __) => const FarmFormPage()),
      GoRoute(
        path: '/farms/:farmId',
        builder: (_, state) => FarmProfilePage(farmId: state.pathParameters['farmId']!),
        routes: [
          GoRoute(
            path: 'edit',
            builder: (_, state) => FarmFormPage(farmId: state.pathParameters['farmId']),
          ),
        ],
      ),
      GoRoute(
        path: '/reports/:analysisId',
        builder: (_, state) => ReportPage(
          analysisId: state.pathParameters['analysisId']!,
          initial: state.extra is Analysis ? state.extra as Analysis : null,
        ),
      ),
      GoRoute(path: AppRoutes.knowledge, builder: (_, __) => const KnowledgePage()),
      GoRoute(
        path: '/knowledge/:slug',
        builder: (_, state) => ArticlePage(slug: state.pathParameters['slug']!),
      ),
      StatefulShellRoute.indexedStack(
        builder: (_, __, shell) => MainShell(navigationShell: shell),
        branches: [
          StatefulShellBranch(routes: [
            GoRoute(path: AppRoutes.dashboard, builder: (_, __) => const DashboardPage()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: AppRoutes.farms, builder: (_, __) => const FarmsPage()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: AppRoutes.history, builder: (_, __) => const HistoryPage()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: AppRoutes.profile, builder: (_, __) => const ProfilePage()),
          ]),
        ],
      ),
    ],
  );
});
