package app.bodylens.android

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result = try {
        Sync.run(applicationContext)
        Result.success()
    } catch (e: SecurityException) {
        Result.failure()   // sin permiso para leer en segundo plano: no sirve reintentar
    } catch (e: Exception) {
        if (runAttemptCount < 3) Result.retry() else Result.failure()
    }
}
