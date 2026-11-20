<!-- en: 366561b443ec448d -->
# 🗓️ CHANGELOG
[Registro de cambios](/CHANGELOG.md) de las versiones anteriores

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Cambios incompatibles:
- **De un artefacto de claude.ai a un servidor propio:** BodyLens ya no vive en claude.ai y pasa a un contenedor Docker en el NAS (`https://bodylens.jaimetur.cloud`). Los datos están en una base de datos SQLite del servidor, no en el espacio de datos del artefacto. Entras con un usuario y una contraseña de BodyLens, no con tu cuenta de Claude.
- **Ya no hace falta la hoja de Google:** Withings, Apple Salud y Android envían los datos directamente al servidor, y cada cuenta guarda allí sus datos; la hoja y su Apps Script ya no se usan.
- **Idioma por defecto: inglés.** Las cuentas nuevas empiezan en inglés; las existentes conservan el español.

#### 🌟 Novedades:
- **Despliegue con Docker (NAS Synology):**
  - Imagen `jaimetur/bodylens` en Docker Hub, construida por GitHub Actions en cada push a la rama de la versión.
  - El stack de Dockhand se ejecuta como `docker_limited:docker_users`, detrás de un proxy inverso HTTPS.
  - Comprobación de estado (`/healthz`) y un aviso si no se puede escribir en `/data`.
- **Despliegue en caliente:** `tools/deploy.sh` copia el código al NAS y el contenedor lo usa sin esperar a una imagen nueva. Las páginas abiertas muestran un aviso «BodyLens se ha actualizado» con un botón para recargar.
- **Varias cuentas, cada una con sus propios datos:**
  - Entras con tu usuario o tu correo y una contraseña; las contraseñas se guardan con argon2 y las sesiones en el servidor.
  - Cada cuenta tiene un usuario, nombre y apellidos, un correo válido y único y una contraseña de al menos 4 caracteres, escrita dos veces.
- **Alta de cuentas:**
  - Petición de cuenta desde la pantalla de acceso, aprobada por la administración; los avisos van por correo.
  - Enlaces de invitación de un solo uso.
  - Cuenta inicial `admin`/`admin123`, que la pantalla de acceso muestra mientras conserva la contraseña por defecto.
- **Correo saliente (SMTP)** para peticiones, aprobaciones, contraseñas temporales, invitaciones de pareja y avisos, configurable desde Administración. El servidor saluda al servidor de correo con su nombre público, y el correo de prueba es como un aviso real; Administración → Correo explica qué hacer si llega al spam.
- **Parejas:** dos cuentas se pueden unir para compartir y editar juntas los registros de ciclo e intimidad. Invitas a tu pareja con su usuario o su correo desde Tu cuenta → Cuenta → Pareja; le llega un correo con la invitación (si no hay ninguna cuenta con ese usuario o correo, te lo dice al momento) y a ti otro cuando la acepta. Un perfil de la app se puede mover a la cuenta propia de esa persona.
- **Tu cuenta:**
  - **Cuenta:** perfil, correo, idioma, tamaño del texto (Pequeño, Normal, Grande, Muy grande; el nuevo Normal es algo más grande que antes), tema (Automático según el dispositivo, Diurno, Nocturno, Sepia, Océano, Bosque, Alto contraste, Rosa, Lavanda, Menta, Atardecer o Grafito, para la app y las páginas del servidor), minutos sin actividad hasta que un perfil con PIN se bloquea (1 por defecto), contraseña, datos personales (altura, sexo, fecha de nacimiento), pareja y fuentes de datos.
  - **Perfiles** y **Datos y copias** (de dónde llegan los datos del móvil, origen de los datos, copia completa e importación, exportación a CSV).
- **Perfiles** (Tu cuenta → Perfiles):
  - Niveles de acceso a los datos de la cuenta: todos los perfiles ven los mismos datos, y cada uno, también el principal, ve solo los módulos elegidos con fichas (como en DriveTest Analyzer), incluidos Objetivos, plan y comidas, Tu cuenta y Administración. Al menos un perfil tiene que tener esos tres. Un perfil solo exporta a PDF los módulos que tiene, y en el móvil la barra de abajo muestra más grandes las secciones cuando son menos.
  - El PIN decide el perfil: escrito en la pantalla de bloqueo, abre el perfil que lo tiene; los perfiles que comparten PIN se abren juntos, con todos sus módulos (el panel avisa cuando un PIN ya está en uso). Íntimo es un módulo como los demás, sin un PIN privado aparte.
  - Los perfiles se ordenan arrastrando su asa ⋮⋮, y el primero es el perfil principal. Al abrir la app se entra directamente en él si no tiene PIN; si lo tiene, se pide y el PIN decide el perfil. Un perfil con PIN se bloquea solo tras los minutos sin actividad elegidos en Tu cuenta.
  - Cada perfil se reabre en la sección y las pestañas que tenía abiertas, también tras un reinicio o en otro dispositivo (se guarda en la cuenta, en el servidor).
- **Administración** (cuentas de administrador), con estas pestañas:
  - **Usuarios:** editar usuario, nombre, correo y contraseña; activar o desactivar con un interruptor; dar o quitar el rol de admin; restablecer la contraseña; borrar.
  - **Peticiones de acceso** e **Invitaciones**.
  - **Correo:** ajustes SMTP y correo de prueba.
  - **Withings:** datos de la aplicación de desarrollador.
  - **Copias de seguridad** y **Traductor**.
  - El servidor nunca se queda sin una cuenta de administración activa.
- **Withings directo:**
  - Conexión OAuth por cuenta, con el token guardado cifrado.
  - Sincronización cada pocos minutos y al instante cuando Withings avisa (webhook).
  - Trae pesadas y composición, actividad, entrenamientos, sueño, SpO2, VO2 máx y ECG.
- **Apple Salud directo:** Health Auto Export envía los datos a una dirección personal de cada cuenta. Es un port completo de la lógica del Apps Script:
  - Sueño por segmentos (AutoSleep más Apple Watch, despertares y siestas, noche de 17:00 a 17:00).
  - Actividad diaria, entrenamientos, ECG, avisos y registros (ciclo, ánimo, síntomas…).
  - Salud tiene prioridad sobre Withings, que solo rellena huecos.
- **App para Android:**
  - Todo BodyLens en el móvil: la app web del servidor en una carcasa nativa, así que cada cambio del servidor se ve en ella al momento, con lo que una página web no puede hacer sola: la dirección del servidor al empezar, una pantalla de inicio y otra sin conexión, descargas de PDF y copias, elegir archivos para importar, el botón atrás de Android (primero cierra lo que está abierto), los bordes del sistema reservados para deslizar y las barras del color del tema.
  - Al entrar, la app se une sola a la cuenta y pide los permisos de Health Connect; Tu cuenta → Fuentes de datos muestra el estado de Health Connect con **Enviar ahora**, **Permisos de Health Connect** y **Cambiar el servidor**.
  - Envía por horas pasos, distancia, pisos, energía, frecuencia cardiaca, HRV, SpO2, respiración, VO2 máx, sueño con fases, entrenamientos, ciclo y actividad sexual, a la misma dirección de envío que Health Auto Export y en el mismo formato.
  - **BodyLens Bridge**, una segunda app hecha con el mismo código, solo envía los datos de Health Connect (para quien usa BodyLens en el navegador); se pueden tener las dos instaladas, y Tu cuenta → Fuentes de datos → **Configurar BodyLens Bridge** la abre ya unida a la cuenta (`/android-bridge.apk`).
  - El APK y el AAB para Google Play los construye GitHub Actions; el APK también se descarga desde el servidor (`/android.apk`, enlazado desde la página de presentación y Tu cuenta). `tools/android-keystore.sh` crea la clave de firma que necesita Google Play.
  - Todas las pantallas, los mensajes de «sin datos» y la ayuda explican el camino de Android al mismo nivel que el del iPhone.
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
- **Versiones** (adaptado de DriveTest Analyzer): `tools/CreateUpdateRelease.py` crea la rama de la siguiente versión con su número de versión, la versión de Android y el bloque vacío del registro de cambios (inglés y español), la confirma y la sube, o actualiza la versión y la fecha de la versión actual; el flujo **🚀 Release** publica una versión en GitHub con las notas de su bloque del registro de cambios, el código fuente y el APK de Android. El APK continuo de Android se publica como «Android app (rolling build)».
- **Cuentas de pago:** además de las invitaciones y las peticiones aprobadas, se puede crear una cuenta con una suscripción de 1,50 € al mes o 12 € al año (1 € al mes), con 7 días de prueba gratis: en la web con Stripe (tarjeta, Google Pay o Apple Pay; la cuenta se crea cuando la página de pago confirma la suscripción) o en la app de Android con Google Play. Tu cuenta → Suscripción muestra el plan, y la suscripción se puede cambiar entre mensual y anual (desde la siguiente renovación) o dar de baja sin borrar la cuenta. Una cuenta cuya suscripción termina (dada de baja, sin pagar o con el tiempo gratis acabado) queda en solo lectura 30 días, con una barra roja en la app que indica el día en que se borrará: se pueden ver y descargar sus datos, pero no añadir nada nuevo, y se detienen la sincronización y los datos que envían sus fuentes; se le avisa por correo tres veces y se borra con sus datos si no se renueva. Administración tiene los ajustes de Google Play y de Stripe. Las cuentas de administración propias del despliegue (`admin`, la de por defecto, y `BODYLENS_ADMIN_USER`) son gratis de por vida.
- **Página de presentación** en `/` para visitantes, en inglés o español (según el idioma del navegador, con un selector EN | ES): qué hace cada módulo, con un carrusel infinito por módulo con un vídeo por pestaña que recorre toda la pestaña (de una cuenta de demostración con datos inventados; GitHub Actions los vuelve a grabar solo cada vez que cambia la app, así que los módulos y pestañas nuevos aparecen solos), una sección de temas de color, la web en pantalla grande, la promoción de lanzamiento, fuentes, descarga de la app de Android (y su enlace de Google Play cuando esté publicada, en Administración → Google Play), precios, preguntas y alta.
- **Borrar mi cuenta** en Tu cuenta (con la contraseña): borra la cuenta y todos sus datos y cancela su suscripción.
- **Páginas legales** (públicas, en todos los idiomas): política de privacidad (`/privacy`), condiciones de uso (`/terms`) y cómo borrar una cuenta (`/delete-account`), con los datos del responsable en Administración → Datos legales; enlazadas desde la página de entrada, Tu cuenta y la app.
- **Códigos de invitación:** al darse de alta con un código (`INVITACION_AMIGOS`, de por vida, por defecto, en Administración → Invitaciones; dan igual mayúsculas, tildes y espacios) se crea al momento una cuenta gratis durante lo que dure el código (1, 3 o 6 meses, 1 año, hasta una fecha o de por vida, a elegir en cada código, una fecha de caducidad opcional y un máximo de cuentas opcional, por ejemplo las 100 primeras, tras los que el código se borra, alias como `LAUNCH` para `LANZAMIENTO` que comparten sus plazas y la opción de anunciarlo en la página principal como promoción con un contador de las plazas que quedan. La lista de usuarios de Administración muestra cómo se creó cada cuenta: el código que usó o su suscripción, con su plan y su método de pago (tarjeta, Google Pay o Apple Pay), aunque las cuentas creadas con él conservan su tiempo), salvo que un administrador le cambie la fecha de fin en Usuarios → Editar → Acceso gratuito. Ya no se piden cuentas: la página de entrada tiene, en lugar de «Pide una», una tarjeta grande **Crear mi cuenta** que abre el alta en un diálogo, con los planes y el código de invitación.

#### 🚀 Mejoras:
- **Un único importador** (Tu cuenta → Datos y copias) para la copia completa y para el `snap.json` de la versión anterior. Si la copia tiene varios perfiles, eliges cuál importar.
- **Comidas:**
  - Cada nota está en la fila de su comida, con botones grandes, y el Agua tiene su propia fila.
  - El registro del día va antes de la pérdida estimada.
  - El registro del día muestra arriba las últimas 4 semanas (de lunes a domingo) en lugar de una sola; las flechas saltan 4 semanas.
- **Entrada manual en todos los módulos**, para quien no lleva reloj ni conecta el móvil:
  - La tarjeta de pesada manual está en Peso (también cuando aún no hay pesadas, en vez de una página vacía); Actividad tiene tarjetas para la actividad del día (pasos, minutos de ejercicio, calorías activas) y para los entrenamientos; Sueño, una para cualquier noche; y Cuerpo → Corazón, una para el pulso en reposo, la VFC, la saturación de oxígeno y el VO2 máx. Los datos de tus fuentes para el mismo día mandan.
  - Cada campo muestra como referencia el último valor de la cuenta (vacío si no hay ninguno). En el móvil, al tocar un número se abre una rueda para deslizar el valor, con Teclado para escribirlo; sin un valor anterior, la rueda empieza en un valor típico para el sexo, la edad y la altura del perfil.
- **Ánimo:** se pueden registrar ánimos pasados, con fecha y hora o tocando el día en el calendario.
- **Historial** pasa a llamarse **Historial de pesos**.
- **Pantallas anchas:** la app llega a 1600 px, y Tu cuenta y Administración aprovechan el ancho con columnas.
- **Barra lateral:**
  - Tu cuenta, Administración (solo administradores) y Ayuda son secciones de la app, con la barra lateral.
  - «Gestionar perfiles» pasa a Tu cuenta.
  - **Ajustes** pasa a llamarse **Objetivos, plan y comidas**; su pestaña **Datos y copias** pasa a Tu cuenta.
- **Menú del avatar:** muestra el nombre completo e incluye Tu cuenta, Administración, Ayuda y **Cerrar sesión**, en rojo.
- **Línea de comandos de administración** (`python -m app.accounts.cli`): crear cuentas con contraseña temporal, invitaciones, contraseñas, usuarios, fuentes y mover perfiles.
- **Reloj de sueño (ampliado):** muestra solo la noche elegida, como un anillo grueso coloreado por fases (profundo, ligero, REM, despierto) cuando el reloj registra fases, con la media de las 14 noches anteriores como una barra gris por dentro, el horario objetivo de ese día (entre semana o fin de semana) discontinuo por fuera y el tiempo dormido más grande en el centro.
- **Móvil:** cada pestaña muestra un gráfico o un panel de cifras completo sin desplazarte: la explicación de cada tarjeta con gráfico espera tras una ⓘ junto a su título (toca el título), las tarjetas para apuntar datos a mano van al final de la pestaña, las tarjetas de cifras (también los récords y rachas de Actividad) tienen colores y minigráficos, y el avatar del perfil es más grande.
- **Tarjetas ampliadas:** deslizar el dedo a un lado en el móvil o la tableta, o las flechas de cada lado en el ordenador, pasa al día anterior o al siguiente.
- **Deslizar entre pestañas:** en pantallas táctiles, deslizar el dedo a un lado pasa a la pestaña siguiente o anterior del módulo (los apartados de Cuerpo cuentan como sus pestañas); después de la última pestaña pasa al módulo siguiente, y antes de la primera, a la última pestaña del anterior.
#### 🐛 Correcciones:
- **Seguridad:** el registro de accesos ya no guarda la dirección de subida de Apple Salud, los códigos OAuth ni las invitaciones.
- **Withings:** la dirección de retorno acepta las pruebas y los avisos de Withings (POST y HEAD).
- **Navegador:**
  - Las páginas y sus estilos se revalidan en cada despliegue, así que no quedan copias obsoletas en la caché.
  - Tu cuenta y Administración se pueden mostrar dentro de la app.
  - Las tarjetas ampliadas caben en la pantalla y su botón de cerrar sigue visible al desplazarte, también con el texto más grande en el móvil.
- **Calendarios de pesadas y de sueño en el móvil:** cada día muestra su cifra completa (por ejemplo 110,9) en vez de cortarla, y la tabla cabe en la pantalla, así que deslizar el dedo sobre ella cambia de pestaña.
- **Traducciones:** se traducen los textos que aún salían en español en los demás idiomas: las iniciales de los días de los calendarios y las de las comidas, las etiquetas del IMC y de los rangos, las fases del sueño y sus descripciones emergentes, los textos de los anillos y las leyendas de los gráficos, la lista de estados de ánimo (emociones y con qué se relacionan) y sus relaciones, cuentas como «21 de 30», el texto de ayuda de las notas y varias frases de los análisis. En español, las fechas conservan su «de» («viernes 20 de noviembre»).

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
