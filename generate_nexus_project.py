import os
from PIL import Image, ImageDraw
import shutil

def create_full_project():
    APP_NAME = "מגן מגנבות"
    PACKAGE_NAME = "com.inon.nexusagent"
    
    print(f"[*] Generating full project for '{APP_NAME}'...")

    PACKAGE_PATH = PACKAGE_NAME.replace(".", "/")

    dirs = [
        f"app/src/main/java/{PACKAGE_PATH}",
        "app/src/main/res/layout",
        "app/src/main/res/mipmap-mdpi",
        "app/src/main/res/mipmap-hdpi",
        "app/src/main/res/mipmap-xhdpi",
        "app/src/main/res/mipmap-xxhdpi",
        "app/src/main/res/mipmap-xxxhdpi",
        "app/src/main/res/values",
        "app/src/main/res/xml",
        "app/src/main/res/raw"
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 1. העתקת קובץ האזעקה המותאם אישית
    if os.path.exists("alarm.mp3"):
        shutil.copy("alarm.mp3", "app/src/main/res/raw/alarm.mp3")
        print("[+] Custom alarm.mp3 embedded successfully!")
    else:
        print("[!] Warning: 'alarm.mp3' not found in root directory.")

    # 2. העתקת קובץ השירות (AgentRealtimeService.kt) מתיקיית העבודה
    service_dest = f"app/src/main/java/{PACKAGE_PATH}/AgentRealtimeService.kt"
    if os.path.exists("AgentRealtimeService.kt"):
        shutil.copy("AgentRealtimeService.kt", service_dest)
        print("[+] AgentRealtimeService.kt copied successfully!")
    else:
        print("[!] Error: 'AgentRealtimeService.kt' must be placed in the root directory alongside this script.")

    # 3. יצירת אייקון
    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    img = None
    if os.path.exists("icon.png"):
        try:
            img = Image.open("icon.png").convert("RGBA")
        except Exception:
            pass

    if img is None:
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((32, 32, 480, 480), fill=(24, 119, 242, 255))
        draw.rectangle((180, 140, 332, 360), fill=(255, 255, 255, 255))

    for folder, size in sizes.items():
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f"app/src/main/res/{folder}/ic_launcher.png", "PNG")
        resized.save(f"app/src/main/res/{folder}/ic_launcher_round.png", "PNG")

    # 4. gradle.properties
    with open("gradle.properties", "w", encoding="utf-8") as f:
        f.write("android.useAndroidX=true\nandroid.enableJetifier=true\norg.gradle.jvmargs=-Xmx3072m -XX:MaxMetaspaceSize=512m\n")

    # 5. device_admin.xml
    admin_xml = """<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <force-lock />
    </uses-policies>
</device-admin>"""
    with open("app/src/main/res/xml/device_admin.xml", "w", encoding="utf-8") as f:
        f.write(admin_xml.strip())

    # 6. AndroidManifest.xml
    manifest_code = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />

    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <uses-feature android:name="android.hardware.camera.front" android:required="false" />

    <application
        android:allowBackup="true"
        android:label="{APP_NAME}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".AgentRealtimeService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="shortService" />

        <receiver
            android:name=".MyDeviceAdminReceiver"
            android:label="{APP_NAME} Admin"
            android:permission="android.permission.BIND_DEVICE_ADMIN"
            android:exported="true">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin" />
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
            </intent-filter>
        </receiver>

        <receiver
            android:name=".BootReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
                <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
            </intent-filter>
        </receiver>

    </application>
</manifest>"""
    with open("app/src/main/AndroidManifest.xml", "w", encoding="utf-8") as f:
        f.write(manifest_code.strip())

    # 7. strings.xml
    with open("app/src/main/res/values/strings.xml", "w", encoding="utf-8") as f:
        f.write(f'<resources><string name="app_name">{APP_NAME}</string></resources>')

    # 8. activity_main.xml
    layout_code = f"""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="32dp"
    android:background="#F5F7FA">

    <ImageView
        android:layout_width="100dp"
        android:layout_height="100dp"
        android:src="@mipmap/ic_launcher"
        android:layout_marginBottom="24dp" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="{APP_NAME}"
        android:textSize="24sp"
        android:textStyle="bold"
        android:textColor="#1A202C"
        android:layout_marginBottom="8dp" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="מחובר ב-Realtime וממתין לפקודות"
        android:textSize="15sp"
        android:textColor="#2F855A"
        android:textStyle="bold"
        android:layout_marginBottom="32dp" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp"
        android:background="#FFFFFF"
        android:elevation="4dp">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="מזהה מכשיר (Device ID):"
            android:textSize="12sp"
            android:textColor="#718096" />

        <TextView
            android:id="@+id/deviceIdText"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="טוען מזהה..."
            android:textSize="14sp"
            android:textStyle="bold"
            android:textColor="#2D3748"
            android:textIsSelectable="true"
            android:layout_marginTop="4dp" />
    </LinearLayout>

</LinearLayout>"""
    with open("app/src/main/res/layout/activity_main.xml", "w", encoding="utf-8") as f:
        f.write(layout_code.strip())

    # 9. MainActivity.kt (מייצר מזהה רנדומלי נקי בכל התקנה חדשה)
    main_activity_code = f"""package {PACKAGE_NAME}

import android.Manifest
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.util.UUID

class MainActivity : AppCompatActivity() {{

    private val PERMISSION_REQUEST_CODE = 1001

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val deviceIdText = findViewById<TextView>(R.id.deviceIdText)
        val deviceId = getOrCreateDeviceId()
        deviceIdText.text = deviceId

        checkAndRequestPermissions()
        requestIgnoreBatteryOptimizations()
        requestDeviceAdmin()
        startRealtimeService()
    }}

    private fun checkAndRequestPermissions() {{
        val permissions = mutableListOf(
            Manifest.permission.CAMERA,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {{
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }}
        
        val missingPermissions = permissions.filter {{
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }}
        
        if (missingPermissions.isNotEmpty()) {{
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), PERMISSION_REQUEST_CODE)
        }}
    }}

    private fun requestIgnoreBatteryOptimizations() {{
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {{
            val intent = Intent()
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            if (!pm.isIgnoringBatteryOptimizations(packageName)) {{
                intent.action = Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
                intent.data = Uri.parse("package:$packageName")
                try {{ startActivity(intent) }} catch (e: Exception) {{ e.printStackTrace() }}
            }}
        }}
    }}

    private fun requestDeviceAdmin() {{
        val adminComponent = ComponentName(this, MyDeviceAdminReceiver::class.java)
        val dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        if (!dpm.isAdminActive(adminComponent)) {{
            val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {{
                putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent)
                putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "נדרש כדי לאפשר נעילת מכשיר מרחוק")
            }}
            try {{ startActivity(intent) }} catch (e: Exception) {{ e.printStackTrace() }}
        }}
    }}

    private fun startRealtimeService() {{
        val serviceIntent = Intent(this, AgentRealtimeService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
            startForegroundService(serviceIntent)
        }} else {{
            startService(serviceIntent)
        }}
    }}

    private fun getOrCreateDeviceId(): String {{
        val prefs = getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)
        var id = prefs.getString("device_id", null)
        if (id.isNullOrEmpty()) {{
            id = UUID.randomUUID().toString()
            prefs.edit().putString("device_id", id).apply()
        }}
        return id
    }}
}}"""
    with open(f"app/src/main/java/{PACKAGE_PATH}/MainActivity.kt", "w", encoding="utf-8") as f:
        f.write(main_activity_code.strip())

    # 10. MyDeviceAdminReceiver.kt
    admin_receiver_code = f"""package {PACKAGE_NAME}

import android.app.admin.DeviceAdminReceiver

class MyDeviceAdminReceiver : DeviceAdminReceiver() {{
}}"""
    with open(f"app/src/main/java/{PACKAGE_PATH}/MyDeviceAdminReceiver.kt", "w", encoding="utf-8") as f:
        f.write(admin_receiver_code.strip())

    # 11. BootReceiver.kt
    boot_receiver_code = f"""package {PACKAGE_NAME}

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

class BootReceiver : BroadcastReceiver() {{
    override fun onReceive(context: Context, intent: Intent) {{
        val serviceIntent = Intent(context, AgentRealtimeService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
            context.startForegroundService(serviceIntent)
        }} else {{
            context.startService(serviceIntent)
        }}
    }}
}}"""
    with open(f"app/src/main/java/{PACKAGE_PATH}/BootReceiver.kt", "w", encoding="utf-8") as f:
        f.write(boot_receiver_code.strip())

    # 12. build.gradle (Root)
    project_gradle = """plugins {
    id 'com.android.application' version '8.1.4' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.0' apply false
}

task clean(type: Delete) {
    delete rootProject.buildDir
}"""
    with open("build.gradle", "w", encoding="utf-8") as f:
        f.write(project_gradle.strip())

    # 13. settings.gradle
    settings_gradle = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "MagenMagnevot"
include ':app'"""
    with open("settings.gradle", "w", encoding="utf-8") as f:
        f.write(settings_gradle.strip())

    # 14. app/build.gradle
    app_gradle = f"""plugins {{
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}}

android {{
    namespace '{PACKAGE_NAME}'
    compileSdk 34

    defaultConfig {{
        applicationId "{PACKAGE_NAME}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }}

    buildTypes {{
        release {{
            minifyEnabled false
        }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = '17'
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'com.google.android.gms:play-services-location:21.1.0'

    def camerax_version = "1.3.1"
    implementation "androidx.camera:camera-core:${{camerax_version}}"
    implementation "androidx.camera:camera-camera2:${{camerax_version}}"
    implementation "androidx.camera:camera-lifecycle:${{camerax_version}}"
    implementation "androidx.camera:camera-view:${{camerax_version}}"
}}"""
    with open("app/build.gradle", "w", encoding="utf-8") as f:
        f.write(app_gradle.strip())

    print("[+] Project generated successfully with name 'מגן מגנבות' and secure random Device ID!")

if __name__ == "__main__":
    create_full_project()
      
