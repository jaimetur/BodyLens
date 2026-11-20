package app.bodylens.android

import android.content.ContentValues
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import android.webkit.JavascriptInterface
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.health.connect.client.HealthConnectClient
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.io.File

/** What the web app can ask the Android app for (window.BodyLensNative in the page). The WebView only shows pages of
 *  the BodyLens server, so only those pages can call it. Methods run on a background thread. */
class NativeBridge(private val activity: MainActivity) {
    private val prefs = Prefs(activity)
    @Volatile private var granted: Int = 0
    @Volatile private var background: Boolean = false

    @JavascriptInterface
    fun version(): String = try { activity.packageManager.getPackageInfo(activity.packageName, 0).versionName ?: "" } catch (_: Exception) { "" }

    /** Health Connect: availability, link with the account, permissions and the last sending (JSON). */
    @JavascriptInterface
    fun healthStatus(): String = JSONObject()
        .put("available", HealthConnectClient.getSdkStatus(activity) == HealthConnectClient.SDK_AVAILABLE)
        .put("configured", prefs.url.isNotEmpty())
        .put("granted", granted).put("total", HealthReader.PERMISSIONS.size).put("background", background)
        .put("auto", prefs.auto).put("lastRun", prefs.lastRun).put("lastOk", prefs.lastOk).put("lastMessage", prefs.lastMessage)
        .toString()

    fun refreshHealth() {
        if (HealthConnectClient.getSdkStatus(activity) != HealthConnectClient.SDK_AVAILABLE) return
        activity.scope().launch {
            try {
                val g = HealthConnectClient.getOrCreate(activity).permissionController.getGrantedPermissions()
                granted = g.intersect(HealthReader.PERMISSIONS).size
                background = HealthReader.BACKGROUND in g
            } catch (_: Exception) { }
        }
    }

    /** The page gives the account's sending address when you sign in: the app links itself and, the first time, asks
     *  for the Health Connect permissions (and sends at once). */
    @JavascriptInterface
    fun setIngestUrl(url: String) {
        val u = url.trim()
        if (!u.startsWith("https://") || "/api/ingest/hae/" !in u) return
        val first = prefs.url != u
        prefs.url = u
        if (first) prefs.auto = true
        Sync.schedule(activity, prefs.auto)
        // Health Connect missing, without permissions (reading in the background included) or with battery limits: the app
        // opens its screen on its own (to install it, or to allow them), at once the first time and then at most once a week
        val sdk = HealthConnectClient.getSdkStatus(activity)
        if (sdk == HealthConnectClient.SDK_UNAVAILABLE || System.currentTimeMillis() - prefs.askedAt < 7 * 24 * 3600_000L) return
        activity.scope().launch {
            val none = sdk != HealthConnectClient.SDK_AVAILABLE || try {
                val g = HealthConnectClient.getOrCreate(activity).permissionController.getGrantedPermissions()
                g.intersect(HealthReader.PERMISSIONS).isEmpty() || HealthReader.BACKGROUND !in g
            } catch (_: Exception) { true } ||
                activity.getSystemService(android.os.PowerManager::class.java)?.isIgnoringBatteryOptimizations(activity.packageName) == false
            if (!none) return@launch
            prefs.askedAt = System.currentTimeMillis()
            activity.runOnUiThread {
                activity.startActivity(Intent(activity, HealthActivity::class.java)
                    .setData(android.net.Uri.parse("bodylens://setup?url=" + android.net.Uri.encode(u))))
            }
        }
    }

    /** Sends now; the page hears the result as the "bl-native-sync" event. */
    @JavascriptInterface
    fun syncNow() {
        activity.scope().launch {
            val (ok, msg) = try { true to Sync.run(activity) } catch (e: Exception) { false to (e.message ?: e.javaClass.simpleName) }
            refreshHealth()
            val detail = JSONObject().put("ok", ok).put("message", msg).toString()
            activity.js("window.dispatchEvent(new CustomEvent('bl-native-sync',{detail:$detail}))")
        }
    }

    @JavascriptInterface
    fun openHealth() = activity.runOnUiThread { activity.startActivity(Intent(activity, HealthActivity::class.java)) }

    /** Plans of the Google Play subscription with their price ("[]" while Google Play does not offer them). */
    @JavascriptInterface
    fun billingProducts(): String = activity.billing.productsJson()

    /** Opens Google Play's purchase screen; the page hears the result through window.blPurchase. */
    @JavascriptInterface
    fun subscribe(plan: String) = activity.billing.subscribe(plan)

    @JavascriptInterface
    fun restorePurchase() = activity.billing.restore()

    @JavascriptInterface
    fun changeServer() = activity.runOnUiThread { activity.changeServer() }

    /** A file made by the page (PDF export, backup, CSV): saved in Downloads and offered to open or share. */
    @JavascriptInterface
    fun saveFile(name: String, mime: String, base64: String) {
        val clean = name.replace(Regex("[\\\\/:*?\"<>|]"), "_").ifBlank { "BodyLens" }
        val bytes = try { Base64.decode(base64, Base64.DEFAULT) } catch (_: Exception) { return }
        try {
            // a copy the app can share, and (Android 10+) one in Downloads
            val dir = File(activity.cacheDir, "shared").apply { mkdirs() }
            val f = File(dir, clean).apply { writeBytes(bytes) }
            if (Build.VERSION.SDK_INT >= 29) {
                val v = ContentValues().apply {
                    put(MediaStore.Downloads.DISPLAY_NAME, clean); put(MediaStore.Downloads.MIME_TYPE, mime)
                    put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                }
                activity.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v)?.let { uri ->
                    activity.contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                }
            }
            val uri = FileProvider.getUriForFile(activity, activity.packageName + ".files", f)
            val send = Intent(Intent.ACTION_SEND).setType(mime).putExtra(Intent.EXTRA_STREAM, uri)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            activity.runOnUiThread {
                if (Build.VERSION.SDK_INT >= 29) Toast.makeText(activity, activity.getString(R.string.saved_downloads, clean), Toast.LENGTH_LONG).show()
                activity.startActivity(Intent.createChooser(send, clean))
            }
        } catch (e: Exception) {
            activity.runOnUiThread { Toast.makeText(activity, e.message ?: "Error", Toast.LENGTH_LONG).show() }
        }
    }
}
