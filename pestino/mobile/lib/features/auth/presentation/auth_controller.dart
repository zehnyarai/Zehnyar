import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../../../core/errors/app_failure.dart';
import '../domain/auth_entities.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState {
  const AuthState({required this.status, this.user, this.error});

  final AuthStatus status;
  final AuthUser? user;

  /// Set when the session could not be restored (e.g. offline at launch).
  final String? error;

  bool get isAuthenticated => status == AuthStatus.authenticated && user != null;
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() => const AuthState(status: AuthStatus.unknown);

  /// Called once at launch (splash) to restore the stored session.
  Future<void> bootstrap() async {
    state = const AuthState(status: AuthStatus.unknown);
    try {
      final user = await ref.read(authRepositoryProvider).restoreSession();
      state = user == null
          ? const AuthState(status: AuthStatus.unauthenticated)
          : AuthState(status: AuthStatus.authenticated, user: user);
    } catch (e) {
      final failure = AppFailure.from(e);
      // Offline at launch: keep the user on splash with a retry option instead of logging them out.
      state = AuthState(status: AuthStatus.unknown, error: failure.message);
    }
  }

  void signIn(AuthUser user) {
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }

  void updateUser(AuthUser user) {
    state = AuthState(status: AuthStatus.authenticated, user: user);
  }

  /// Invoked by the API client when the refresh token is no longer valid.
  void sessionExpired() {
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}
