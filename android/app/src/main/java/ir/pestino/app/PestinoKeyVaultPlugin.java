package ir.pestino.app;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** No plaintext keys enter backups, files, logs or APK assets. */
@CapacitorPlugin(name = "PestinoKeyVault")
public class PestinoKeyVaultPlugin extends Plugin {
    @PluginMethod
    public synchronized void get(PluginCall call) {
        try {
            String value = new DeviceKeyVault(getContext()).read();
            JSObject result = new JSObject();
            result.put("value", value == null ? org.json.JSONObject.NULL : value);
            call.resolve(result);
        } catch (Exception error) {
            call.reject("خواندن کلید ذخیره‌شده ممکن نشد؛ داده‌های دستگاه را پاک نکنید.");
        }
    }
    @PluginMethod
    public synchronized void set(PluginCall call) {
        try {
            new DeviceKeyVault(getContext()).write(call.getString("value"));
            call.resolve();
        } catch (Exception error) {
            call.reject("ذخیرهٔ پایدار کلید تأیید نشد؛ دوباره تلاش کنید.");
        }
    }
}
