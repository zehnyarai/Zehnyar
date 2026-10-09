plugins {
    id("com.android.application")
}

// آدرس HTTPS سایت از پارامتر -PrzUrl گرفته می‌شود (در GitHub Actions از متغیر RZ_URL یا ورودی url).
val rzUrl: String = (project.findProperty("rzUrl") as String?)?.trim() ?: ""
if (!rzUrl.startsWith("https://")) {
    throw GradleException("آدرس HTTPS سایت لازم است: -PrzUrl=https://your-domain.ir")
}

android {
    namespace = "ir.reshteyar.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "ir.reshteyar.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        buildConfigField("String", "RZ_URL", "\"$rzUrl\"")
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
