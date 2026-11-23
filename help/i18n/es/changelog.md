<!-- en: 12736b8e2232a1c8 -->
# 🗓️ CHANGELOG
[Registro de cambios](/CHANGELOG.md) de las versiones anteriores

---

## Release: v0.1.0
### Release Date: 2026-11-19
#### ⚠️ Cambios incompatibles:
- **De un artefacto de claude.ai a un servidor propio:** BodyLens ya no vive en claude.ai y pasa a un contenedor Docker en el NAS (`https://bodylens.jtgcloud.com`). Los datos están en una base de datos SQLite del servidor, no en el espacio de datos del artefacto. Entras con un usuario y una contraseña de BodyLens, no con tu cuenta de Claude.
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
  - Al entrar, la app se une sola a la cuenta y abre su pantalla de Health Connect: te lleva a Google Play si falta Health Connect o está desactualizado y pide los permisos (otra vez al volver de instalarlo), lectura en segundo plano incluida, y después el permiso de Android para funcionar en segundo plano sin límites de batería; te lo recuerda como mucho una vez por semana mientras falte algo, y la pantalla muestra las dos cosas con un botón para lo que falte y tiene un botón **Cerrar**. Tu cuenta → Fuentes de datos muestra el estado de Health Connect con **Enviar ahora**, **Permisos de Health Connect** y **Cambiar el servidor**.
  - **Fuente de salud que manda** en cada cuenta (Tu cuenta → Fuentes de datos): si a una cuenta le llegan datos de Apple Salud y de Android, la que manda tiene prioridad y la otra solo rellena los días y tipos de datos que le falten, sin sumar ni duplicar nada. **Automática** por defecto (Android, salvo que la mayoría de los datos lleguen de Apple Salud), **Apple Salud** o **Android**. El recuadro indica si los datos llegan de Apple Salud, de Android o de los dos, con el último envío de cada uno y cuántos datos no se han usado.
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
- **Gráficas de sueño, reorganizadas y más claras:** cada pestaña trata un tema (Noche, Saldo, Evolución, Horario, Análisis) y Saldo muestra el plan para saldar la deuda en tarjetas y noche a noche en barras verdes y rojas con la lista plegada; Tendencia y A qué hora duermes siguen el periodo elegido, por semanas (por meses a partir de 6 meses); Entre semana y fin de semana usa puntos sobre una misma escala; Calidad es una barra por noche (por semana a partir de 1 mes) repartida por fases; el calendario del Histórico pasa a mapa de calor con más de 6 semanas; los medidores de bienestar muestran dos cifras cada uno y el resto en Más.
- **Menú del perfil:** destaca sobre la página, con un fondo más claro, un borde de color y el resto de la pantalla oscurecido mientras está abierto.
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
- **Móvil:** cada pestaña muestra un gráfico o un panel de cifras completo sin desplazarte: la explicación de cada tarjeta con gráfico (y de las tarjetas de Tu cuenta, Administración y Objetivos, plan y comidas) espera tras una ⓘ junto a su título (toca el título), las tarjetas para apuntar datos a mano van al final de la pestaña, todas las tarjetas de cifras tienen color y, cuando hay datos, un minigráfico o una barra de progreso (Peso, Actividad, Sueño…), y el avatar del perfil es más grande.
- **Tarjetas ampliadas:** deslizar el dedo a un lado en el móvil o la tableta, o las flechas de cada lado en el ordenador, pasa al día anterior o al siguiente.
- **Deslizar entre pestañas:** en pantallas táctiles, deslizar el dedo a un lado pasa a la pestaña siguiente o anterior del módulo (los apartados de Cuerpo cuentan como sus pestañas); después de la última pestaña pasa al módulo siguiente, y antes de la primera, a la última pestaña del anterior.
- **Sin zoom en el móvil:** la app y sus páginas (acceso, Tu cuenta, Administración, Ayuda) ya no se amplían al pellizcar, al tocar dos veces seguidas (también en el teclado del PIN) ni al entrar en un campo; si un navegador la amplía igualmente (Brave, por ejemplo), vuelve a su tamaño normal y se puede reducir pellizcando.
- **Las pestañas empiezan por la primera tras el bloqueo:** cuando sale el bloqueo con PIN (al volver a abrir la app, tras el tiempo de inactividad o al bloquear el perfil), cada módulo vuelve a abrirse en su primera pestaña; se mantiene el módulo en el que estabas.
- **Pantalla del PIN:** cabe en la pantalla sin barras de desplazamiento (las teclas son más grandes y están más separadas, crecen con el espacio libre y solo se reducen en pantallas muy bajas) y tiene **Entrar con otro usuario**, que cierra la sesión y vuelve a la pantalla de acceso.
- **Ayuda, Tu cuenta y Administración dentro de la app se desplazan como una sola página:** en el móvil la página que se ve dentro de la app ya no se desplaza por su cuenta, así que al deslizar siempre se mueve el contenido.
- **Navegación más fácil en el móvil:** la barra de abajo muestra los 4 módulos que más usas (o los que elijas en **Editar la barra**, quitando con − y añadiendo con +) y **Más**, un menú con todos los módulos, cuya flecha despliega sus pestañas para ir directamente a una, que se cierra al volver a tocar **Más**, con su botón ✕ o deslizándolo hacia abajo; las pestañas de cada módulo, con sus iconos, están abajo, en una franja justo encima de la barra de abajo, teñida del color del módulo para distinguirlas (también en Tu cuenta, en verde, y Administración, en rojo, cuyas pestañas también se recorren deslizando); al bajar por la página, una barra fina arriba mantiene el nombre del módulo (y las pestañas de Administración, ahora en una sola fila que se desliza, con iconos y la pestaña actual resaltada en color); el periodo muestra solo el que está en uso y se abre con un toque; unos puntos indican dónde estás al cambiar de pestaña, y la primera vez un aviso explica que se puede deslizar a los lados. Los botones de cerrar y las flechas de los paneles son más grandes y se ven mejor, y el de cerrar es rojo anaranjado y está alineado con las flechas.
- **Los campos de datos a mano ya no se abren sin querer en el móvil:** la rueda para elegir el valor solo se abre con un toque deliberado, no al rozar un campo mientras desplazas, al deslizar el dedo sobre él ni al tocarlo con la página aún en movimiento.
- **Los paneles se cierran deslizando hacia abajo en el móvil:** el detalle de una tarjeta, los diálogos de Comidas y Exportar a PDF se cierran al deslizarlos hacia abajo desde arriba, como el menú **Más**.
- **Apuntar el ánimo como en la app Salud:** tras la cara, la app pregunta qué emociones lo describen mejor (sugeridas según lo agradable que sea) y qué está influyendo más, las dos cosas opcionales, y si es un momento o el ánimo de todo el día.
- **Novedades y Acerca de BodyLens en los menús:** junto a Ayuda al final de **Más**, y en el menú del perfil. **Acerca de BodyLens** es un panel con el nombre, la versión, su fecha, el autor y enlaces a la documentación; Tu cuenta y Administración muestran sus iconos en verde y rojo en **Más**.

#### 🐛 Correcciones:
- **Seguridad:** el registro de accesos ya no guarda la dirección de subida de Apple Salud, los códigos OAuth ni las invitaciones.
- **Withings:** la dirección de retorno acepta las pruebas y los avisos de Withings (POST y HEAD).
- **Navegador:**
- **Barras de abajo en el iPhone:** al cambiar de pestaña o de sección se suelta el campo de texto que queda oculto, para que Safari no se quede con la pantalla encogida del teclado y las barras de abajo sigan en su sitio.
  - Las páginas y sus estilos se revalidan en cada despliegue, así que no quedan copias obsoletas en la caché.
  - Tu cuenta y Administración se pueden mostrar dentro de la app.
  - Las tarjetas ampliadas caben en la pantalla y su botón de cerrar sigue visible al desplazarte, también con el texto más grande en el móvil.
- **Calendarios de pesadas y de sueño en el móvil:** cada día muestra su cifra completa (por ejemplo 110,9) en vez de cortarla, y la tabla cabe en la pantalla, así que deslizar el dedo sobre ella cambia de pestaña. Las horas habituales de la gráfica de Horario (Auto, Semana, Mes, Trimestre, Año) usan todas las noches de cada ventana, así que cambian con la ventana aunque el periodo mostrado sea una semana. En el histórico de sueño, las barras de cada día ya no tapan su fecha, las cifras de la leyenda se leen con normalidad y la clave de la media semanal es una línea discontinua, y una semana nueva sin ninguna noche todavía no añade una fila vacía.
- **Traducciones:** se traducen los textos que aún salían en español en los demás idiomas: las iniciales de los días de los calendarios y las de las comidas, las etiquetas del IMC y de los rangos, las fases del sueño y sus descripciones emergentes, los textos de los anillos y las leyendas de los gráficos, la lista de estados de ánimo (emociones y con qué se relacionan) y sus relaciones, cuentas como «21 de 30», el texto de ayuda de las notas y varias frases de los análisis. En español, las fechas conservan su «de» («viernes 20 de noviembre»).
- **Administración en el móvil:** los botones de cada usuario (Editar, Hacer admin, Restablecer contraseña…) pasan a la línea siguiente en vez de salirse de la pantalla.
- **Tu cuenta, Administración y Ayuda en modo oscuro en el iPhone:** las páginas que se muestran dentro de la app siguen el tema de la app en vez de verse claras.
- **Deslizar sobre campos en el móvil:** un deslizamiento a un lado que empieza sobre un campo (Tu cuenta, Administración y todos los módulos) también cambia de pestaña, salvo si estás escribiendo en él.
- **Gráficas de ánimo en el móvil:** «Por día de la semana» ocupa todo el ancho, con barras hacia arriba (verde) o hacia abajo (rojo) desde la línea de cero, y las cifras de «Tus días difíciles» van en una rejilla ordenada, teñidas de verde o rojo.

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
