package app.bodylens.android

import android.content.Context
import androidx.health.connect.client.HealthConnectClient
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.time.Duration
import java.time.Instant
import java.util.concurrent.TimeUnit

/** Un envío: lee desde el último envío (con margen) y lo manda a la dirección configurada. */
object Sync {
    private const val WORK = "bodylens-sync"

    suspend fun run(context: Context): String {
        val prefs = Prefs(context)
        val url = prefs.url
        prefs.lastRun = System.currentTimeMillis()
        try {
            if (!url.startsWith("https://") && !url.startsWith("http://")) throw IllegalStateException(context.getString(R.string.err_no_url))
            if (HealthConnectClient.getSdkStatus(context) != HealthConnectClient.SDK_AVAILABLE)
                throw IllegalStateException(context.getString(R.string.hc_missing))
            val client = HealthConnectClient.getOrCreate(context)
            val now = Instant.now()
            val from = if (prefs.sentUntil > 0) Instant.ofEpochMilli(prefs.sentUntil).minus(Duration.ofHours(3))
                       else now.minus(Duration.ofDays(30))
            val sleepFrom = minOf(from, now.minus(Duration.ofDays(3)))
            val res = HealthReader.read(client, from, now, sleepFrom)
            post(url, res.body.toString())
            prefs.sentUntil = now.toEpochMilli()
            val n = res.counts.values.sum()
            val msg = context.getString(R.string.sent_ok, n)
            prefs.lastOk = true; prefs.lastMessage = msg
            return msg
        } catch (e: Exception) {
            val msg = e.message ?: e.javaClass.simpleName
            prefs.lastOk = false; prefs.lastMessage = msg
            throw e
        }
    }

    /** On a background thread: Android does not allow network calls on the screen's thread. */
    private suspend fun post(url: String, body: String) = withContext(Dispatchers.IO) {
        val c = URL(url).openConnection() as HttpURLConnection
        try {
            c.requestMethod = "POST"
            c.connectTimeout = 20000; c.readTimeout = 120000
            c.doOutput = true
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            c.setRequestProperty("User-Agent", "BodyLens-Android")
            c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            val code = c.responseCode
            if (code !in 200..299) {
                val err = (c.errorStream ?: c.inputStream)?.bufferedReader()?.use { it.readText() }?.take(200) ?: ""
                throw IllegalStateException("HTTP $code $err".trim())
            }
            c.inputStream.use { it.readBytes() }
        } finally {
            c.disconnect()
        }
    }

    /** Programa (o quita) el envío automático cada hora. */
    fun schedule(context: Context, on: Boolean) {
        val wm = WorkManager.getInstance(context)
        if (!on) { wm.cancelUniqueWork(WORK); return }
        val req = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        wm.enqueueUniquePeriodicWork(WORK, ExistingPeriodicWorkPolicy.UPDATE, req)
    }
}
