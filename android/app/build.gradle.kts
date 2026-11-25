plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "app.bodylens.android"
    compileSdk = 36

    defaultConfig {
        applicationId = "app.bodylens.android"
        minSdk = 28
        targetSdk = 36
        versionCode = (System.getenv("BODYLENS_ANDROID_BUILD") ?: "1").toInt()
        versionName = "0.2." + (System.getenv("BODYLENS_ANDROID_BUILD") ?: "0")
    }

    // en CI, si hay almacén de claves en los secretos, se firma con él; si no, con la clave de depuración
    val ks = System.getenv("ANDROID_KEYSTORE_FILE")?.let { file(it) }?.takeIf { it.exists() }
    signingConfigs {
        if (ks != null) create("release") {
            storeFile = ks
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
        }
    }

    // two apps from the same code: the whole BodyLens app, and BodyLens Bridge, which only sends Health Connect data
    // (the first app: no web app, no subscriptions). Both can be installed at the same time.
    flavorDimensions += "app"
    productFlavors {
        create("full") {
            dimension = "app"
            applicationId = "app.bodylens.android"
            resValue("string", "app_name", "BodyLens")
        }
        create("bridge") {
            dimension = "app"
            applicationId = "app.bodylens.bridge"
            resValue("string", "app_name", "BodyLens Bridge")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName(if (ks != null) "release" else "debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.health.connect:connect-client:1.1.0-alpha10")
    implementation("androidx.work:work-runtime-ktx:2.10.0")
    implementation("androidx.core:core-splashscreen:1.0.1")
    implementation("com.android.billingclient:billing-ktx:8.0.0")
    implementation("androidx.fragment:fragment-ktx:1.8.5")   // activity results need Fragment 1.3+ (lint)
}
