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
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/** Save an explicitly requested backup/report through Android's document picker.
 * No broad storage permission, hard-coded destination or cloud upload. */
@CapacitorPlugin(name = "PestinoFiles")
public class PestinoFilesPlugin extends Plugin {
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
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_TITLE, name);
        try {
            startActivityForResult(call, intent, "documentCreated");
        } catch (Exception error) {
            call.reject("انتخاب‌گر ذخیره فایل در این دستگاه در دسترس نیست.");
        }
    }

    @ActivityCallback
    private void documentCreated(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) {
            JSObject data = new JSObject();
            data.put("cancelled", true);
            call.resolve(data);
            return;
        }
        getBridge().execute(() -> {
            try (OutputStream output = getContext().getContentResolver().openOutputStream(result.getData().getData(), "wt")) {
                String content = call.getString("content");
                if (output == null || content == null) throw new java.io.IOException();
                output.write(content.getBytes(StandardCharsets.UTF_8));
                output.flush();
                call.resolve(new JSObject());
            } catch (Exception error) {
                call.reject("فایل ذخیره نشد. فضای آزاد و محل انتخابی را بررسی کنید.");
            }
        });
    }
}
