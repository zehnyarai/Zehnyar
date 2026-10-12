import 'auth_entities.dart';

/// Contract for authentication. Implemented in the data layer.
abstract interface class AuthRepository {
  /// Sends a one-time code to [phone]. Throws AppFailure on invalid phone or cooldown.
  Future<OtpChallenge> requestOtp(String phone);

  /// Verifies the code, stores the session and returns the signed-in user.
  Future<({AuthUser user, bool isNewUser})> verifyOtp({required String phone, required String code});

  /// Returns the current user if a valid session exists, otherwise null.
  Future<AuthUser?> restoreSession();

  Future<AuthUser> updateProfile({String? fullName, String? province, String? city});

  /// Revokes the refresh token on the server and clears local tokens.
  Future<void> logout();
}
