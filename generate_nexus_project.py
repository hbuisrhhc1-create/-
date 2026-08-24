import os
from PIL import Image, ImageDraw

def create_full_project():
    # ==========================================
    # הגדרות ראשיות - תוכל לשנות כאן מתי שתרצה
    # ==========================================
    APP_NAME = "מגן מגנבות"  # <--- כאן בוחרים את שם האפליקציה
    PACKAGE_NAME = "com.inon.nexusagent"
    
    SUPABASE_URL = "https://pqomjgjmuxddunbhzptd.supabase.co"
    SUPABASE_KEY = "Sb_publishable_A9zsHfvlgv05Ywv0Ji9GYw_17I6ZFVN"
    # ==========================================

    print(f"[*] Generating project for '{APP_NAME}' with Supabase Realtime credentials...")

    PACKAGE_PATH = PACKAGE_NAME.replace(".", "/")

    dirs = [
        f"app/src/main/java/{PACKAGE_PATH}",
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

    # 1. יצירת אייקון
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
        except Exception as e:
            print(f"[!] Custom icon loading failed ({e}). Using fallback.")

    if img is None:
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((32, 32, 480, 480), fill=(24, 119, 242, 255))
        draw.rectangle((180, 140, 332, 360), fill=(255, 255, 255, 255))

    for folder, size in sizes.items():
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f"app/src/main/res/{folder}/ic_launcher.png", "PNG")
        resized.save(f"app/src/main/res/{folder}/ic_launcher_round.png", "PNG")

    # 2. gradle.properties
    with open("gradle.properties", "w", encoding="utf-8") as f:
        f.write("android.useAndroidX=true\nandroid.enableJetifier=true\norg.gradle.jvmargs=-Xmx3072m -XX:MaxMetaspaceSize=512m\n")

    # 3. AndroidManifest.xml
    manifest_code = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />

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

    # 4. strings.xml
    with open("app/src/main/res/values/strings.xml", "w", encoding="utf-8") as f:
        f.write(f'<resources><string name="app_name">{APP_NAME}</string></resources>')

    # 5. activity_main.xml
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

    # 6. MainActivity.kt
    main_activity_code = f"""package {PACKAGE_NAME}

import android.Manifest
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
        startRealtimeService()
    }}

    private fun checkAndRequestPermissions() {{
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {{
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {{
                ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), PERMISSION_REQUEST_CODE)
            }}
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
            val hardwareId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            id = if (!hardwareId.isNullOrEmpty() && hardwareId != "9774d56d682e549c") {{ hardwareId }} else {{ UUID.randomUUID().toString() }}
            prefs.edit().putString("device_id", id).apply()
        }}
        return id
    }}
}}"""
    with open(f"app/src/main/java/{PACKAGE_PATH}/MainActivity.kt", "w", encoding="utf-8") as f:
        f.write(main_activity_code.strip())

    # 7. AgentRealtimeService.kt
    realtime_service_code = f"""package {PACKAGE_NAME}

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import okhttp3.*
import java.util.concurrent.TimeUnit

class AgentRealtimeService : Service() {{

    private var wakeLock: PowerManager.WakeLock? = null
    private val CHANNEL_ID = "NexusRealtimeChannel"
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    override fun onCreate() {{
        super.onCreate()
        
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "NexusAgent::RealtimeWakelock").apply {{
            acquire()
        }}

        createNotificationChannel()
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("{APP_NAME} Active")
            .setContentText("מחובר ב-Realtime ל-Supabase")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        startForeground(1001, notification)
        connectToRealtime()
    }}

    private fun connectToRealtime() {{
        val prefs = getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)
        val deviceId = prefs.getString("device_id", "unknown") ?: "unknown"

        val wsUrl = "{SUPABASE_URL.replace("https://", "wss://")}/realtime/v1/websocket?apikey={SUPABASE_KEY}&vsn=1.0.0"

        val request = Request.Builder()
            .url(wsUrl)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {{
            override fun onOpen(webSocket: WebSocket, response: Response) {{
                val joinJson = \"\"\"
                {{
                    "topic": "realtime:public:commands:device_id=eq.$deviceId",
                    "event": "phx_join",
                    "payload": {{}},
                    "ref": "1"
                }}
                \"\"\".trimIndent()
                webSocket.send(joinJson)
            }}

            override fun onMessage(webSocket: WebSocket, text: String) {{
                if (text.contains("INSERT") || text.contains("UPDATE")) {{
                    handleIncomingCommand(text)
                }}
            }}

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {{
                try {{ Thread.sleep(5000); connectToRealtime() }} catch (_: Exception) {{}}
            }}
        }})
    }}

    private fun handleIncomingCommand(rawJson: String) {{
        // עיבוד הפקודה שהתקבלה מהאתר דרך Supabase Realtime
    }}

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {{
        return START_STICKY
    }}

    private fun createNotificationChannel() {{
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "{APP_NAME} Realtime Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }}
    }}

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {{
        webSocket?.close(1000, "Service destroyed")
        wakeLock?.let {{ if (it.isHeld) it.release() }}
        super.onDestroy()
    }}
}}"""
    with open(f"app/src/main/java/{PACKAGE_PATH}/AgentRealtimeService.kt", "w", encoding="utf-8") as f:
        f.write(realtime_service_code.strip())

    # 8. BootReceiver.kt
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

    # 9. build.gradle (Root)
    project_gradle = """plugins {
    id 'com.android.application' version '8.0.2' apply false
    id 'org.jetbrains.kotlin.android' version '1.8.20' apply false
}

task clean(type: Delete) {
    delete rootProject.buildDir
}"""
    with open("build.gradle", "w", encoding="utf-8") as f:
        f.write(project_gradle.strip())

    # 10. settings.gradle
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

    # 11. app/build.gradle
    app_gradle = f"""plugins {{
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}}

android {{
    namespace '{PACKAGE_NAME}'
    compileSdk 33

    defaultConfig {{
        applicationId "{PACKAGE_NAME}"
        minSdk 24
        targetSdk 33
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
    implementation 'androidx.core:core-ktx:1.10.1'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
}}"""
    with open("app/build.gradle", "w", encoding="utf-8") as f:
        f.write(app_gradle.strip())

    print("[+] Project script fully generated with customizable APP_NAME and Supabase credentials!")

if __name__ == "__main__":
    create_full_project()
  
