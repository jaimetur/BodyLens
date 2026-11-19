package app.bodylens.android

import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.FloorsClimbedRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.HeartRateVariabilityRmssdRecord
import androidx.health.connect.client.records.MenstruationFlowRecord
import androidx.health.connect.client.records.OxygenSaturationRecord
import androidx.health.connect.client.records.Record
import androidx.health.connect.client.records.RespiratoryRateRecord
import androidx.health.connect.client.records.RestingHeartRateRecord
import androidx.health.connect.client.records.SexualActivityRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.Vo2MaxRecord
import androidx.health.connect.client.request.AggregateGroupByDurationRequest
import androidx.health.connect.client.request.AggregateRequest
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import org.json.JSONArray
import org.json.JSONObject
import java.time.Duration
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import kotlin.reflect.KClass

/**
 * Lee Health Connect y lo convierte al formato de Health Auto Export (el que ya entiende el servidor de BodyLens):
 * {"data": {"metrics": [...], "workouts": [...]}}.
 */
object HealthReader {
    val TYPES: List<KClass<out Record>> = listOf(
        StepsRecord::class, DistanceRecord::class, FloorsClimbedRecord::class, ActiveCaloriesBurnedRecord::class,
        HeartRateRecord::class, RestingHeartRateRecord::class, HeartRateVariabilityRmssdRecord::class,
        OxygenSaturationRecord::class, RespiratoryRateRecord::class, Vo2MaxRecord::class, SleepSessionRecord::class,
        ExerciseSessionRecord::class, MenstruationFlowRecord::class, SexualActivityRecord::class,
    )
    const val BACKGROUND = "android.permission.health.READ_HEALTH_DATA_IN_BACKGROUND"
    val PERMISSIONS: Set<String> = TYPES.map { HealthPermission.getReadPermission(it) }.toSet()

    private val FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss Z").withZone(ZoneId.systemDefault())
    private fun d(t: Instant) = FMT.format(t)

    class Result(val body: JSONObject, val counts: Map<String, Int>)

    suspend fun read(client: HealthConnectClient, from: Instant, to: Instant, sleepFrom: Instant): Result {
        val granted = client.permissionController.getGrantedPermissions()
        fun can(t: KClass<out Record>) = HealthPermission.getReadPermission(t) in granted
        val metrics = JSONArray()
        val counts = linkedMapOf<String, Int>()
        fun metric(name: String, units: String, data: JSONArray) {
            if (data.length() == 0) return
            metrics.put(JSONObject().put("name", name).put("units", units).put("data", data))
            counts[name] = data.length()
        }

        // ---- por horas: pasos, distancia, pisos, energía activa y pulso ----
        val start = from.truncatedTo(ChronoUnit.HOURS)
        val hourly = buildList {
            if (can(StepsRecord::class)) add(StepsRecord.COUNT_TOTAL)
            if (can(DistanceRecord::class)) add(DistanceRecord.DISTANCE_TOTAL)
            if (can(FloorsClimbedRecord::class)) add(FloorsClimbedRecord.FLOORS_CLIMBED_TOTAL)
            if (can(ActiveCaloriesBurnedRecord::class)) add(ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL)
            if (can(HeartRateRecord::class)) { add(HeartRateRecord.BPM_AVG); add(HeartRateRecord.BPM_MIN); add(HeartRateRecord.BPM_MAX) }
        }
        if (hourly.isNotEmpty() && start < to) {
            val steps = JSONArray(); val dist = JSONArray(); val floors = JSONArray(); val energy = JSONArray(); val hr = JSONArray()
            // de 30 en 30 días, para no pedir demasiados tramos de una vez
            var a = start
            while (a < to) {
                val b = minOf(a.plus(Duration.ofDays(30)), to)
                val groups = client.aggregateGroupByDuration(
                    AggregateGroupByDurationRequest(hourly.toSet(), TimeRangeFilter.between(a, b), Duration.ofHours(1))
                )
                for (g in groups) {
                    val t = d(g.startTime)
                    val r = g.result
                    r[StepsRecord.COUNT_TOTAL]?.let { if (it > 0) steps.put(JSONObject().put("date", t).put("qty", it)) }
                    r[DistanceRecord.DISTANCE_TOTAL]?.let { if (it.inMeters > 0) dist.put(JSONObject().put("date", t).put("qty", it.inKilometers)) }
                    r[FloorsClimbedRecord.FLOORS_CLIMBED_TOTAL]?.let { if (it > 0) floors.put(JSONObject().put("date", t).put("qty", it)) }
                    r[ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL]?.let { if (it.inKilocalories > 0) energy.put(JSONObject().put("date", t).put("qty", it.inKilocalories)) }
                    r[HeartRateRecord.BPM_AVG]?.let { avg ->
                        hr.put(JSONObject().put("date", t).put("Avg", avg)
                            .put("Min", r[HeartRateRecord.BPM_MIN] ?: avg).put("Max", r[HeartRateRecord.BPM_MAX] ?: avg))
                    }
                }
                a = b
            }
            metric("step_count", "count", steps)
            metric("walking_running_distance", "km", dist)
            metric("flights_climbed", "count", floors)
            metric("active_energy", "kcal", energy)
            metric("heart_rate", "count/min", hr)
        }

        // ---- valores sueltos ----
        val range = TimeRangeFilter.between(from, to)
        if (can(RestingHeartRateRecord::class))
            metric("resting_heart_rate", "count/min", samples(readAll(client, RestingHeartRateRecord::class, range)) { it.time to it.beatsPerMinute.toDouble() })
        if (can(HeartRateVariabilityRmssdRecord::class))
            metric("heart_rate_variability", "ms", samples(readAll(client, HeartRateVariabilityRmssdRecord::class, range)) { it.time to it.heartRateVariabilityMillis })
        if (can(OxygenSaturationRecord::class))
            metric("oxygen_saturation", "%", samples(readAll(client, OxygenSaturationRecord::class, range)) { it.time to it.percentage.value })
        if (can(RespiratoryRateRecord::class))
            metric("respiratory_rate", "count/min", samples(readAll(client, RespiratoryRateRecord::class, range)) { it.time to it.rate })
        if (can(Vo2MaxRecord::class))
            metric("vo2max", "ml/(kg·min)", samples(readAll(client, Vo2MaxRecord::class, range)) { it.time to it.vo2MillilitersPerMinuteKilogram })

        // ---- ciclo y actividad sexual (registros) ----
        if (can(MenstruationFlowRecord::class)) {
            val arr = JSONArray()
            for (r in readAll(client, MenstruationFlowRecord::class, range)) {
                val v = when (r.flow) {
                    MenstruationFlowRecord.FLOW_LIGHT -> "light"; MenstruationFlowRecord.FLOW_MEDIUM -> "medium"
                    MenstruationFlowRecord.FLOW_HEAVY -> "heavy"; else -> "unspecified"
                }
                arr.put(JSONObject().put("date", d(r.time)).put("value", v).put("source", r.metadata.dataOrigin.packageName))
            }
            metric("menstrual_flow", "", arr)
        }
        if (can(SexualActivityRecord::class)) {
            val arr = JSONArray()
            for (r in readAll(client, SexualActivityRecord::class, range)) {
                val v = when (r.protectionUsed) {
                    SexualActivityRecord.PROTECTION_USED_PROTECTED -> "protected"
                    SexualActivityRecord.PROTECTION_USED_UNPROTECTED -> "unprotected"; else -> "unspecified"
                }
                arr.put(JSONObject().put("date", d(r.time)).put("value", v).put("source", r.metadata.dataOrigin.packageName))
            }
            metric("sexual_activity", "", arr)
        }

        // ---- sueño: un tramo por fase (siempre se reenvían los últimos días, por si la noche llegó tarde) ----
        if (can(SleepSessionRecord::class)) {
            val arr = JSONArray()
            for (s in readAll(client, SleepSessionRecord::class, TimeRangeFilter.between(sleepFrom, to))) {
                val src = s.metadata.dataOrigin.packageName
                fun seg(a: Instant, b: Instant, v: String) =
                    arr.put(JSONObject().put("startDate", d(a)).put("endDate", d(b)).put("value", v).put("source", src))
                seg(s.startTime, s.endTime, "In Bed")
                if (s.stages.isEmpty()) seg(s.startTime, s.endTime, "Asleep")
                for (st in s.stages) {
                    val v = when (st.stage) {
                        SleepSessionRecord.STAGE_TYPE_DEEP -> "Deep"
                        SleepSessionRecord.STAGE_TYPE_REM -> "REM"
                        SleepSessionRecord.STAGE_TYPE_LIGHT -> "Core"
                        SleepSessionRecord.STAGE_TYPE_AWAKE, SleepSessionRecord.STAGE_TYPE_AWAKE_IN_BED,
                        SleepSessionRecord.STAGE_TYPE_OUT_OF_BED -> "Awake"
                        else -> "Asleep"
                    }
                    seg(st.startTime, st.endTime, v)
                }
            }
            metric("sleep_analysis", "hr", arr)
        }

        // ---- entrenamientos ----
        val workouts = JSONArray()
        if (can(ExerciseSessionRecord::class)) {
            for (w in readAll(client, ExerciseSessionRecord::class, TimeRangeFilter.between(from.minus(Duration.ofDays(1)), to))) {
                val wr = TimeRangeFilter.between(w.startTime, w.endTime)
                val m = buildSet {
                    if (can(ActiveCaloriesBurnedRecord::class)) add(ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL)
                    if (can(DistanceRecord::class)) add(DistanceRecord.DISTANCE_TOTAL)
                    if (can(HeartRateRecord::class)) { add(HeartRateRecord.BPM_AVG); add(HeartRateRecord.BPM_MIN); add(HeartRateRecord.BPM_MAX) }
                }
                val agg = if (m.isEmpty()) null else client.aggregate(AggregateRequest(m, wr))
                val o = JSONObject()
                    .put("id", w.metadata.id)
                    .put("name", workoutName(w.exerciseType, w.title))
                    .put("start", d(w.startTime)).put("end", d(w.endTime))
                    .put("duration", Duration.between(w.startTime, w.endTime).seconds)
                    .put("source", w.metadata.dataOrigin.packageName)
                agg?.get(ActiveCaloriesBurnedRecord.ACTIVE_CALORIES_TOTAL)?.let {
                    o.put("activeEnergyBurned", JSONObject().put("qty", it.inKilocalories).put("units", "kcal"))
                }
                agg?.get(DistanceRecord.DISTANCE_TOTAL)?.let {
                    if (it.inMeters > 0) o.put("distance", JSONObject().put("qty", it.inKilometers).put("units", "km"))
                }
                agg?.get(HeartRateRecord.BPM_AVG)?.let { avg ->
                    val h = JSONObject().put("avg", JSONObject().put("qty", avg))
                    agg[HeartRateRecord.BPM_MIN]?.let { h.put("min", JSONObject().put("qty", it)) }
                    agg[HeartRateRecord.BPM_MAX]?.let { h.put("max", JSONObject().put("qty", it)) }
                    o.put("heartRate", h)
                }
                workouts.put(o)
            }
        }
        if (workouts.length() > 0) counts["workouts"] = workouts.length()

        val data = JSONObject().put("metrics", metrics).put("workouts", workouts)
        return Result(JSONObject().put("data", data), counts)
    }

    private suspend fun <T : Record> readAll(client: HealthConnectClient, type: KClass<T>, range: TimeRangeFilter): List<T> {
        val out = mutableListOf<T>()
        var token: String? = null
        do {
            val r = client.readRecords(ReadRecordsRequest(recordType = type, timeRangeFilter = range, pageToken = token))
            out += r.records
            token = r.pageToken
        } while (!token.isNullOrEmpty())
        return out
    }

    private fun <T : Record> samples(list: List<T>, f: (T) -> Pair<Instant, Double>): JSONArray {
        val arr = JSONArray()
        for (r in list) {
            val (t, v) = f(r)
            arr.put(JSONObject().put("date", d(t)).put("qty", v).put("source", r.metadata.dataOrigin.packageName))
        }
        return arr
    }

    /** Nombres como los de Apple Salud, que el servidor ya traduce. */
    private fun workoutName(type: Int, title: String?): String = when (type) {
        ExerciseSessionRecord.EXERCISE_TYPE_WALKING -> "Walking"
        ExerciseSessionRecord.EXERCISE_TYPE_RUNNING -> "Running"
        ExerciseSessionRecord.EXERCISE_TYPE_RUNNING_TREADMILL -> "Indoor Run"
        ExerciseSessionRecord.EXERCISE_TYPE_BIKING -> "Cycling"
        ExerciseSessionRecord.EXERCISE_TYPE_BIKING_STATIONARY -> "Indoor Cycle"
        ExerciseSessionRecord.EXERCISE_TYPE_HIKING -> "Hiking"
        ExerciseSessionRecord.EXERCISE_TYPE_SWIMMING_POOL -> "Pool Swim"
        ExerciseSessionRecord.EXERCISE_TYPE_SWIMMING_OPEN_WATER -> "Open Water Swim"
        ExerciseSessionRecord.EXERCISE_TYPE_YOGA -> "Yoga"
        ExerciseSessionRecord.EXERCISE_TYPE_PILATES -> "Pilates"
        ExerciseSessionRecord.EXERCISE_TYPE_ELLIPTICAL -> "Elliptical"
        ExerciseSessionRecord.EXERCISE_TYPE_ROWING, ExerciseSessionRecord.EXERCISE_TYPE_ROWING_MACHINE -> "Rowing"
        ExerciseSessionRecord.EXERCISE_TYPE_STRENGTH_TRAINING, ExerciseSessionRecord.EXERCISE_TYPE_WEIGHTLIFTING -> "Traditional Strength Training"
        ExerciseSessionRecord.EXERCISE_TYPE_HIGH_INTENSITY_INTERVAL_TRAINING -> "High Intensity Interval Training"
        ExerciseSessionRecord.EXERCISE_TYPE_DANCING -> "Dance"
        ExerciseSessionRecord.EXERCISE_TYPE_STAIR_CLIMBING, ExerciseSessionRecord.EXERCISE_TYPE_STAIR_CLIMBING_MACHINE -> "Stair Stepper"
        ExerciseSessionRecord.EXERCISE_TYPE_SOCCER -> "Soccer"
        ExerciseSessionRecord.EXERCISE_TYPE_TENNIS -> "Tennis"
        else -> title?.takeIf { it.isNotBlank() } ?: "Other"
    }
}
