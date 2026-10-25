package ai.mohajeryar.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.webkit.WebViewAssetLoader;

import org.json.JSONObject;

import java.net.HttpURLConnection;
import java.net.URL;

/**
 * پوستهٔ بومی مهاجریار.
 *
 * در نخستین اجرا، صفحهٔ راه‌اندازی از کاربر آدرس سرور را می‌گیرد، اتصال را با
 * /api/health می‌سنجد و در SharedPreferences ذخیره می‌کند. سپس همان آدرس در
 * WebView بارگذاری می‌شود. این کار باعث می‌شود یک APK برای هر استقرار
 * (دامنهٔ عمومی، سرور شخصی یا شبکهٔ محلی) کار کند.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "mohajeryar";
    private static final String KEY_SERVER = "server_url";
    private static final String START_PAGE = "https://appassets.androidplatform.net/assets/index.html";

    private WebView webView;
    private SharedPreferences prefs;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setUserAgentString(settings.getUserAgentString() + " MohajeryarApp/1.0");

        webView.addJavascriptInterface(new Bridge(), "Mohajeryar");

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                if (scheme.equals("http") || scheme.equals("https")) {
                    String saved = savedServer();
                    if (!saved.isEmpty() && uri.toString().startsWith(saved)) {
                        return false;
                    }
                    if (uri.toString().startsWith("https://appassets.androidplatform.net")) {
                        return false;
                    }
                    openExternal(uri);
                    return true;
                }
                if (scheme.equals("mailto") || scheme.equals("tel")) {
                    openExternal(uri);
                    return true;
                }
                return false;
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    String saved = savedServer();
                    if (!saved.isEmpty()) {
                        view.loadUrl("https://appassets.androidplatform.net/assets/offline.html");
                    }
                }
            }
        });

        webView.loadUrl(savedServer().isEmpty() ? START_PAGE : savedServer());
    }

    private String savedServer() {
        return prefs.getString(KEY_SERVER, "");
    }

    private void openExternal(Uri uri) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (Exception ignored) {
            Toast.makeText(this, "برنامه‌ای برای باز کردن این پیوند پیدا نشد.", Toast.LENGTH_SHORT).show();
        }
    }

    /** پل جاوااسکریپت برای صفحهٔ راه‌اندازی و مدیریت اتصال. */
    private class Bridge {

        @JavascriptInterface
        public String saved() {
            return savedServer();
        }

        @JavascriptInterface
        public void save(String url) {
            prefs.edit().putString(KEY_SERVER, url).apply();
        }

        @JavascriptInterface
        public void clear() {
            prefs.edit().remove(KEY_SERVER).apply();
        }

        @JavascriptInterface
        public void load(final String url) {
            runOnUiThread(() -> webView.loadUrl(url));
        }

        @JavascriptInterface
        public void setup() {
            runOnUiThread(() -> webView.loadUrl(START_PAGE));
        }

        @JavascriptInterface
        public void exit() {
            runOnUiThread(MainActivity.this::finish);
        }

        @JavascriptInterface
        public void ping(final String url) {
            new Thread(() -> {
                boolean ok = false;
                String message;
                HttpURLConnection connection = null;
                try {
                    connection = (HttpURLConnection) new URL(url + "/api/health").openConnection();
                    connection.setConnectTimeout(6000);
                    connection.setReadTimeout(6000);
                    connection.setRequestMethod("GET");
                    int code = connection.getResponseCode();
                    ok = code >= 200 && code < 300;
                    message = ok ? "اتصال برقرار است." : "سرور پاسخ " + code + " داد.";
                } catch (Exception error) {
                    message = "اتصال برقرار نشد: " + error.getClass().getSimpleName();
                } finally {
                    if (connection != null) {
                        connection.disconnect();
                    }
                }
                emitPing(ok, message);
            }).start();
        }

        private void emitPing(final boolean ok, final String message) {
            runOnUiThread(() -> {
                try {
                    String js = "window.onPing && window.onPing(" + ok + "," + JSONObject.quote(message) + ")";
                    webView.evaluateJavascript(js, null);
                } catch (Exception ignored) {
                    // صفحهٔ راه‌اندازی ممکن است دیگر باز نباشد.
                }
            });
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.loadUrl("about:blank");
            webView.removeJavascriptInterface("Mohajeryar");
            webView.destroy();
        }
        super.onDestroy();
    }
}
