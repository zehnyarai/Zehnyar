import java.util.Properties

plugins {
    id("com.android.application")
}

// کلید امضای ثابت: همه‌ی نسخه‌ها با یک کلید امضا می‌شوند تا به‌روزرسانی روی نسخه‌ی قبلی نصب شود.
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore/keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

// هر اجرای CI کد نسخه‌ی بزرگ‌تری می‌گیرد؛ اندروید فقط نسخه‌ی جدیدتر را به‌روزرسانی می‌کند.
val ciRun: Int = System.getenv("GITHUB_RUN_NUMBER")?.toIntOrNull() ?: 0

android {
    namespace = "ir.reshteyar.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "ir.reshteyar.app"
        // اندروید ۵.۰ به بالا (WebView و جاوااسکریپت پایه)
        minSdk = 21
        targetSdk = 34
        versionCode = 1000 + ciRun
        versionName = "1.1.$ciRun"
    }

    signingConfigs {
        create("release") {
            if (keystoreProps.isNotEmpty()) {
                storeFile = rootProject.file("keystore/" + keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
                storeType = "pkcs12"
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            if (keystoreProps.isNotEmpty()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
