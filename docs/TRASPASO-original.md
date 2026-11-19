# BodyLens (antes «Báscula de Jaime») — traspaso a Claude Code (versión Docker para el NAS)

Documento para arrancar el proyecto en una sesión de Claude Code. Resume qué hay hecho, cómo está montado y qué hay que construir.

## 1. Qué es hoy

Una app web de una sola página, **BodyLens** (antes «Báscula de Jaime»), publicada como artefacto en claude.ai:
https://claude.ai/artifact/CZEknjHx3FHhChoctbFc87

Pestañas: Resumen, Peso, Cuerpo (Báscula / Medidas / Corazón / Bienestar), Actividad, Sueño, Comidas, Historial y Ajustes. Todo en español, tema claro y oscuro, pensada para iPhone (gestos de deslizar entre secciones, barra inferior, selector de ventana temporal flotante).

### Fuentes de datos actuales
- **Báscula Withings → Google Apps Script → hoja de Google «Peso Jaime 2026»** (ID `1aUMgruI3VycOCjbqH4_UvL8nS8i-mt1QFNiz6xaQx2Q`).
  - Proyecto de Apps Script: `1NEOQM5tetei6FUMfYZTjmIRSfx_64-kuRra-xZpDoDpbhjMJ9X3KCHy1` (aplicación web, implementación versión 5).
  - URL de la aplicación web: `https://script.google.com/macros/s/AKfycbyq4X7M4IRxqFM7ez4BYQ9SelLUPo1Wauc9zm4YgCfD8wubBL-rVKe5rytquF4D-7Ac/exec`, con `?accion=sincronizar | notas | pesos`.
  - Ese script hace el OAuth con Withings y trae pesadas, composición, sueño, actividad y entrenos. **Hay que exportar su código** (script.google.com → el proyecto → copiar los .gs), porque es la referencia para portar la sincronización al contenedor. Las credenciales de Withings están en `guardarCredenciales`: no subirlas nunca al repositorio; van a variables de entorno.
- **Espacio de datos del artefacto** (`window.claude.use('db')`), colección `bascula`. Documentos:
  - `peso`: `{cfg, cfgEdited, manual, notes, milestones, lastSync}`.
  - `hist-AAAA`: `{y, d:{'AAAA-MM-DD':[kg, grasa%, masaGrasa, músculo, agua(kg), hueso, origen]}}`.
  - `com-AAAA`: notas de comidas `{y, d:{fecha:{t:[...], s:[7 puntuaciones], app?}}}`.
  - `act-AAAA`, `slp-AAAA`, `wo-AAAA`: actividad, sueño y entrenos por año.
  - Medidas con cinta: `{v:1, e:{...}}`.
- **Copia de datos dentro de la página** (`PACK`: gzip + base64 de `{self, snap}`) para quien abre sin sesión. En Docker ya no hace falta.

## 2. Ficheros que van en este paquete

| Fichero | Qué es |
|---|---|
| `src/app_a.html` | Estilos (tokens de color claro/oscuro) y estructura HTML de todas las vistas |
| `src/app_b.html` | Núcleo: utilidades de fechas, `buildModel` (tendencia, plan, intentos, hitos, estadísticas), métricas `MET` |
| `src/app_c.html` | Interfaz: todas las vistas, gráficas SVG hechas a mano, hojas ampliadas, ajustes, gestos, sincronización |
| `src/build.py` | Une a+b+c en `app.html`, mete la copia de datos en `"@@PACK@@"` y genera `peso.html` |
| `src/snaptest.js` | Prueba rápida en Node de que la página arranca sin errores |
| `peso.html` | La página tal como está publicada hoy (versión 144) |
| `datos/snap.json` | **Tus datos reales** (peso desde 2009, notas, sueño, actividad…). Para sembrar la base de datos. **No subir a un repositorio público.** |

## 3. Qué hay que construir (Docker en el Synology)

1. **Servidor (Python + FastAPI) que sirva la app** tal cual, sin rehacer el diseño.
2. **Sustituir `window.claude`** por una pequeña capa en JS que implemente lo que la app usa:
   - `use('db')`: `collection(...).doc(...).get/set/update`, `onSnapshot`, `list`. Apuntará a una API REST del servidor que guarda en **SQLite** (volumen del NAS).
   - `use('user')`: siempre «dueño» (un solo usuario).
   - `use('artifact')` (autopublicarse con la copia de datos), `use('downloads')` y `use('mcp')` (Google Drive): eliminar o sustituir por equivalentes normales (descarga directa del navegador).
3. **Sembrar SQLite** con `datos/snap.json`.
4. **Sincronización con Withings** en el contenedor, portando la lógica del Apps Script: OAuth (con refresco de tokens), pesadas, composición, sueño, actividad y entrenos; tarea periódica y botón «Sincronizar». La hoja de Google pasa a ser opcional.
5. **Entrada de datos de Salud** (opcional, segunda fase): endpoint que reciba el JSON de Health Auto Export o de un atajo (VFC, pulso al despertar, sueño del reloj).
6. **Acceso**: por el proxy inverso del Synology con HTTPS, igual que DriveTestAnalyzer y PhotoMigrator. Como queda expuesto a internet, la app necesita **login propio** (son datos de salud).
7. **Despliegue**: GitHub (repositorio privado) + GitHub Actions que construya la imagen y la publique en GHCR; el NAS la actualiza.

### 3.1 Datos nuevos que traer de Withings en la sincronización (hoy no llegan)

Jaime quiere ver estos datos, que la app de Withings sí muestra (hay capturas en el chat original):

- **Saturación de oxígeno (SpO2)**: valor con estado y barra de rangos (85–90 baja, 90–95 por debajo de la media, 95–100 normal). Va en Sueño (nocturna) o en la sección Corazón.
- **ECG**: lista de registros (fecha, clasificación de Withings —ritmo sinusal normal, fibrilación auricular, no concluyente—, pulso) y, al tocar uno, el trazado sobre cuadrícula con desplazamiento y ampliación. Mostrar la clasificación de Withings tal cual con su aviso; no interpretar los ECG.
- **VO2 máx**: valor con estado (Baja…) y barra de rangos para su sexo y edad (Withings le da 37,6 / 41,0 / 44,9 como cortes), comparación con la media de su edad («edad cardiovascular»), percentil y evolución. Va en Actividad, como «Forma física».
- **Pulso en reposo** y, si llega de Salud, **VFC** y **pulso al despertar**.
- **Calidad respiratoria nocturna** («Evaluación de la calidad respiratoria»: Óptima…): en el resumen de sueño de Withings vienen campos de alteraciones respiratorias / apneas; va en Sueño.
- **Avisos de frecuencia cardiaca baja y alta** (eventos de los últimos 12 meses, p. ej. 48 lpm el 23 sept y 135 lpm el 28 jun 2025), si la API los expone; si no, detectarlos con los mínimos y máximos de pulso diarios y avisar con prudencia (no es diagnóstico).
- Ya están en la app y no hace falta añadirlos: pasos diarios con % del objetivo, pulso medio diario, estatura (Ajustes, 178 cm). Las escaleras (pisos) llegan como desnivel (`elev`) y se podrían mostrar.
- **Sueño, más detalle del resumen de Withings** (capturas de «Calidad del sueño» en el chat original):
  - Puntuación de sueño de Withings (`sleep_score`, 57 la noche del 1 nov) para mostrarla junto a la calificación propia de la app (80), explicando la diferencia.
  - Curva de pulso durante la noche (media, mínimo, máximo).
  - **VFC nocturna** (Withings da la media de los primeros y de los últimos 90 minutos: 45 / 44 ms) y su comparación con las noches anteriores.
  - **Frecuencia respiratoria** (media 18 rpm, rango 14–24).
  - Calidad respiratoria (Óptima) y ronquidos si llegan.
  - Gráfico de interrupciones sobre el hipnograma de la noche.
  - **Siestas** («Siestas y otras mediciones»), separadas de la noche principal.
  - Tarjetas de detalle por componente (duración, pulso, VFC, profundidad, regularidad, interrupciones) con barra de rangos y texto explicativo, como en Withings.
- **Error detectado en los datos actuales**: la noche del 31 oct → 1 nov está guardada como 06:56–14:23 (6 h 53 dormido, 33 min profundo, 1 h 29 REM), pero Withings la da como 06:55–14:56 (7 h 28: profundo 36 min, REM 2 h 02, ligero 4 h 50). La sincronización la leyó **antes de que terminara la noche** y no la volvió a actualizar. La nueva sincronización debe **volver a pedir siempre las últimas 2–3 noches** y sobrescribirlas.
- Propuesta de ubicación: una sección nueva **Corazón** (ECG, SpO2, pulso en reposo y durmiendo, VFC).
- Fecha de nacimiento: ya está en Ajustes (`cfg.birth`); los rangos de grasa (Gallagher 2000) y las campanas usan la franja de edad. Usarla también para el VO2 máx.

### 3.2 Pendientes de la app (propuestos, no hechos)

- **Informe de salud en PDF** del periodo elegido (peso, composición, sueño, actividad, pulso, notas), para descargar y compartir. Botón en Ajustes y al final de Resumen.
- **Notas por día**: cuadro «Notas» al final de la vista de cada día (Peso, Sueño, Actividad). Se guardan en `doc.notes` (ya existe: son las etiquetas que salen en la gráfica de peso).


### 3.3 Perfiles (añadido el 3 nov 2026)
- La app tiene perfiles: «Jaime Tur» (principal, id `''`) y «Laura Romero» (id `laura`, marcado como «ciclo»).
- El perfil principal usa los documentos de siempre; los demás usan `pf-<id>-<documento>` (p. ej. `pf-laura-hklog`, `pf-laura-peso`). La lista vive en el documento `perfiles` (`{v:1,list:[{id,name,col,cycle?}]}`).
- Los datos del ciclo que lleguen de Apple Salud al perfil principal se pasan solos al perfil marcado como «ciclo» (`routeCycle`).
- La copia de la página guarda los demás perfiles en `snap.prof[<id>]` y la lista en `snap.profs`.
- En Docker: un solo usuario de acceso, pero conservar los perfiles como espacios de datos separados.


### 3.4 Objetivo: no depender de la hoja de Google (decisión de Jaime, 3 nov 2026)
- En Docker, el servidor habla **directamente con la API de Withings** (OAuth con refresco de tokens guardados en el servidor, nunca en la página) y guarda todo en SQLite. La hoja «Peso Jaime 2026» y el Apps Script dejan de hacer falta.
- **Withings en tiempo real**: suscribirse a las notificaciones de Withings (`notify/subscribe`, webhook HTTPS en el NAS) para que cada pesada o noche llegue sola; además, una tarea periódica de respaldo que vuelva a pedir las últimas 2–3 noches.
- **Apple Salud**: Health Auto Export manda el JSON por POST directamente a un endpoint del servidor (con token), en lugar de al Apps Script.
- El botón «Sincronizar» de la app llamará al servidor (`POST /api/sync`), sin abrir pestañas.
- Migración: sembrar SQLite con `datos/snap.json` (incluye perfiles en `prof`/`profs`) y, si se quiere, importar una última vez la hoja para no perder nada.
- La hoja puede quedar como exportación opcional (copia de seguridad), nunca como fuente.


### 3.5 Marca: BodyLens (3 nov 2026)
- Nombre de la app: **BodyLens**. Logo en `branding/`: `icon.svg` (icono), `wordmark.svg` (logo con nombre), PNG de 512, 192 y 180 (apple-touch-icon) y 32 px.
- En Docker, servir como favicon y en el manifiesto web (PWA):
  `<link rel="icon" type="image/svg+xml" href="/icon.svg">`, `<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">`, `<link rel="apple-touch-icon" href="/apple-touch-icon.png">` y `manifest.webmanifest` con `icon-192.png` e `icon-512.png`, `name: "BodyLens"`, `theme_color: "#3B7BF2"`.
- Antes de comercializarla: comprobar marca en EUIPO/USPTO (clases 9 y 44), App Store/Google Play y dominios.

### 3.6 Fuentes de datos: Salud manda, Withings rellena (5 nov 2026)
- **Fuente principal: Apple Salud** (Health Auto Export) para sueño, siestas, actividad diaria, entrenamientos, pulso, SpO2, VO2, ECG del reloj, avisos y registros. **Withings** solo para **peso y composición** (músculo, agua, hueso, grasa: Salud no los tiene o solo tiene una copia tardía) y para rellenar huecos (días u horas sin Salud, campos que Salud no da, como actividad suave/intensa o despertares). Nunca pisa un dato de Salud.
- Ya funciona así en el Apps Script de la hoja (implementación v11, 5 nov 2026): `actividadDesdeSalud_` (día a partir de las horas guardadas en «Salud»), `suenoDesdeSalud_` / `guardarNochesSalud_` (noche = episodio más largo que acaba antes de las 17:00; el resto, siestas ≥10 min; los tramos se guardan en «Sueño Salud (fases)» para rehacer la noche aunque llegue en varios envíos), `entrenosDesdeSalud_` (sustituye la copia de Withings del mismo entreno, inicio a <10 min) y `mezclaWithings_` / `rellenaHuecos_`. Portar esta lógica tal cual al servidor.
- Health Auto Export manda **un tipo de dato por automatización**; Jaime tiene una por tipo, todas a la misma URL con `?token=`: Métricas de Salud (resumidas por hora), Análisis del sueño **sin resumir** (tramos de fases), Entrenamientos, ECG, Notificaciones de frecuencia cardiaca, Ciclo, Estado de ánimo, Síntomas y Medicamentos. El endpoint del servidor debe aceptar los dos formatos de sueño (resumido por noche y por tramos) y preferir los tramos.
- **Varios usuarios**: diseñar el servidor multiusuario desde el principio (login propio, `user_id` en todas las tablas, un token de envío por usuario: `POST /api/ingest/<token>`, OAuth de Withings por usuario). Los perfiles actuales (`pf-<id>-…`) pasan a ser usuarios o perfiles de un usuario.

### 3.7 Android: módulo `android/` (decisión de Jaime, 5 nov 2026)
- Ni Apple Salud ni Health Connect tienen API en la nube: solo se leen desde una app en el móvil. Google Fit está en cierre; su sustituto es **Health Connect** (datos solo en el dispositivo). Por eso el servidor nunca podrá «tirar» de ellos: hace falta una app que los **empuje**.
- Repositorio: carpeta `android/` con una app pequeña en **Kotlin** (Jetpack Compose para las 2–3 pantallas):
  1. Configuración: URL del servidor y login (o pegar/escanear un QR con el token de envío del usuario, que genera el servidor).
  2. Permisos de lectura de Health Connect: pasos, distancia, pisos, calorías activas y basales, minutos de ejercicio, frecuencia cardiaca y en reposo, VFC, SpO2, frecuencia respiratoria, VO2 máx, temperatura, peso, sueño (sesiones y fases), entrenamientos (ExerciseSession) y ciclo menstrual.
  3. `WorkManager` periódico (cada hora y al abrir la app) que lee lo nuevo desde el último envío (tokens de cambios de Health Connect) y lo manda a `POST /api/ingest/<token>`.
- Formato de envío: el **mismo JSON que Health Auto Export** (`data.metrics[]` con `name/units/data`, `data.workouts[]`, sueño por tramos con `startDate/endDate/value`), para que el servidor tenga un único traductor. Campo `source` con el origen real (p. ej. el reloj Wear OS o Samsung Health).
- GitHub Actions: un workflow aparte que compile el APK firmado (y opcionalmente el AAB) y lo adjunte a la release; el de Docker no cambia.
- Más adelante, opcional: la misma idea en iOS (app propia con HealthKit) para no depender de Health Auto Export si se comercializa.

## 4. Entorno de desarrollo deseado

- Ver los cambios **al instante, sin pasar por GitHub Actions**: `docker compose` de desarrollo en el Mac (o en el NAS) con el código montado como volumen y recarga automática (`uvicorn --reload`, y la página se sirve directamente desde `src/`, sin compilar).
- Actions solo para generar la imagen de producción.
- El artefacto de Claude puede seguir sirviendo de laboratorio para probar ideas de diseño.

## 5. Decisiones y preferencias ya tomadas (respetarlas)

- Diseño actual idéntico; nada de rediseños.
- Ventana temporal sincronizada entre módulos; Historial con 6 meses / 1 año / 3 / 5 / 10 años / Todo.
- Sueño: «Calificación» por defecto antes que «Horas»; horario objetivo (laborables y fin de semana, por defecto acostarse 00:00 y despertarse 07:00) en Ajustes; banco de sueño con saldo neto de 7 noches y hoja ampliada con gráfica y «Informe».
- Intentos de pérdida de peso: por defecto visibles el actual, el último y el mejor; el mejor siempre en verde; etiquetas ACTUAL / ÚLTIMO / MEJOR; rebote medido como la subida máxima en los 6 meses siguientes al mínimo.
- Tablas sin desplazamiento lateral en el iPhone siempre que se pueda.
- Respuestas y textos de la app en español (España).
