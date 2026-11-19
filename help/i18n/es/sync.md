<!-- en: 6223420ef26a82e8 -->
# Sincronización

Los datos de tu báscula y de tu reloj llegan solos a tu cuenta. Se configura en **Tu cuenta → Fuentes de datos**.

## Withings (báscula, y lo que Withings tenga del reloj)
- **Conectar Withings** te lleva a Withings para dar permiso; cuando vuelves, el servidor trae tus datos y desde entonces los lee solo cada pocos minutos.
- Trae pesadas y composición, actividad, entrenamientos, sueño (las últimas 3 noches se piden siempre de nuevo, porque a veces se cierran tarde), SpO2, VO2 máx y ECG.
- Withings nunca sobrescribe lo que llega de Apple Salud: solo rellena los huecos (por ejemplo la actividad suave e intensa o los despertares).

## Apple Salud (Health Auto Export en el iPhone)
- **Crear mi dirección de envío** te da una dirección personal; ponla como URL en cada automatización de Health Auto Export (tipo **REST API**, formato **JSON versión 2**).
- Para el **sueño sin resumir**, el intervalo de fechas es **últimos 2–7 días** (así se recogen las noches que el reloj o AutoSleep cierran tarde). Para todo lo demás, «Desde la última sincronización».
- Apple Salud es la fuente principal de sueño, siestas, actividad, entrenamientos, frecuencia cardiaca, HRV, SpO2, ECG, avisos, ciclo, ánimo y síntomas.
- Reglas del sueño: noche de 17:00 a 17:00, AutoSleep decide el horario si está (salvo que el reloj registre claramente más), profundo y REM del reloj, despertares de 10 min o más, siestas de 10 min o más. Un envío nuevo corrige lo que esa app ya no tiene en el periodo que cubre.
- **Cambiar la dirección** invalida la anterior.

## Android (Health Connect)
- Instala la app de BodyLens para Android: en **Tu cuenta → Fuentes de datos** hay un enlace para descargarla (`/android.apk`). Android te pedirá permiso para instalar apps de fuera de Google Play.
- En la app: pega la misma **dirección de envío** de antes, pulsa **Conceder permisos de Health Connect** (y acepta también «leer datos en segundo plano») y **Enviar ahora**.
- La primera vez envía los últimos 30 días; después, cada hora, lo que haya nuevo (el sueño de los últimos 3 días se reenvía siempre, por si una noche llega tarde).
- Envía: pasos, distancia, pisos, energía activa y frecuencia cardiaca por horas; frecuencia cardiaca en reposo, HRV, SpO2, respiración y VO2 máx; sueño con fases; entrenamientos; ciclo y actividad sexual. El servidor lo trata igual que lo que llega del iPhone.

## Cómo te enteras
- La página abierta se actualiza sola cuando llegan datos (comprueba cada minuto y cuando vuelves a la pestaña).
- **Sincronizar ahora** (o el botón de la nube de arriba) pide a Withings los últimos datos al instante.

## Antes (puente con la hoja de Google)
Mientras una cuenta no haya conectado Withings ni recibido envíos directos, el servidor sigue leyendo su hoja de Google cada pocos minutos. La primera vez que llega algo directamente, la cuenta pasa a guardar sus datos en el servidor: antes se importa toda su hoja para no perder historial.
