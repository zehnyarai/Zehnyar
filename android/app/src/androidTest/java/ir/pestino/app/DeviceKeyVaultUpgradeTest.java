package ir.pestino.app;

import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;
import android.content.Context;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;

/** Two separate runner processes, with adb install -r between them. Disposable CI devices ONLY. */
@RunWith(AndroidJUnit4.class)
public class DeviceKeyVaultUpgradeTest {
    private static final String FIXTURE = "{\"version\":2,\"active\":\"grok\",\"slots\":{\"gemini\":{\"key\":\"dummy-upgrade-google\"},\"grok\":{\"key\":\"dummy-upgrade-xai\"}}}";
    @Test public void keysSurviveInPlacePackageReplacement() throws Exception {
        String stage = InstrumentationRegistry.getArguments().getString("pestinoStage");
        assumeTrue(stage != null);
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        DeviceKeyVault vault = new DeviceKeyVault(context);
        if ("seed".equals(stage)) {
            assertNull("Requires a fresh fixture device, never an owner's phone", vault.read());
            vault.write(FIXTURE);
            context.getSharedPreferences("pestino_upgrade_fixture", Context.MODE_PRIVATE).edit().putInt("uid", android.os.Process.myUid()).commit();
        } else {
            assertEquals("verify", stage);
            assertEquals(context.getSharedPreferences("pestino_upgrade_fixture", Context.MODE_PRIVATE).getInt("uid", -1), android.os.Process.myUid());
            assertEquals(FIXTURE, vault.read());
            assertFalse(vault.prefs().getString("encrypted", "").contains("dummy-upgrade"));
            vault.prefs().edit().clear().commit();
            context.getSharedPreferences("pestino_upgrade_fixture", Context.MODE_PRIVATE).edit().clear().commit();
        }
    }
}
