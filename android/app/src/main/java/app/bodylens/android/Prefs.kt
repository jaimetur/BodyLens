package app.bodylens.android

import android.content.Context

/** Settings of the app: server address, sending address (it carries the secret token), last sending and result. */
class Prefs(context: Context) {
    private val sp = context.getSharedPreferences("bodylens", Context.MODE_PRIVATE)

    var url: String
        get() = sp.getString("url", "") ?: ""
        set(v) = sp.edit().putString("url", v.trim()).apply()

    var auto: Boolean
        get() = sp.getBoolean("auto", true)
        set(v) = sp.edit().putBoolean("auto", v).apply()

    /** Hasta dónde se envió con éxito (milisegundos Unix); 0 = nunca. */
    var sentUntil: Long
        get() = sp.getLong("sentUntil", 0L)
        set(v) = sp.edit().putLong("sentUntil", v).apply()

    var lastRun: Long
        get() = sp.getLong("lastRun", 0L)
        set(v) = sp.edit().putLong("lastRun", v).apply()

    var lastOk: Boolean
        get() = sp.getBoolean("lastOk", false)
        set(v) = sp.edit().putBoolean("lastOk", v).apply()

    /** Address of the BodyLens server the app shows (https://…); empty until the first set-up. */
    var server: String
        get() = sp.getString("server", "") ?: ""
        set(v) = sp.edit().putString("server", v.trim().trimEnd('/')).apply()

    /** When the app last opened the Health Connect screen on its own (to install it or give the permissions); 0 = never. */
    var askedAt: Long
        get() = sp.getLong("askedAt", 0L)
        set(v) = sp.edit().putLong("askedAt", v).apply()

    /** The system's question about battery limits was already shown once on its own. */
    var askedBattery: Boolean
        get() = sp.getBoolean("askedBattery", false)
        set(v) = sp.edit().putBoolean("askedBattery", v).apply()

    var lastMessage: String
        get() = sp.getString("lastMessage", "") ?: ""
        set(v) = sp.edit().putString("lastMessage", v).apply()
}
