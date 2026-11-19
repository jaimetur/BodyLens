<!-- en: dc806c1efaaed472 -->
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
- **Parejas:** dos cuentas se pueden unir para compartir y editar juntas los registros de ciclo e intimidad. Invitas a tu pareja con su usuario o su correo desde Tu cuenta → Cuenta → Pareja; le llega un correo con la invitación (si no hay ninguna cuenta con ese usuario o correo, te lo dice al momento) y a ti otro cuando la acepta. Un perfil de la app se puede mover a la cuenta propia de esa persona.
- **Tu cuenta:**
  - **Cuenta:** perfil, correo, idioma y contraseña, pareja, fuentes de datos, sincronización e importación.
  - **Perfiles:** niveles de acceso a los datos de tu cuenta (todos los perfiles ven los mismos datos), explicados en el propio panel. A cada perfil, también al principal, se le pueden dar solo los módulos que elijas, con fichas como en DriveTest Analyzer; en el menú solo ve esos. Los módulos incluyen Objetivos, plan y comidas, Tu cuenta (que también abre Perfiles y Datos y copias) y, en administradores, Administración; al menos un perfil tiene que tener esos, y los demás pueden tener los módulos que quieras. Los perfiles ya no tienen pareja ni ciclo propios.
  - **El PIN decide el perfil:** el PIN que se escribe en la pantalla de bloqueo abre el perfil que lo tiene; si varios perfiles comparten PIN, al entrar con él se ven los módulos de todos (el panel avisa cuando pones un PIN que ya usa otro perfil). Desaparece el PIN privado aparte para Ciclo e intimidad: Íntimo es un módulo como los demás, y un perfil solo exporta a PDF los módulos que tiene.
  - **Orden y perfil principal:** los perfiles se ordenan arrastrando su asa ⋮⋮; el primero es el perfil principal. Al abrir la app se entra en el perfil principal si no tiene PIN; si lo tiene, se pide y el PIN que se escriba decide el perfil. Un perfil con PIN se bloquea solo tras 1 minuto sin actividad, y cada perfil se reabre en la sección y las pestañas que tenía abiertas. En el móvil, la barra de abajo muestra las secciones más grandes cuando el perfil tiene menos.
  - **Datos personales** (altura, sexo, fecha de nacimiento) es un panel de la pestaña **Cuenta**, debajo de Contraseña.
  - **Datos y copias:** de dónde llegan los datos del móvil, origen de los datos, copia completa y exportación a CSV.
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
- **Ayuda:** una sección Ayuda en la app con la ayuda de cada módulo, el README y el registro de cambios, sin salir de la herramienta. Es pública: se puede leer sin entrar (enlace en la pantalla de entrar, con su propio selector de idioma).
  - Los documentos están escritos solo en inglés y se traducen automáticamente al idioma de cada cuenta con LibreTranslate, un traductor gratuito que funciona en el propio servidor junto a BodyLens (la API de Claude se puede poner como alternativa opcional y de pago en Administración → **Traductor**); cada traducción se conserva hasta que cambia el texto en inglés.
  - El español viene ya traducido con la app (`help/i18n/es/`), así que no necesita traductor.
  - Todos los documentos se traducen de antemano a todos los idiomas al arrancar el servidor y se revisan cada 10 minutos: solo se vuelven a traducir los documentos cuyo texto en inglés ha cambiado (su huella), así que la ayuda se abre ya traducida.
- **Tamaño del texto** por cuenta (Pequeño, Normal, Grande, Muy grande) en *Tu cuenta*, igual que el idioma; el nuevo Normal es algo más grande que antes.
- **Temas** por cuenta en *Tu cuenta*: Automático (según el dispositivo), Diurno, Nocturno, Sepia, Océano, Bosque y Alto contraste, para la app y las páginas del servidor.
- **Minutos hasta que un perfil con PIN se bloquea**, a elegir en *Tu cuenta* (1 por defecto).
- **Entrada manual más cómoda:** cada campo muestra como referencia el último valor de la cuenta (vacío si no hay ninguno, en vez de un ejemplo fijo) y, en el móvil, al tocar un número se abre una rueda para deslizar el valor, con Teclado para escribirlo. Sin un valor anterior, la rueda empieza en un valor típico para el sexo, la edad y la altura del perfil (Datos personales).

#### 🚀 Mejoras:
- **Un único importador** (Tu cuenta → Datos y copias) para la copia completa y para el `snap.json` de la versión anterior. Si la copia tiene varios perfiles, eliges cuál importar.
- **Comidas:**
  - Cada nota está en la fila de su comida, con botones grandes, y el Agua tiene su propia fila.
  - El registro del día va antes de la pérdida estimada.
  - El registro del día muestra arriba las últimas 4 semanas (de lunes a domingo) en lugar de una sola; las flechas saltan 4 semanas.
- **Correo:** el servidor saluda al servidor de correo con su nombre público en vez de con la dirección privada del contenedor, que los filtros de spam penalizan; el correo de prueba es como un aviso real (saludo, para qué sirve, enlace a la app) en vez de una sola frase.
- **Panel de perfiles:** cada fila se adapta al ancho del panel, así que los botones de PIN ya no quedan fuera de la vista.
- **Entrada manual en todos los módulos:** la tarjeta de pesada manual está en Peso (también cuando aún no hay pesadas, en vez de una página vacía); Actividad tiene tarjetas para apuntar a mano la actividad del día (pasos, minutos de ejercicio, calorías activas) y los entrenamientos; Sueño, una para apuntar a mano cualquier noche, y Cuerpo → Corazón, una para apuntar el pulso en reposo, la VFC, la saturación de oxígeno y el VO2 máx. Los datos de tus fuentes para el mismo día mandan. Las medidas, las comidas, el ánimo y los registros personales ya se podían apuntar a mano.
- **Android al mismo nivel que el iPhone:** todas las pantallas, avisos y mensajes de «sin datos» que solo hablaban de Apple Salud / Health Auto Export explican también el camino de Android (Health Connect con la app de BodyLens), con la misma dirección de envío para los dos.
- **Ánimo:** se pueden registrar ánimos pasados, con fecha y hora o tocando el día en el calendario.
- **Historial** pasa a llamarse **Historial de pesos**.
- **Pantallas anchas:** la app llega a 1600 px, y Tu cuenta y Administración aprovechan el ancho con columnas.
- **Barra lateral:**
  - Tu cuenta y Administración (solo administradores) son secciones de la app, con la barra lateral.
  - «Gestionar perfiles» pasa a Tu cuenta.
  - **Ajustes** pasa a llamarse **Objetivos, plan y comidas**; su pestaña **Datos y copias** pasa a Tu cuenta.
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
