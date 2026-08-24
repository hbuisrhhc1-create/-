import os
from PIL import Image, ImageDraw

def create_full_project():
    print("[*] Generating complete Nexus Agent Android project structure...")

    dirs = [
        "app/src/main/java/com/inon/nexusagent",
        "app/src/main/res/layout",
        "app/src/main/res/mipmap-mdpi",
        "app/src/main/res/mipmap-hdpi",
        "app/src/main/res/mipmap-xhdpi",
        "app/src/main/res/mipmap-xxhdpi",
        "app/src/main/res/mipmap-xxxhdpi",
        "app/src/main/res/values"
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

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
            print("[*] Processing custom icon.png...")
            img = Image.open("icon.png").convert("RGBA")
        except Exception as e:
            print(f"[!] Could not process icon.png ({e}).")

    if img is None:
        print("[*] Generating fallback icon...")
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((50, 50, 462, 462), fill=(0, 122, 255, 255))

    for folder, size in sizes.items():
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f"app/src/main/res/{folder}/ic_launcher.png", "PNG")
        resized.save(f"app/src/main/res/{folder}/ic_launcher_round.png", "PNG")

    # 1. AndroidManifest.xml
    manifest_code = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.inon.nexusagent">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />

    <application
        android:allowBackup="true"
        android:label="Nexus Agent"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".AgentService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="camera|location" />

        <receiver
            android:name=".BootReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>

    </application>
</manifest>"""
    with open("app/src/main/AndroidManifest.xml", "w", encoding="utf-8") as f:
        f.write(manifest_code.strip())

    # 2. strings.xml
    with open("app/src/main/res/values/strings.xml", "w", encoding="utf-8") as f:
        f.write('<resources><string name="app_name">Nexus Agent</string></resources>')

    # 3. activity_main.xml
    layout_code = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="24dp">

    <ImageView
        android:layout_width="120dp"
        android:layout_height="120dp"
        android:src="@mipmap/ic_launcher"
        android:layout_marginBottom="32dp" />

    <TextView
        android:id="@+id/statusText"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="הסוכן כבוי"
        android:textSize="20sp"
        android:textStyle="bold"
        android:layout_marginBottom="24dp" />

    <Button
        android:id="@+id/toggleButton"
        android:layout_width="200dp"
        android:layout_height="wrap_content"
        android:text="הפעל סוכן"
        android:padding="12dp" />

</LinearLayout>"""
    with open("app/src/main/res/layout/activity_main.xml", "w", encoding="utf-8") as f:
        f.write(layout_code.strip())

    # 4. MainActivity.kt
    main_activity_code = """package com.inon.nexusagent

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val statusText = findViewById<TextView>(R.id.statusText)
        val toggleButton = findViewById<Button>(R.id.toggleButton)
        val prefs = getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)

        fun updateUI() {
            val isActive = prefs.getBoolean("is_active", false)
            if (isActive) {
                statusText.text = "הסוכן פעיל ברקע"
                toggleButton.text = "עצור סוכן"
            } else {
                statusText.text = "הסוכן כבוי"
                toggleButton.text = "הפעל סוכן"
            }
        }

        updateUI()

        toggleButton.setOnClickListener {
            val isActive = prefs.getBoolean("is_active", false)
            val serviceIntent = Intent(this, AgentService::class.java)

            if (isActive) {
                stopService(serviceIntent)
                prefs.edit().putBoolean("is_active", false).apply()
            } else {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(serviceIntent)
                } else {
                    startService(serviceIntent)
                }
                prefs.edit().putBoolean("is_active", true).apply()
            }
            updateUI()
        }
    }
}"""
    with open("app/src/main/java/com/inon/nexusagent/MainActivity.kt", "w", encoding="utf-8") as f:
        f.write(main_activity_code.strip())

    # 5. AgentService.kt
    agent_service_code = """package com.inon.nexusagent

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.core.app.NotificationCompat

class AgentService : Service() {

    private var wakeLock: PowerManager.WakeLock? = null
    private val CHANNEL_ID = "NexusAgentChannel"

    override fun onCreate() {
        super.onCreate()
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "NexusAgent::Wakelock").apply {
            acquire(24 * 60 * 60 * 1000L)
        }

        createNotificationChannel()
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Nexus Agent Running")
            .setContentText("Service is active in background")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .build()

        startForeground(1, notification)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Nexus Agent Service Channel",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    override fun onDestroy() {
        super.onDestroy()
        wakeLock?.release()
    }
}"""
    with open("app/src/main/java/com/inon/nexusagent/AgentService.kt", "w", encoding="utf-8") as f:
        f.write(agent_service_code.strip())

    # 6. BootReceiver.kt
    boot_receiver_code = """package com.inon.nexusagent

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val prefs = context.getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)
            val isActive = prefs.getBoolean("is_active", false)
            if (isActive) {
                val serviceIntent = Intent(context, AgentService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(serviceIntent)
                } else {
                    context.startService(serviceIntent)
                }
            }
        }
    }
}"""
    with open("app/src/main/java/com/inon/nexusagent/BootReceiver.kt", "w", encoding="utf-8") as f:
        f.write(boot_receiver_code.strip())

    # 7. build.gradle
    project_gradle = """buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.4.2'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:1.8.0"
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}"""
    with open("build.gradle", "w", encoding="utf-8") as f:
        f.write(project_gradle.strip())

    # 8. settings.gradle
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

rootProject.name = "NexusAgent"
include ':app'"""
    with open("settings.gradle", "w", encoding="utf-8") as f:
        f.write(settings_gradle.strip())

    # 9. app/build.gradle
    app_gradle = """plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    namespace 'com.inon.nexusagent'
    compileSdk 33

    defaultConfig {
        applicationId "com.inon.nexusagent"
        minSdk 24
        targetSdk 33
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_11
        targetCompatibility JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = '11'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.9.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.8.0'
}"""
    with open("app/build.gradle", "w", encoding="utf-8") as f:
        f.write(app_gradle.strip())

    print("[+] Project generated cleanly without configuration conflicts!")

if __name__ == "__main__":
    create_full_project()
