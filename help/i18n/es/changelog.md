<!-- en: 20cf3e40ce00a574 -->
# 🗓️ CHANGELOG
[Registro de cambios](/CHANGELOG.md) de las versiones anteriores

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Cambios incompatibles:
- **De un artefacto de claude.ai a un servidor propio:** BodyLens ya no vive en claude.ai y pasa a un contenedor Docker en el NAS (`https://bodylens.jaimetur.cloud`). Los datos están en una base de datos SQLite del servidor, no en el espacio de datos del artefacto. Entras con un usuario y una contraseña de BodyLens, no con tu cuenta de Claude.
- **Ya no hace falta la hoja de Google:** Withings y Apple Salud envían los datos directamente al servidor. La hoja y su Apps Script quedan solo como puente temporal, para las cuentas que aún no se han migrado.
- **Idioma por defecto: inglés.** Las cuentas nuevas empiezan en inglés; las existentes conservan el español.

#### 🌟 Novedades:
- **Despliegue con Docker (NAS Synology):**
  - Imagen `jaimetur/bodylens` en Docker Hub, construida por GitHub Actions en cada push a la rama de la versión.
  - El stack de Dockhand se ejecuta como `docker_limited:docker_users`, detrás de un proxy inverso HTTPS.
  - Comprobación de estado (`/healthz`) y un aviso si no se puede escribir en `/data`.
- **Despliegue en caliente:** `tools/deploy.sh` copia el código al NAS y el contenedor lo usa sin esperar a una imagen nueva. Las páginas abiertas muestran un aviso «BodyLens se ha actualizado» con un botón para recargar.
- **Varias cuentas, cada una con sus propios datos:**
  - Entras con usuario y contraseña; las contraseñas se guardan con argon2 y las sesiones en el servidor.
  - Cada cuenta tiene un usuario, nombre y apellidos, un correo válido y único y una contraseña de al menos 4 caracteres, escrita dos veces.
- **Alta de cuentas:**
  - Petición de cuenta desde la pantalla de acceso, aprobada por la administración; los avisos van por correo.
  - Enlaces de invitación de un solo uso.
  - Cuenta inicial `admin`/`admin123`, que la pantalla de acceso muestra mientras conserva la contraseña por defecto.
- **Correo saliente (SMTP)** para peticiones, aprobaciones, contraseñas temporales y avisos, configurable desde Administración.
- **Parejas:** dos cuentas se pueden unir para compartir y editar juntas los registros de ciclo e intimidad. Un perfil de la app se puede mover a la cuenta propia de esa persona.
- **Tu cuenta:**
  - **Cuenta:** perfil, correo, idioma y contraseña, pareja, fuentes de datos, sincronización e importación.
  - **Perfiles y Datos personales:** gestión de los perfiles de la app.
- **Administración** (cuentas de administrador), con estas pestañas:
  - **Usuarios:** editar usuario, nombre, correo y contraseña; activar o desactivar con un interruptor; dar o quitar el rol de admin; restablecer la contraseña; borrar.
  - **Peticiones de acceso** e **Invitaciones**.
  - **Correo:** ajustes SMTP y correo de prueba.
  - **Withings:** datos de la aplicación de desarrollador.
  - **Copias de seguridad** y **Fuentes de datos**.
  - El servidor nunca se queda sin una cuenta de administración activa.
- **Withings directo:**
  - Conexión OAuth por cuenta, con el token guardado cifrado.
  - Sincronización cada pocos minutos y al instante cuando Withings avisa (webhook).
  - Trae pesadas y composición, actividad, entrenamientos, sueño, SpO2, VO2 máx y ECG.
- **Apple Salud directo:** Health Auto Export envía los datos a una dirección personal de cada cuenta. Es un port completo de la lógica del Apps Script:
  - Sueño por segmentos (AutoSleep más Apple Watch, despertares y siestas, noche de 17:00 a 17:00).
  - Actividad diaria, entrenamientos, ECG, avisos y registros (ciclo, ánimo, síntomas…).
  - Salud tiene prioridad sobre Withings, que solo rellena huecos.
- **App para Android (Health Connect):**
  - Envía por horas pasos, distancia, pisos, energía, frecuencia cardiaca, HRV, SpO2, respiración, VO2 máx, sueño con fases, entrenamientos, ciclo y actividad sexual.
  - Usa el mismo formato que Health Auto Export.
  - El APK lo construye GitHub Actions y se descarga desde Tu cuenta (`/android.apk`).
- **Datos en el servidor:**
  - Las pestañas de la hoja pasan a ser tablas del servidor, y el libro que lee la página se genera a partir de ellas.
  - Paridad con la hoja original comprobada en las 16 pestañas.
  - La primera conexión con Withings o la primera subida de Salud importa antes la hoja, para no perder historial.
- **Copia de seguridad diaria de la base de datos** a las 03:30, en `/data/backups`. Se conservan las últimas 30 y se pueden descargar desde Administración.
- **Multiidioma:** inglés, español, catalán, francés, italiano, alemán, portugués, neerlandés, chino y japonés.
  - Cada cuenta elige el suyo, y los correos llegan en el idioma de quien los recibe.
  - El catálogo base está en inglés (`src/frontend/i18n/`), con una guía para contribuir con traducciones.
  - El idioma también se elige en los formularios de petición de acceso y de invitación.
- **Ayuda:** una sección Ayuda en la app con la ayuda de cada módulo, el README y el registro de cambios, sin salir de la herramienta.
  - Los documentos están escritos solo en inglés y se traducen automáticamente al idioma de cada cuenta con la API de Claude (Administración → **Traductor**, con la clave de la API de Anthropic guardada cifrada); cada traducción se conserva hasta que cambia el texto en inglés, y los idiomas que usan las cuentas se preparan de antemano.

#### 🚀 Mejoras:
- **Un único importador** (Ajustes → Datos y copias) para la copia completa y para el `snap.json` de la versión anterior. Si la copia tiene varios perfiles, eliges cuál importar.
- **Comidas:**
  - Cada nota está en la fila de su comida, con botones grandes, y el Agua tiene su propia fila.
  - El registro del día va antes de la pérdida estimada.
  - El registro del día muestra arriba las últimas 4 semanas (de lunes a domingo) en lugar de una sola; las flechas saltan 4 semanas.
- **Ánimo:** se pueden registrar ánimos pasados, con fecha y hora o tocando el día en el calendario.
- **Historial** pasa a llamarse **Historial de pesos**.
- **Pantallas anchas:** la app llega a 1600 px, y Tu cuenta y Administración aprovechan el ancho con columnas.
- **Barra lateral:**
  - Tu cuenta y Administración (solo administradores) son secciones de la app, con la barra lateral.
  - «Gestionar perfiles» pasa a Tu cuenta.
- **Menú del avatar:** muestra el nombre completo e incluye Tu cuenta, Administración y **Cerrar sesión**, en rojo.
- **Línea de comandos de administración** (`python -m app.accounts.cli`): crear cuentas con contraseña temporal, invitaciones, contraseñas, usuarios, fuentes y mover perfiles.

#### 🐛 Correcciones:
- **Seguridad:** el registro de accesos ya no guarda la dirección de subida de Apple Salud, los códigos OAuth ni las invitaciones.
- **Withings:** la dirección de retorno acepta las pruebas y los avisos de Withings (POST y HEAD).
- **Navegador:**
  - Las páginas y sus estilos se revalidan en cada despliegue, así que no quedan copias obsoletas en la caché.
  - Tu cuenta y Administración se pueden mostrar dentro de la app.

#### 📚 Documentación:
- **El inglés es el idioma oficial del proyecto:** código, documentación y mensajes de commit. `README.md` completo; el README, la ayuda y el registro de cambios se escriben solo en inglés y se muestran traducidos en la app.
- Ayuda de uso por módulo en `help/en/` (se muestra en la Ayuda de la app en cada idioma).
- `docs/DEPLOYMENT.md` (NAS, Dockhand, despliegue en caliente, Withings, Apple Salud, Android).
- El material que ya no se usa sale del repositorio: el plan de migración original, el encargo y el traspaso (`docs/`) y los scripts de Apps Script y de Salud (`legacy/`); las reglas de datos que hay que conservar pasan a `AGENTS.md`.
- `AGENTS.md` con las reglas del repositorio (diseño intacto, paridad de datos, secretos y datos personales fuera, idioma de trabajo, textos e idiomas).
- `src/frontend/i18n/README.md`: cómo añadir o mejorar una traducción.

---

## Release: v0.0.1
### Release Date: 2026-11-01
Versión de partida: la app tal como se publicó como artefacto de claude.ai (versión de página 144) cuando Claude Work se la pasó a Claude Code.

#### ⚠️ Cambios incompatibles:

#### 🌟 Novedades:
- **App web de una sola página**, publicada como artefacto de claude.ai. Los datos estaban en el espacio de datos del artefacto (colección `bascula`), y la página llevaba dentro una copia para quien la abriera sin sesión.
- **Resumen:** peso de tendencia, progreso del plan, «hoy de un vistazo» (preparación, sueño, saldo de sueño, HRV, pasos) y avisos y análisis automáticos.
- **Peso:** tendencia suavizada, plan con ritmos objetivo, proyección, semanas, calendario e hitos.
- **Cuerpo:**
  - **Báscula:** grasa, músculo, agua y hueso; IMC y FFMI con rangos por edad y sexo.
  - **Medidas** con cinta.
  - **Corazón:** frecuencia cardiaca en reposo, HRV, SpO2, VO2 máx, ECG y avisos de frecuencia cardiaca.
  - **Bienestar.**
- **Actividad:** pasos, calorías y minutos de ejercicio con anillos y objetivos; entrenamientos y su relación con el peso.
- **Sueño:** la última noche con sus fases, saldo de sueño de 7 noches, siestas, horario objetivo y análisis.
- **Comidas:** una nota diaria de lo que comes (comidas, agua, ejercicio y «pecados») y su efecto estimado en el peso.
- **Íntimo:** ciclo con previsión, sexualidad y ánimo, protegidos por un PIN privado.
- **Historial:** años de pesadas (desde 2009), intentos de pérdida y rebotes.
- **Perfiles** dentro de la app, cada uno con sus propios datos y, si se quiere, un PIN. El ciclo de Apple Salud va automáticamente al perfil marcado como «ciclo».
- **Informe en PDF** del periodo elegido y **copias de seguridad** completas en JSON y CSV.
- **Fuentes de datos mediante una hoja de Google** («Peso Jaime 2026») con su Apps Script:
  - Withings: pesadas, composición, actividad, sueño, entrenamientos, SpO2, VO2 y ECG.
  - Health Auto Export desde el iPhone: Apple Salud, que tiene prioridad sobre Withings.
  - Reglas propias de sueño: mezcla de AutoSleep y Apple Watch, ventana de 17:00 a 17:00, despertares y siestas.
- **Interfaz:**
  - Tema claro y oscuro y marca **BodyLens**, con icono y logo.
  - Pensada para el iPhone: se instala como app desde Safari, gestos de deslizamiento entre secciones, barra inferior y selector de periodo flotante.
  - Todo en español.

#### 🚀 Mejoras:

#### 🐛 Correcciones:

#### 📚 Documentación:
- Documento de traspaso de Claude Work con lo que se había hecho, cómo estaba montado y lo que quedaba por construir.
