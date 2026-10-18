package ir.pestino.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Separated so actual AndroidKeyStore persistence can be tested on API 24 and 35. */
final class DeviceKeyVault {
    private final Context context;
    DeviceKeyVault(Context context) { this.context = context; }
    private static final String ALIAS = "pestino.provider.settings.v1";
    SharedPreferences prefs() {
        return context.getSharedPreferences("pestino_provider_vault", Context.MODE_PRIVATE);
    }
    private SecretKey secret() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) return (SecretKey) store.getKey(ALIAS, null);
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return generator.generateKey();
    }
    private String decrypt(String encoded) throws Exception {
        String[] parts = encoded.split(":", -1);
        if (parts.length != 2) throw new IllegalArgumentException();
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, secret(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
        return new String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), StandardCharsets.UTF_8);
    }
    synchronized String read() throws Exception {
        String encoded = prefs().getString("encrypted", null);
        return encoded == null ? null : decrypt(encoded);
    }
    synchronized void write(String value) throws Exception {
        if (value == null || value.length() > 30000) throw new IllegalArgumentException();
        new org.json.JSONObject(value);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, secret());
        String encoded = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + ":" +
            Base64.encodeToString(cipher.doFinal(value.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
        if (!prefs().edit().putString("encrypted", encoded).commit() || !value.equals(read()))
            throw new IllegalStateException("Durable write not verified");
    }
}
