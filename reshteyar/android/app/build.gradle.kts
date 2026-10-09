plugins {
    id("com.android.application")
}

android {
    namespace = "ir.reshteyar.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "ir.reshteyar.app"
        // اندروید ۵.۰ به بالا (WebView و جاوااسکریپت پایه)
        minSdk = 21
        targetSdk = 34
        versionCode = 2
        versionName = "1.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
