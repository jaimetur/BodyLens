package app.bodylens.android

import android.content.Intent
import android.net.Uri
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

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = lightColorScheme(primary = Color(0xFF3B7BF2))) {
                Surface(Modifier.fillMaxSize()) { Screen() }
            }
        }
    }
}

@Composable
private fun Screen() {
    val context = LocalContext.current
    val prefs = remember { Prefs(context) }
    val scope = rememberCoroutineScope()
    var url by remember { mutableStateOf(prefs.url) }
    var auto by remember { mutableStateOf(prefs.auto) }
    var busy by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf(statusText(context, prefs)) }
    var granted by remember { mutableStateOf<Set<String>>(emptySet()) }
    val sdk = remember { HealthConnectClient.getSdkStatus(context) }
    val available = sdk == HealthConnectClient.SDK_AVAILABLE

    suspend fun refreshGranted() {
        if (available) granted = HealthConnectClient.getOrCreate(context).permissionController.getGrantedPermissions()
    }
    val askPermissions = rememberLauncherForActivityResult(PermissionController.createRequestPermissionResultContract()) {
        granted = it
    }
    LaunchedEffect(Unit) {
        refreshGranted()
        Sync.schedule(context, prefs.auto && prefs.url.isNotEmpty())
    }

    Column(
        Modifier.safeDrawingPadding().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("BodyLens", fontSize = 30.sp, fontWeight = FontWeight.ExtraBold)
        Text(stringResource(R.string.intro))

        if (!available) {
            Text(stringResource(R.string.hc_missing), color = MaterialTheme.colorScheme.error)
            Button(onClick = {
                context.startActivity(Intent(Intent.ACTION_VIEW,
                    Uri.parse("market://details?id=com.google.android.apps.healthdata")))
            }) { Text(stringResource(R.string.hc_install)) }
        }

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
        if (available && HealthReader.BACKGROUND !in granted && have > 0)
            Text(stringResource(R.string.perm_background), fontSize = 13.sp, color = Color.Gray)

        Text(stringResource(R.string.step3), fontWeight = FontWeight.Bold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(stringResource(R.string.auto_label), Modifier.weight(1f))
            Switch(checked = auto, onCheckedChange = {
                auto = it; prefs.auto = it; Sync.schedule(context, it && prefs.url.isNotEmpty())
            })
        }
        Button(enabled = !busy && available && url.isNotBlank(), onClick = {
            busy = true
            scope.launch {
                try { Sync.run(context) } catch (_: Exception) { }
                Sync.schedule(context, prefs.auto)
                status = statusText(context, prefs)
                busy = false
            }
        }, modifier = Modifier.fillMaxWidth()) {
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
