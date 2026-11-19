# 🗓️ CHANGELOG
[Changelog](/CHANGELOG.md) de las versiones publicadas

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Breaking Changes:
- **De artefacto de claude.ai a servidor propio:** BodyLens deja de vivir en claude.ai y pasa a un contenedor Docker en el NAS (`https://bodylens.jaimetur.cloud`). Los datos están en una base SQLite del servidor, no en el espacio de datos del artefacto. Se entra con usuario y contraseña de BodyLens, no con la cuenta de Claude.
- **Ya no hace falta la hoja de Google:** Withings y Apple Salud mandan los datos directamente al servidor. La hoja y su Apps Script quedan solo como puente provisional, para las cuentas que todavía no se han pasado.
- **Idioma predeterminado: inglés.** Las cuentas nuevas empiezan en inglés; las que ya existían conservan el español.

#### 🌟 New Features:
- **Despliegue en Docker (NAS Synology):**
  - Imagen `jaimetur/bodylens` en Docker Hub, construida por GitHub Actions en cada push a la rama de la versión.
  - El stack de Dockhand corre como `docker_limited:docker_users`, con proxy inverso HTTPS.
  - Comprobación de salud (`/healthz`) y aviso si no se puede escribir en `/data`.
- **Despliegue en caliente:** `tools/deploy.sh` copia el código al NAS y el contenedor lo usa sin esperar a una imagen nueva. Las páginas abiertas avisan de «BodyLens se ha actualizado» con un botón para recargar.
- **Varias cuentas, cada una con sus datos:**
  - Se entra con usuario y contraseña; las contraseñas se guardan con argon2 y las sesiones en el servidor.
  - Cada cuenta tiene usuario, nombre y apellidos, un correo válido y único y una contraseña de al menos 4 caracteres, escrita dos veces.
- **Alta de cuentas:**
  - Petición de cuenta desde la pantalla de entrar, que aprueba la administración; los avisos van por correo.
  - Enlaces de invitación de un solo uso.
  - Cuenta inicial `admin`/`admin123`, que la pantalla de entrar muestra mientras conserve la contraseña por defecto.
- **Correo saliente (SMTP)** para peticiones, aprobaciones, contraseñas provisionales y avisos, configurable desde Administración.
- **Pareja:** dos cuentas pueden unirse para compartir y editar juntas el ciclo y la intimidad. Un perfil de la app puede pasarse a la cuenta propia de esa persona.
- **Tu cuenta:**
  - **Cuenta:** perfil, correo, idioma y contraseña, pareja, fuentes de datos, sincronización e importación.
  - **Perfiles y Datos personales:** la gestión de perfiles de la app.
- **Administración** (cuentas administradoras), con estas pestañas:
  - **Usuarios:** editar usuario, nombre, correo y contraseña; activar o desactivar con un interruptor; hacer o quitar admin; restablecer la contraseña; borrar.
  - **Peticiones de acceso** e **Invitaciones**.
  - **Correo:** configuración SMTP y correo de prueba.
  - **Withings:** datos de la aplicación de desarrollador.
  - **Copias** de seguridad y **Fuentes de datos**.
  - El servidor nunca se queda sin una cuenta de administración activa.
- **Withings directo:**
  - Conexión OAuth por cuenta, con el token guardado cifrado.
  - Sincronización cada pocos minutos y al momento cuando Withings avisa (webhook).
  - Trae pesadas y composición, actividad, entrenamientos, sueño, SpO2, VO2 máx y ECG.
- **Apple Salud directo:** Health Auto Export envía a una dirección personal de cada cuenta. Es un port completo de la lógica del Apps Script:
  - Sueño por tramos (AutoSleep más Apple Watch, desvelos y siestas, noche de 17:00 a 17:00).
  - Actividad del día, entrenamientos, ECG, avisos y registros (ciclo, ánimo, síntomas…).
  - Salud manda sobre Withings, que solo rellena huecos.
- **App de Android (Health Connect):**
  - Envía cada hora pasos, distancia, pisos, energía, pulso, VFC, SpO2, respiración, VO2 máx, sueño con fases, entrenamientos, ciclo y actividad sexual.
  - Usa el mismo formato que Health Auto Export.
  - El APK lo compila GitHub Actions y se descarga desde Tu cuenta (`/android.apk`).
- **Datos en el servidor:**
  - Las pestañas de la hoja pasan a ser tablas del servidor, y el libro que lee la página se genera desde ellas.
  - Paridad comprobada con la hoja original en las 16 pestañas.
  - La primera conexión de Withings o el primer envío de Salud importan antes la hoja, para no perder historial.
- **Copia de seguridad diaria** de la base a las 03:30, en `/data/backups`. Se conservan 30 y se pueden bajar desde Administración.
- **Multi-idioma:** inglés, español, catalán, francés, italiano, alemán, portugués, neerlandés, chino y japonés.
  - Cada cuenta elige el suyo, y los correos llegan en el idioma de quien los recibe.
  - El catálogo base está en inglés (`src/frontend/i18n/`), con una guía para colaborar con traducciones.

#### 🚀 Enhancements:
- **Un solo importador** (Ajustes → Datos y copias) para la copia completa y para el `snap.json` de la versión anterior. Si la copia trae varios perfiles, se elige cuál importar.
- **Comidas:**
  - Cada puntuación va en la fila de su comida, con botones grandes, y Agua tiene su propia fila.
  - El registro del día va antes que la pérdida estimada.
  - El registro del día muestra arriba las últimas 4 semanas (de lunes a domingo) en lugar de una sola; las flechas saltan 4 semanas.
- **Estado de ánimo:** se pueden apuntar estados de días pasados, con fecha y hora o tocando el día en el calendario.
- **Historial** pasa a llamarse **Historial de pesos**.
- **Pantallas anchas:** la app llega a 1600 px, y Tu cuenta y Administración aprovechan el ancho con columnas.
- **Barra lateral:**
  - Tu cuenta y Administración (solo para administradores) son secciones de la app, con la barra lateral.
  - «Gestionar perfiles» pasa a Tu cuenta.
- **Menú del avatar:** muestra el nombre completo e incluye Tu cuenta, Administración y **Cerrar sesión**, en rojo.
- **Línea de órdenes de administración** (`python -m app.accounts.cli`): crear cuentas con contraseña provisional, invitaciones, contraseñas, usuarios, fuentes y pasar perfiles.

#### 🐛 Bug fixes:
- **Seguridad:** el registro de accesos ya no guarda la dirección de envío de Apple Salud, los códigos OAuth ni las invitaciones.
- **Withings:** la dirección de retorno acepta las pruebas y los avisos de Withings (POST y HEAD).
- **Navegador:**
  - Las páginas y sus estilos se revalidan en cada despliegue, así que no se quedan copias viejas en caché.
  - Tu cuenta y Administración se pueden mostrar dentro de la app.

#### 📚 Documentation:
- `README.md` completo y ayuda de uso por módulo en `help/`.
- `docs/MIGRACION.md` (plan por fases) y `docs/DESPLIEGUE.md` (NAS, Dockhand, despliegue en caliente, Withings, Apple Salud, Android).
- `AGENTS.md` con las reglas del repositorio (diseño intacto, paridad de datos, secretos y datos personales fuera, idioma del trabajo, textos e idiomas).
- `src/frontend/i18n/README.md`: cómo añadir o mejorar una traducción.

---

## Release: v0.0.1
### Release Date: 2026-11-19
Versión de partida: la app tal como estaba publicada como artefacto de claude.ai (versión 144 de la página) cuando Claude Work la pasó a Claude Code.

#### ⚠️ Breaking Changes:

#### 🌟 New Features:
- **App web de una sola página**, publicada como artefacto de claude.ai. Los datos estaban en el espacio de datos del artefacto (colección `bascula`), y la página llevaba dentro una copia para quien la abría sin sesión.
- **Resumen:** peso de tendencia, progreso del plan, «hoy de un vistazo» (preparación, sueño, saldo de sueño, VFC, pasos) y avisos y conclusiones automáticas.
- **Peso:** tendencia suavizada, plan con ritmos objetivo, proyección, semanas, calendario e hitos.
- **Cuerpo:**
  - **Báscula:** grasa, músculo, agua y hueso; IMC y FFMI con rangos por edad y sexo.
  - **Medidas** con cinta.
  - **Corazón:** pulso en reposo, VFC, SpO2, VO2 máx, ECG y avisos de frecuencia.
  - **Bienestar.**
- **Actividad:** pasos, calorías y minutos de ejercicio con anillos y objetivos; entrenamientos y su relación con el peso.
- **Sueño:** última noche con fases, saldo de sueño de 7 noches, siestas, horario objetivo y análisis.
- **Comidas:** nota diaria de lo que comes (comidas, agua, deporte y «pecados») y su efecto estimado en el peso.
- **Íntimo:** ciclo con previsión, sexualidad y estado de ánimo, protegidos con un PIN privado.
- **Historial:** años de pesadas (desde 2009), intentos de pérdida de peso y rebotes.
- **Perfiles** dentro de la app, cada uno con sus datos y, si se quiere, un PIN. El ciclo de Apple Salud pasa solo al perfil marcado como «ciclo».
- **Informe PDF** del periodo elegido y **copias** completas en JSON y CSV.
- **Fuentes de datos a través de una hoja de Google** («Peso Jaime 2026») con su Apps Script:
  - Withings: pesadas, composición, actividad, sueño, entrenos, SpO2, VO2 y ECG.
  - Health Auto Export desde el iPhone: Apple Salud, que manda sobre Withings.
  - Reglas de sueño propias: mezcla de AutoSleep y Apple Watch, ventana de 17:00 a 17:00, desvelos y siestas.
- **Interfaz:**
  - Tema claro y oscuro y marca **BodyLens**, con icono y logo.
  - Pensada para el iPhone: se instala como app desde Safari, gestos para pasar de sección, barra inferior y selector de periodo flotante.
  - Todo en español.

#### 🚀 Enhancements:

#### 🐛 Bug fixes:

#### 📚 Documentation:
- Documento de traspaso (`docs/TRASPASO-original.md`) con qué había hecho, cómo estaba montado y qué faltaba por construir.
