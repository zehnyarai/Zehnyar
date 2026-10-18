package ir.pestino.app;

import static org.junit.Assert.*;
import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;

/** Dummy keys only, on fresh disposable CI emulators; never the owner's account. */
@RunWith(AndroidJUnit4.class)
public class DeviceKeyVaultTest {
    private Context context() { return InstrumentationRegistry.getInstrumentation().getTargetContext(); }
    @Test public void encryptedPersistenceAcrossFreshInstances() throws Exception {
        DeviceKeyVault vault = new DeviceKeyVault(context());
        String previous = vault.read();
        try {
            String value = "{\"version\":2,\"slots\":{\"gemini\":{\"key\":\"dummy-google-native\"},\"grok\":{\"key\":\"dummy-xai-native\"}}}";
            vault.write(value);
            String encrypted = vault.prefs().getString("encrypted", "");
            assertFalse(encrypted.contains("dummy-google-native"));
            assertFalse(encrypted.contains("dummy-xai-native"));
            assertEquals(value, new DeviceKeyVault(context()).read());
            vault.write(value);
            assertNotEquals(encrypted, vault.prefs().getString("encrypted", "")); // fresh GCM nonce
            assertEquals(value, new DeviceKeyVault(context()).read());
        } finally { if (previous == null) vault.prefs().edit().clear().commit(); else vault.write(previous); }
    }
    @Test public void deletionDoesNotResurrectPreviousKey() throws Exception {
        DeviceKeyVault vault = new DeviceKeyVault(context());
        String previous = vault.read();
        try {
            vault.write("{\"slots\":{\"gemini\":{\"key\":\"dummy-google\"},\"grok\":{\"key\":\"dummy-grok\"}}}");
            String deleted = "{\"slots\":{\"gemini\":{\"key\":\"dummy-google\"},\"grok\":{\"key\":\"\"}}}";
            vault.write(deleted);
            assertEquals(deleted, new DeviceKeyVault(context()).read());
            assertFalse(new DeviceKeyVault(context()).read().contains("dummy-grok"));
        } finally { if (previous == null) vault.prefs().edit().clear().commit(); else vault.write(previous); }
    }
}
