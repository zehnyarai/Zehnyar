package ir.pestino.app;

import android.app.Activity;
import android.content.Intent;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/** User-requested backup/report, saved through the Android document picker.
 * No broad storage permission or cloud upload. Large content is NOT retained
 * in saved activity state (Binder's size limit is much smaller than a backup). */
@CapacitorPlugin(name = "PestinoFiles")
public class PestinoFilesPlugin extends Plugin {
    @Override
    public void load() {
        File[] leftovers = getContext().getCacheDir().listFiles();
        if (leftovers == null) return;
        for (File file : leftovers) {
            if (file.getName().startsWith("pestino-export-") && file.getName().endsWith(".tmp")
                && file.lastModified() < System.currentTimeMillis() - 86400000L) file.delete();
        }
    }

    @PluginMethod
    public void save(PluginCall call) {
        String name = call.getString("name", "pestino-backup.json");
        String content = call.getString("content");
        String mime = call.getString("mime", "application/json");
        if (content == null || content.getBytes(StandardCharsets.UTF_8).length > 32 * 1024 * 1024
            || name == null || !name.matches("[A-Za-z0-9._-]{1,120}")
            || !("application/json".equals(mime) || "text/plain".equals(mime) || "text/csv".equals(mime))) {
            call.reject("اطلاعات فایل معتبر نیست.");
            return;
        }
        getBridge().execute(() -> {
            File temporary = null;
            try {
                temporary = File.createTempFile("pestino-export-", ".tmp", getContext().getCacheDir());
                try (OutputStream output = new FileOutputStream(temporary)) {
                    output.write(content.getBytes(StandardCharsets.UTF_8));
                }
                call.getData().remove("content");
                call.getData().put("temporaryFile", temporary.getName());
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(mime);
                intent.putExtra(Intent.EXTRA_TITLE, name);
                getBridge().executeOnMainThread(() -> {
                    try { startActivityForResult(call, intent, "documentCreated"); }
                    catch (Exception error) {
                        removeTemporary(call);
                        call.reject("انتخاب‌گر ذخیره فایل در این دستگاه در دسترس نیست.");
                    }
                });
            } catch (Exception error) {
                if (temporary != null) temporary.delete();
                call.reject("آماده‌کردن فایل ممکن نشد. فضای آزاد دستگاه را بررسی کنید.");
            }
        });
    }

    private File temporaryFile(PluginCall call) {
        String name = call.getString("temporaryFile", "");
        if (!name.matches("pestino-export-[A-Za-z0-9-]+\\.tmp")) return null;
        return new File(getContext().getCacheDir(), name);
    }

    private void removeTemporary(PluginCall call) {
        File file = temporaryFile(call);
        if (file != null) file.delete();
    }

    @ActivityCallback
    private void documentCreated(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) {
            removeTemporary(call);
            JSObject data = new JSObject();
            data.put("cancelled", true);
            call.resolve(data);
            return;
        }
        getBridge().execute(() -> {
            File temporary = temporaryFile(call);
            if (temporary == null) { call.reject("فایل موقت در دسترس نیست."); return; }
            try (FileInputStream input = new FileInputStream(temporary);
                 OutputStream output = getContext().getContentResolver().openOutputStream(result.getData().getData(), "wt")) {
                if (output == null) throw new java.io.IOException();
                byte[] buffer = new byte[8192];
                int read;
                while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
                output.flush();
                call.resolve(new JSObject());
            } catch (Exception error) {
                call.reject("فایل ذخیره نشد. فضای آزاد و محل انتخابی را بررسی کنید.");
            } finally { temporary.delete(); }
        });
    }
}
