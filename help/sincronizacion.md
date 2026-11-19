# Sincronización

Los datos de la báscula y del reloj llegan solos a tu cuenta. Se configuran en **Tu cuenta → Fuentes de datos**.

## Withings (báscula, y lo que Withings tenga del reloj)
- **Conectar Withings** te lleva a Withings para dar permiso; al volver, el servidor trae tus datos y desde entonces los lee solo cada pocos minutos.
- Trae pesadas y composición, actividad, entrenos, sueño (las 3 últimas noches se vuelven a pedir siempre, porque a veces se cierran tarde), SpO2, VO2 máx y ECG.
- Withings nunca pisa lo que llega de Apple Salud: solo rellena los huecos (por ejemplo, actividad suave e intensa o despertares).

## Apple Salud (Health Auto Export en el iPhone)
- **Crear mi dirección de envío** da una dirección personal; ponla como URL en cada automatización de Health Auto Export (tipo **API REST**, formato **JSON versión 2**).
- Para el **sueño sin resumir**, el rango de fechas: **últimos 2–7 días** (así llegan las noches que el reloj o AutoSleep cierran tarde). Para lo demás, «Desde la última sincronización».
- Apple Salud es la fuente principal de sueño, siestas, actividad, entrenos, pulso, VFC, SpO2, ECG, avisos, ciclo, ánimo y síntomas.
- Reglas del sueño: noche de 17:00 a 17:00, AutoSleep manda en el horario si lo hay (salvo que el reloj registre claramente más), profundo y REM del reloj, desvelos de 10 min o más, siestas de 10 min o más. Un envío nuevo corrige lo que esa app ya no tenga en el periodo que cubre.
- **Cambiar la dirección** invalida la anterior.

## Cómo te enteras
- La página abierta se actualiza sola cuando llegan datos (comprueba cada minuto y al volver a la pestaña).
- **Sincronizar ahora** (o el botón de la nube arriba) pide a Withings lo último al momento.

## Antes (puente con la hoja de Google)
Mientras una cuenta no conecte Withings ni reciba envíos directos, el servidor sigue leyendo su hoja de Google cada pocos minutos. La primera vez que llega algo directo, la cuenta pasa a tener sus datos en el servidor: antes se importa toda su hoja para no perder historial.
