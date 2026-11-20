<!-- en: 68e1b2838a3a449d -->
# Sincronización

BodyLens no te pide que escribas tus datos: los recibe de tu báscula, tu móvil y tu reloj. Solo tienes que conectar
cada servicio una vez. Todo se configura en **Tu cuenta → Fuentes de datos**, y allí se ve el estado de cada fuente.

¿Cuáles necesitas?

| Tienes… | Conecta |
|---|---|
| Una báscula Withings (o un reloj Withings) | **Withings** |
| Un iPhone (y quizá un Apple Watch, AutoSleep…) | **Apple Salud** con la app Health Auto Export |
| Un móvil Android (Samsung, Pixel, un reloj Wear OS, Fitbit…) | **Android** con la app de BodyLens para Health Connect |

Puedes conectar varios: Apple Salud o Android son la fuente principal de sueño, actividad y corazón; Withings trae tus
pesadas y tu composición corporal y rellena los huecos.

Si a tu cuenta le llegan datos **de Apple Salud y de Android a la vez**, una de las dos manda y la otra solo rellena
los días y tipos de datos que le falten a la primera (sueño: noches enteras; entrenamientos: la misma sesión no se
duplica). Elígela en **Tu cuenta → Fuentes de datos → Fuente que manda**: **Automática** (la opción por defecto:
Android, salvo que la mayoría de tus datos lleguen de Apple Salud), **Apple Salud** o **Android (Health Connect)**. La
elección se aplica a los datos que llegan a partir de ese momento.

## Withings, paso a paso

1. Abre BodyLens y ve a **Tu cuenta → Fuentes de datos**.
2. En el recuadro **Withings**, pulsa **Conectar Withings**.
   - Si no aparece el botón, el servidor aún no está preparado para Withings: pídeselo a quien lo administra (se hace
     una vez en **Administración → Withings**).
3. Se abre Withings. Entra con tu cuenta de Withings (la misma de la app de Withings: [App Store](https://apps.apple.com/app/id542701020), [Google Play](https://play.google.com/store/apps/details?id=com.withings.wiscale2); o créala en la [web de Withings](https://account.withings.com/)).
4. Withings te pregunta si BodyLens puede leer tus datos: pulsa **Permitir**.
5. Vuelves a BodyLens y el recuadro pone **conectado**. La primera vez BodyLens trae tus datos recientes; puede tardar
   un minuto.

A partir de ahí BodyLens lee Withings cada pocos minutos, y al momento cuando tu báscula manda una pesada nueva.
Para dejarlo, pulsa **Desconectar** en el mismo recuadro.

Qué trae: pesadas y composición (grasa, músculo, agua, hueso), actividad, entrenamientos, sueño, SpO2, VO2 máx y ECG.
Withings nunca pisa lo que llega de Apple Salud o de Android: solo rellena los huecos.

## Apple Salud (iPhone), paso a paso

El iPhone guarda tus datos de salud solo en el teléfono, así que hace falta una app que se los mande a BodyLens.
BodyLens usa **Health Auto Export**, de la App Store. El envío automático (las **automatizaciones**) necesita su
versión Premium.

### 1. Crea tu dirección de envío en BodyLens

1. En BodyLens, ve a **Tu cuenta → Fuentes de datos**, recuadro **Apple Salud / Android**.
2. Pulsa **Crear mi dirección de envío**. Aparece una dirección larga (`https://…/api/ingest/hae/…`).
3. Pulsa **Copiar la dirección**. Abre BodyLens en el propio iPhone, para copiarla allí y pegarla en la app.

La dirección es personal: quien la tenga puede mandar datos a tu cuenta. No la compartas. Si crees que alguien la
tiene, pulsa **Cambiar la dirección** y pon la nueva en tus automatizaciones (la anterior deja de funcionar).

### 2. Instala Health Auto Export y dale acceso a Salud

1. Instala [Health Auto Export – JSON+CSV](https://apps.apple.com/app/id1115567069) desde la App Store y ábrela.
2. Cuando pida acceso a Salud, permite **todos** los tipos de datos (puedes cambiarlo después en **Ajustes → Salud →
   Acceso a datos y dispositivos** del iPhone).
3. Consigue la versión Premium, que hace falta para las automatizaciones.

### 3. Crea las automatizaciones

Health Auto Export manda un tipo de datos por automatización, así que crea una para cada tipo que quieras (por lo
menos las dos primeras). En cada una:

1. Abre la pestaña **Automatizaciones** (Automations) y crea una nueva.
2. Tipo: **REST API**.
3. URL: pega tu **dirección de envío**.
4. Formato: **JSON**, versión **2**.
5. Elige los datos (mira la tabla) y el intervalo de fechas.
6. Activa la automatización y guárdala.

| Automatización | Datos que elegir | Intervalo de fechas | Notas |
|---|---|---|---|
| Métricas de salud | **Health Metrics**, todas | Desde la última sincronización | Resumir (agrupar) por **hora** |
| Sueño | **Health Metrics**, solo **Sleep Analysis** | **Últimos 2–7 días** | **Desactiva** el resumen, para que lleguen las fases |
| Entrenamientos | **Workouts** | Desde la última sincronización | |
| ECG | **ECG** | Desde la última sincronización | Si tienes un Apple Watch con ECG |
| Avisos del corazón | **Heart Rate Notifications** | Desde la última sincronización | Avisos de pulso alto, bajo y ritmo irregular |
| Ciclo | **Cycle Tracking** | Desde la última sincronización | Si apuntas tu ciclo en Salud |
| Ánimo, síntomas, medicamentos | **State of Mind**, **Symptoms**, **Medications** | Desde la última sincronización | Opcional |

La automatización del sueño mira varios días atrás porque AutoSleep y el reloj a veces cierran una noche tarde;
mandar una noche otra vez la corrige, nunca la duplica.

### 4. Comprueba que funciona

1. En cada automatización, usa su botón para enviar ahora (exportación manual).
2. En BodyLens, **Tu cuenta → Fuentes de datos**: el recuadro pasa de **esperando datos** a **recibiendo**, con la hora
   del último envío. Tu sueño, tus pasos y tu pulso aparecen en la app en menos de un minuto.

Health Auto Export envía en segundo plano, pero iOS solo se lo permite si desbloqueas el teléfono de vez en cuando.
Si dejan de llegar tus datos, abre Health Auto Export un momento.

### Opcional: AutoSleep, para un sueño más preciso

[AutoSleep](https://apps.apple.com/app/id1164801111) (App Store, de pago, una sola vez) es una app de iPhone que
calcula tu sueño a partir del Apple Watch, aunque no actives ningún modo de sueño: cuándo te duermes, los desvelos de
la noche y cuándo te levantas. Mucha gente encuentra sus horas más precisas que las del propio reloj. No la
necesitas: sin AutoSleep, BodyLens usa el sueño que registra el Apple Watch.

BodyLens no se conecta a AutoSleep directamente: AutoSleep escribe cada noche en Apple Salud, y Health Auto Export la
manda a BodyLens con el resto de tu sueño. Para configurarlo:

1. Instala AutoSleep y ábrela una vez. Su configuración inicial te pregunta cómo usas el reloj por la noche; síguela.
2. Cuando pida acceso a Salud, permítele **escribir el sueño** (Análisis del sueño). Puedes comprobarlo después en
   **Ajustes → Salud → Acceso a datos y dispositivos → AutoSleep** del iPhone.
3. Duerme con el reloj puesto y cárgalo en otro momento del día (AutoSleep lo necesita en la muñeca toda la noche).
4. Por la mañana, abre AutoSleep una vez, para que cierre la noche y la escriba en Salud (suele hacerlo sola un rato
   después de que te levantes).
5. Nada más: la automatización de **Sueño** de Health Auto Export ya la manda (por eso mira 2–7 días atrás:
   AutoSleep a veces cierra una noche tarde).

Cómo la usa BodyLens: cuando una noche tiene datos de AutoSleep, la hora de acostarte, la de levantarte, el tiempo
dormido y los desvelos salen de AutoSleep, y las fases (profundo, REM) del Apple Watch. Si el reloj registra
claramente más sueño que AutoSleep (por ejemplo, si AutoSleep se perdió parte de la noche), manda el reloj. El origen
de cada noche se ve en **Sueño**.

## Android (Health Connect), paso a paso

En Android, las apps de salud (Samsung Health, Google Fit, Fitbit, un reloj Wear OS…) guardan sus datos en **Health
Connect**, el almacén de datos de salud de Android (el equivalente de Apple Salud en el iPhone). Health Connect solo
guarda los datos en el móvil; la **app de BodyLens para Android** es la que los lee allí y los envía a tu cuenta cada
hora (el equivalente de Health Auto Export en el iPhone, pero ya preparada para BodyLens: sin automatizaciones que
crear).

La app de BodyLens es todo BodyLens en tu móvil: muestra la misma app que el navegador (cada cambio en el servidor
aparece en ella al momento) y añade Health Connect, las descargas de tu PDF y de las copias, el botón de atrás de
Android y una pantalla de inicio.

### 1. Asegúrate de que tus datos llegan a Health Connect

1. Health Connect viene con Android 14 y posteriores (en **Ajustes → Seguridad y privacidad → Privacidad → Health
   Connect**, o busca «Health Connect» en Ajustes). En versiones anteriores, instala
   [Health Connect](https://play.google.com/store/apps/details?id=com.google.android.apps.healthdata) desde Google Play.
2. En la app que registra tu salud (Samsung Health, Fitbit, Google Fit, la app de tu reloj…), activa la
   sincronización con Health Connect. En Samsung Health, por ejemplo: **Ajustes → Health Connect**.

### 2. Instala la app de BodyLens

- Desde **Google Play**, cuando esté publicada allí; o
- desde tu servidor: abre BodyLens en el navegador del móvil, ve a **Tu cuenta → Fuentes de datos** y toca el enlace
  para descargar **la app de BodyLens** (`/android.apk`). Android avisa de que viene de fuera de Google Play: permite
  instalar apps desde tu navegador.

### 3. Ábrela y entra

1. La primera vez, la app te pide la **dirección del servidor** (la misma con la que abres BodyLens en el navegador;
   ya viene rellenada). Pulsa **Continuar**.
2. Entra con tu usuario y contraseña de BodyLens (o crea una cuenta: mira [Cuentas](accounts.md)).
3. La app se une sola a tu cuenta y abre ella sola su pantalla de Health Connect. Si falta Health Connect o está
   desactualizado, la pantalla te lo indica y **Abrir Health Connect en Google Play** lo instala; al volver, la app te
   pide los permisos. Permite todos los tipos de datos y también **leer datos en segundo plano**, para que pueda
   enviar con la app cerrada. Después Android pregunta si la app puede funcionar en segundo plano sin límites de
   batería: permítelo, o Android puede retrasar o parar el envío de cada hora. La pantalla de Health Connect muestra
   las dos cosas, con un botón para lo que falte. Si la dejas sin ellos, la app te lo recuerda como mucho una vez por
   semana.
4. Ya está: envía tus datos al momento y después cada hora ella sola.

Dentro de la app, **Tu cuenta → Fuentes de datos** muestra el estado de Health Connect (permisos concedidos y último
envío) con **Enviar ahora**, **Permisos de Health Connect** y **Cambiar el servidor**. La pantalla de Health Connect
tiene un botón **Cerrar** para volver a la app.

**BodyLens Bridge** es una segunda app, más pequeña, para quien usa BodyLens en el navegador: solo envía tus datos
de Health Connect (`/android-bridge.apk`). Instálala, abre **Tu cuenta → Fuentes de datos** en el navegador del móvil
y pulsa **Configurar BodyLens Bridge**: se abre ya unida a tu cuenta y te pide los permisos. O copia la dirección con
**Copiar la dirección** y pégala en la app. No la necesitas si usas la app de BodyLens.

La primera vez manda los últimos 30 días; después, cada hora, lo que haya nuevo. La app muestra la hora y el
resultado del último envío, y en BodyLens el recuadro pasa a **recibiendo**.

## Cómo ves que llegan tus datos

- **Tu cuenta → Fuentes de datos** muestra cada fuente: **conectado** / **sin conectar** para Withings, y
  **recibiendo** / **esperando datos** para Apple Salud y Android, indicando de dónde llegan los datos (Apple Salud,
  Android o los dos, en los dos últimos días) y el último envío de cada uno, con cuántos datos no se han usado porque
  manda la otra fuente.
- La página abierta se actualiza sola cuando llegan datos (lo comprueba cada minuto y cuando vuelves a la pestaña).
- **Sincronizar ahora** (o el botón de la nube de arriba) pide a Withings los últimos datos al momento.

## Si no llegan tus datos

| Problema | Qué hacer |
|---|---|
| No aparece el botón **Conectar Withings** | Quien administra tiene que preparar Withings una vez (Administración → Withings). |
| Withings sigue **sin conectar** después de permitir | Vuelve a pulsar **Conectar Withings** y asegúrate de pulsar **Permitir** en la página de Withings. |
| Apple Salud se queda en **esperando datos** | Comprueba que la URL de cada automatización es exactamente tu dirección de envío, que el formato es JSON versión 2 y que la automatización está activada; después envíala a mano. |
| El sueño llega sin fases | En la automatización del sueño, desactiva el resumen y usa los últimos 2–7 días. |
| Dejan de llegar datos del iPhone | Abre Health Auto Export un momento; iOS pausa las apps en segundo plano. |
| Has cambiado tu dirección de envío | Pon la nueva dirección en todas las automatizaciones (iPhone) o en la app de BodyLens (Android). |
| Android no envía nada | Comprueba que tu app de salud sincroniza con Health Connect y que la app de BodyLens tiene todos los permisos, también el de leer en segundo plano. |
