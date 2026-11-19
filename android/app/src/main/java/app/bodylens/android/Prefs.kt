package app.bodylens.android

import android.content.Context

/** Ajustes de la app: dirección de envío (lleva el token secreto), último envío y resultado. */
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

    var lastMessage: String
        get() = sp.getString("lastMessage", "") ?: ""
        set(v) = sp.edit().putString("lastMessage", v).apply()
}
