package app.bodylens.android

import android.content.Intent
import android.net.Uri
import android.os.PowerManager
import android.provider.Settings
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Date

/** Health Connect: permissions, automatic sending and the last result. Opened from Your account inside the app (or by
 *  the setup link bodylens://setup?url=… from a browser). */
class HealthActivity : ComponentActivity() {
    /** Bumped when a setup link (bodylens://setup?url=…) brings the sending address, so the screen asks for the
     *  permissions and sends at once. */
    private val setupTick = mutableStateOf(0)
    /** Bumped each time the screen comes back (e.g. from Google Play after installing Health Connect). */
    private val resumeTick = mutableStateOf(0)

    override fun onResume() {
        super.onResume()
        resumeTick.value += 1
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        applySetup(intent)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(primary = Color(0xFF3B7BF2))) {
                // opened from the app (not as BodyLens Bridge's own screen): a button closes it and goes back to the app
                val close: (() -> Unit)? = if (isTaskRoot) null else ({ finish() })
                Surface(Modifier.fillMaxSize()) { Screen(setupTick.value, resumeTick.value, close) }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        applySetup(intent)
    }

    /** "Set up the app" link from Your account → Data sources: it carries the account's sending address. */
    private fun applySetup(intent: Intent?) {
        val data = intent?.data ?: return
        if (data.scheme != "bodylens" || data.host != "setup") return
        val url = data.getQueryParameter("url")?.trim() ?: return
        if (!url.startsWith("https://") || "/api/ingest/hae/" !in url) return
        val prefs = Prefs(this)
        prefs.url = url
        prefs.auto = true
        setupTick.value += 1
    }
}

@Composable
private fun Screen(setupTick: Int, resumeTick: Int, onClose: (() -> Unit)?) {
    val context = LocalContext.current
    val prefs = remember { Prefs(context) }
    val scope = rememberCoroutineScope()
    var url by remember { mutableStateOf(prefs.url) }
    var auto by remember { mutableStateOf(prefs.auto) }
    var busy by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf(statusText(context, prefs)) }
    var granted by remember { mutableStateOf<Set<String>>(emptySet()) }
    var sdk by remember { mutableStateOf(HealthConnectClient.getSdkStatus(context)) }
    val available = sdk == HealthConnectClient.SDK_AVAILABLE
    // opened by the setup link while Health Connect was missing: ask for the permissions once it is installed
    var askWhenInstalled by remember { mutableStateOf(false) }
    // Android does not stop or delay the hourly sending to save battery
    val power = remember { context.getSystemService(PowerManager::class.java) }
    fun unrestricted() = power?.isIgnoringBatteryOptimizations(context.packageName) ?: true
    var battery by remember { mutableStateOf(unrestricted()) }
    fun askBattery() {
        try {
            context.startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:" + context.packageName)))
        } catch (_: Exception) {
            try { context.startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)) } catch (_: Exception) { }
        }
    }

    suspend fun refreshGranted() {
        if (available) granted = HealthConnectClient.getOrCreate(context).permissionController.getGrantedPermissions()
    }
    // first sending as soon as there is an address and some permission: nothing else for the user to do
    fun sendNow() {
        busy = true
        scope.launch {
            try { Sync.run(context) } catch (_: Exception) { }
            Sync.schedule(context, prefs.auto && prefs.url.isNotEmpty())
            status = statusText(context, prefs)
            busy = false
        }
    }
    val askPermissions = rememberLauncherForActivityResult(PermissionController.createRequestPermissionResultContract()) {
        granted = it
        if (it.intersect(HealthReader.PERMISSIONS).isNotEmpty() && prefs.url.isNotEmpty() && prefs.lastRun == 0L) sendNow()
        // then, once, the system's question to let the app send in the background without battery limits
        if (it.intersect(HealthReader.PERMISSIONS).isNotEmpty() && !unrestricted() && !prefs.askedBattery) {
            prefs.askedBattery = true
            askBattery()
        }
    }
    LaunchedEffect(Unit) {
        refreshGranted()
        Sync.schedule(context, prefs.auto && prefs.url.isNotEmpty())
    }
    LaunchedEffect(resumeTick) {
        val was = available
        battery = unrestricted()
        sdk = HealthConnectClient.getSdkStatus(context)
        if (sdk != HealthConnectClient.SDK_AVAILABLE) return@LaunchedEffect
        refreshGranted()
        if (!was && askWhenInstalled && granted.intersect(HealthReader.PERMISSIONS).isEmpty()) {
            askWhenInstalled = false
            askPermissions.launch(HealthReader.PERMISSIONS + HealthReader.BACKGROUND)
        }
    }
    // opened from the setup link: address saved, so ask for every permission (or send, if they are already granted)
    LaunchedEffect(setupTick) {
        if (setupTick == 0) return@LaunchedEffect
        url = prefs.url; auto = prefs.auto
        refreshGranted()
        if (!available) { askWhenInstalled = true; return@LaunchedEffect }
        if (!granted.containsAll(HealthReader.PERMISSIONS + HealthReader.BACKGROUND))
            askPermissions.launch(HealthReader.PERMISSIONS + HealthReader.BACKGROUND)
        else sendNow()
    }

    Column(
        Modifier.safeDrawingPadding().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("BodyLens", fontSize = 30.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.weight(1f))
            if (onClose != null) TextButton(onClick = onClose) { Text(stringResource(R.string.close), fontSize = 16.sp) }
        }
        Text(stringResource(R.string.intro))

        if (!available) {
            Text(stringResource(if (sdk == HealthConnectClient.SDK_UNAVAILABLE) R.string.hc_unsupported else R.string.hc_missing),
                color = MaterialTheme.colorScheme.error)
            if (sdk != HealthConnectClient.SDK_UNAVAILABLE) Button(onClick = {
                // Google Play's page of Health Connect (install or update), which then opens its set-up
                val play = "details?id=com.google.android.apps.healthdata&url=healthconnect%3A%2F%2Fonboarding"
                try { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("market://$play"))) }
                catch (_: Exception) { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/$play"))) }
            }) { Text(stringResource(R.string.hc_install)) }
        }

        if (url.isNotBlank()) Text(stringResource(R.string.configured), color = Color(0xFF1F9D6B), fontWeight = FontWeight.Bold)
        Text(stringResource(R.string.step1), fontWeight = FontWeight.Bold)
        OutlinedTextField(
            value = url, onValueChange = { url = it; prefs.url = it },
            label = { Text(stringResource(R.string.url_label)) },
            placeholder = { Text("https://…/api/ingest/hae/…") },
            singleLine = true, modifier = Modifier.fillMaxWidth(),
        )
        Text(stringResource(R.string.url_help), fontSize = 13.sp, color = Color.Gray)

        Text(stringResource(R.string.step2), fontWeight = FontWeight.Bold)
        val have = granted.intersect(HealthReader.PERMISSIONS).size
        Text(stringResource(R.string.perm_count, have, HealthReader.PERMISSIONS.size), fontSize = 14.sp)
        OutlinedButton(enabled = available, onClick = {
            askPermissions.launch(HealthReader.PERMISSIONS + HealthReader.BACKGROUND)
        }) { Text(stringResource(R.string.perm_button)) }
        if (available && have > 0)
            if (HealthReader.BACKGROUND in granted) Text(stringResource(R.string.bg_ok), fontSize = 14.sp, color = Color(0xFF1F9D6B))
            else Text(stringResource(R.string.perm_background), fontSize = 13.sp, color = MaterialTheme.colorScheme.error)

        Text(stringResource(R.string.step3), fontWeight = FontWeight.Bold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(stringResource(R.string.auto_label), Modifier.weight(1f))
            Switch(checked = auto, onCheckedChange = {
                auto = it; prefs.auto = it; Sync.schedule(context, it && prefs.url.isNotEmpty())
            })
        }
        if (battery) Text(stringResource(R.string.battery_ok), fontSize = 14.sp, color = Color(0xFF1F9D6B))
        else {
            Text(stringResource(R.string.battery_missing), fontSize = 13.sp, color = MaterialTheme.colorScheme.error)
            OutlinedButton(onClick = { askBattery() }) { Text(stringResource(R.string.battery_button)) }
        }
        Button(enabled = !busy && available && url.isNotBlank(), onClick = { sendNow() }, modifier = Modifier.fillMaxWidth()) {
            Text(stringResource(if (busy) R.string.sending else R.string.send_now))
        }
        Spacer(Modifier.padding(2.dp))
        Text(status, color = if (prefs.lastOk || prefs.lastRun == 0L) Color.Unspecified else MaterialTheme.colorScheme.error)
    }
}

private fun statusText(context: android.content.Context, p: Prefs): String {
    if (p.lastRun == 0L) return context.getString(R.string.never)
    val t = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(p.lastRun))
    return context.getString(R.string.last_run, t, p.lastMessage)
}
