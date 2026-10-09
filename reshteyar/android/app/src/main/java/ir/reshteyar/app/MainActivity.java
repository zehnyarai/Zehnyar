package ir.reshteyar.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * پوسته‌ی WebView برای رشته‌یار.
 * فقط دامنه‌ی سایت و درگاه زرین‌پال داخل برنامه باز می‌شوند؛ بقیه‌ی لینک‌ها در مرورگر خارجی.
 */
public class MainActivity extends Activity {

    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        CookieManager.getInstance().setAcceptCookie(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return openExternally(request.getUrl());
            }
        });

        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            web.loadUrl(BuildConfig.RZ_URL);
        }
    }

    private boolean isAllowedInside(Uri uri) {
        if (uri == null || !"https".equals(uri.getScheme()) || uri.getHost() == null) {
            return false;
        }
        String host = uri.getHost();
        String siteHost = Uri.parse(BuildConfig.RZ_URL).getHost();
        return host.equals(siteHost)
                || host.equals("payment.zarinpal.com")
                || host.equals("sandbox.zarinpal.com");
    }

    /** true برمی‌گرداند یعنی WebView بارگذاری نکند. */
    private boolean openExternally(Uri uri) {
        if (isAllowedInside(uri)) {
            return false;
        }
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (ActivityNotFoundException ignored) {
            // هیچ برنامه‌ای برای این لینک نصب نیست؛ کاری نمی‌کنیم.
        }
        return true;
    }

    @Override
    public boolean onKeyDown(int keyCode, android.view.KeyEvent event) {
        if (keyCode == android.view.KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }
}
