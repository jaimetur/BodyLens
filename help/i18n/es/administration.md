<!-- en: 25cb698c648819f0 -->
# Administración

Solo para cuentas de administrador. Está en «Tu cuenta» → **Administración**.

## Usuarios
- Todas las cuentas del servidor. El **interruptor** de cada fila activa o desactiva la cuenta (una cuenta desactivada no puede entrar, pero conserva sus datos). No puedes desactivar la tuya.
- Junto a cada nombre, cómo se creó la cuenta: el **código de invitación** que usó (o «Gratis por administración») con el final de su tiempo gratis, o su **suscripción**: en la web (mensual o anual, y cómo se paga: marca y últimas cifras de la tarjeta, Google Pay o Apple Pay) o en Google Play (mensual o anual).
- **Editar**: usuario, nombre y apellidos, correo y, si quieres, una contraseña nueva (escrita dos veces; vacío = sin cambios). Al cambiar la contraseña se cierran las sesiones abiertas de esa cuenta.
- **Restablecer contraseña**: pone una temporal, se la envía por correo a la persona y le pide que la cambie al entrar.
- **Hacer admin / Quitar admin** y **Borrar** (borra la cuenta y todos sus datos).

## Negocio
Las cifras del servicio y, debajo, su configuración (pagos, suscripciones, claves de API, correo y datos legales), que antes tenía sus propias pestañas.

- **Periodo**: 7 días, 30 días, 12 meses o desde el principio. **Actualizar** vuelve a preguntar a Stripe y a Google Play (si no, sus cifras se guardan unos minutos). Cada recuadro dice de dónde salen sus cifras y cuándo se tomaron; un servicio sin configurar dice **Sin configurar** y enlaza a su ajuste, y uno que falla muestra su error sin afectar al resto.
- **Usuarios**: cuentas y parejas, altas del periodo (con un gráfico por día o por mes) y cuentas activas en los últimos 7 y 30 días (contadas desde que se instaló esta versión).
- **Suscripciones**: de pago, en prueba, canceladas o caducadas y en solo lectura; por plan (mensual o anual) y por canal (web o Google Play); acceso gratis (de por vida o dado por la administración); códigos de invitación usados y plazas que quedan de la oferta de lanzamiento. Google Play no dice si una suscripción está en la prueba, así que cuenta como de pago.
- **Ingresos**: el ingreso recurrente mensual con los precios de tarifa (los planes anuales cuentan ÷ 12), por canal. De **Stripe**: lo cobrado y devuelto en el periodo, los ingresos netos por mes, las pruebas que pasaron a pago y las bajas. De **Google Play**: sus informes mensuales de ingresos (ya sin la comisión de Google), que Google publica hacia el día 5 del mes siguiente.
- **Descargas**: las descargas de los APK de BodyLens y BodyLens Bridge desde este servidor y, de los informes de estadísticas de Google Play, las instalaciones, los usuarios que la han instalado y los dispositivos con la app (Google los publica con unos días de retraso).
- **Versiones en Google Play**: la versión de cada canal (prueba interna, prueba cerrada, producción).
- **Salud**: la última copia de seguridad, si el correo saliente está configurado y el espacio libre en disco.
- Las claves guardadas se conservan cifradas en el servidor y nunca se muestran enteras: solo que están configuradas y sus últimos caracteres.

### Pagos · Stripe
- Para las cuentas que pagan en la web (tarjeta, Google Pay, Apple Pay), a 1,50 € al mes o 12 € al año con 7 días de prueba gratis.
- Pega tu **clave secreta** de Stripe: el servidor crea en Stripe el producto de BodyLens y sus dos precios si aún no existen. Después crea un webhook en Stripe (Developers → Webhooks) con la dirección que se muestra aquí y los eventos `checkout.session.completed` y `customer.subscription.*`, y pega su **secreto de firma**. **Probar conexión** comprueba la clave.
- Una clave de prueba (`sk_test_…`) permite probarlo todo con las tarjetas de prueba de Stripe; cambia a la clave real para cobrar de verdad.
- Las cuentas que dejan de pagar reciben tres correos, con una semana de diferencia, y se borran siete días después del tercero; las cuentas de administrador nunca se borran así.

### Google Play
- Para las cuentas que pagan con una suscripción en la app de Android. Pega la **clave JSON de una cuenta de servicio** con acceso a la Play Console; el servidor la usa para comprobar cada compra con Google y para cancelar la suscripción de una cuenta que se borra. El paquete (`app.bodylens.android`) y el ID de la suscripción (`bodylens`) vienen rellenados. Mientras no esté configurado, la app no ofrece suscribirse. **Probar conexión** comprueba que Google deja a la cuenta de servicio acceder a la app.
- **Bucket de informes de Google Play**: las descargas y los ingresos de Google Play salen de los informes que Google deja cada mes en un bucket de Google Cloud Storage. En Play Console, ve a «Gestionar cuenta > Informes de aplicaciones de Play», elige «Estadísticas», pulsa «Copiar URI de Cloud Storage» junto al encabezado de la sección y pégalo aquí (empieza por `pubsite_prod_rev`). La cuenta de servicio necesita, para toda la cuenta, permiso para ver la información de las aplicaciones y para ver los datos financieros. **Probar los informes** comprueba que puede leerlos.

### Suscripciones
- BodyLens tiene una sola suscripción, con un plan mensual y otro anual y una prueba gratis. Los planes y precios de la web los crea el servidor en Stripe; los de Google Play son los de la suscripción `bodylens` en Play Console. El acceso gratis se da en Usuarios → Editar, y los códigos de promoción y la oferta de lanzamiento están en Invitaciones.

### Withings
- BodyLens se conecta a Withings con una aplicación de desarrollador gratuita, que se crea una sola vez en developer.withings.com (una aplicación de la API pública), con la **dirección de retorno (callback URL)** que muestra este bloque.
- Withings da entonces dos datos: el **Client ID**, que identifica a la aplicación, y el **Client secret**, su contraseña (no lo compartas). Cópialos aquí y pulsa **Guardar**; después, cada cuenta conecta su báscula en Tu cuenta → Fuentes de datos.

### Traductor
- La ayuda, el README y el registro de cambios se traducen solos al idioma de cada cuenta con LibreTranslate, que funciona en este servidor; si quieres, se usa una clave de la API de Anthropic cuando LibreTranslate no está disponible.

### Correo
- El correo se envía desde el buzón configurado aquí o en el servidor (variables `SMTP_*`). **Enviarme un correo de prueba** comprueba que funciona.

### Datos legales
- El responsable de los datos (tu nombre o tu marca), un correo de contacto para privacidad y, si quieres, una dirección postal. Aparecen al principio de las páginas públicas [política de privacidad](/privacy), [condiciones de uso](/terms) y [borrar una cuenta](/delete-account), que Google Play pide para publicar la app.

## Copias
Copias de seguridad de la base de datos y de los archivos de las cuentas, a mano o programadas, en ZIP dentro de una carpeta de la carpeta de datos del servidor (no de tu ordenador).

- **Cifras**: copias guardadas (completas y ligeras) y su tamaño, espacio libre en el disco (en rojo cuando queda poco), la última copia correcta y la próxima, y si será completa o ligera.
- **Hacer copia ahora**: elige el contenido (la **base de datos** y los **archivos de las cuentas**: el libro de cada cuenta y las hojas importadas) y la carpeta; los dos se guardan para las próximas copias, también las programadas. El botón pregunta si es **completa** (base de datos y archivos) o **ligera** (solo la base de datos).
- **Restaurar**: elige una carpeta, el tipo y la copia, y después las partes que se restauran. Antes de restaurar se hace sola una copia ligera de la base de datos actual, para poder deshacerlo; la programación de copias y las sesiones abiertas de este servidor se conservan. **Descargar** guarda una copia fuera del servidor; **Borrar** quita una.
- **Copias programadas**: activadas o no; frecuencia (cada hora, cada 4 horas, diaria, semanal o mensual), día de la semana o del mes, hora (Madrid); copias ligeras entre las completas, con el día de la completa. Por defecto: diaria a las 03:30, ligera de lunes a sábado y completa el domingo.
- **Retención**, solo de las copias programadas: todas las de los últimos 15 días y, de las completas, la más reciente, una por semana durante 12 semanas y una por mes durante 120 meses (todo se puede cambiar). Las copias hechas a mano, antes de restaurar o por versiones anteriores nunca se borran.
- Las claves del servidor (`secrets`) nunca entran en una copia, ni lo que el servidor vuelve a crear solo (las apps de Android, los medios de la página de inicio y las traducciones de la ayuda). Las copias diarias de la base de datos de versiones anteriores aparecen como copias ligeras «de una versión anterior».

## Peticiones de acceso
- Peticiones hechas antes de que las cuentas se crearan con una suscripción o un código de invitación (ya no llegan nuevas).
- Lista de las cuentas pedidas desde la pantalla de acceso, con nombre, usuario, correo, fecha y mensaje.
- **Aprobar**: la cuenta se activa y la persona recibe un correo con el enlace para entrar.
- **Rechazar**: la petición se borra y la persona recibe un correo.
- Cada petición nueva se envía por correo a las cuentas de administrador que tengan correo.

## Invitaciones
- **Crear invitación**: genera un enlace de registro de un solo uso (opcional: una nota para recordar a quién va dirigido). El enlace se muestra una sola vez: cópialo.
- La lista indica si cada invitación está pendiente, usada (y por quién) o caducada.

## Códigos de invitación
- En la pestaña Invitaciones, **Códigos de invitación**: cada código con su **duración**: 1 mes, 3 meses, 6 meses, 1 año, de por vida o hasta una fecha que elijas. `INVITACION_AMIGOS`, de por vida, por defecto. Quien se registra con uno tiene una cuenta gratis, sin pagar, durante ese tiempo contado desde el día del alta, o hasta esa fecha (hasta el final del último día); después puedes cambiarle la fecha de fin en Usuarios → Editar. Un código puede tener además una **fecha de caducidad** y un **máximo de cuentas** (los dos opcionales; por ejemplo, las 100 primeras para una promoción): se puede usar hasta el final de ese día o hasta que lo hayan usado esas cuentas; después se borra y ya no vale, pero las cuentas que ya se crearon con él conservan su tiempo gratis. Debajo del máximo se ve cuántas plazas quedan. **Anunciar en la web** muestra el código en la página principal como promoción, con su tiempo gratis y un contador de las plazas que quedan. Un código puede tener **alias**, en su campo **Alias**, separados por comas (por ejemplo, `LAUNCH` para `LANZAMIENTO`): otros nombres del mismo código que comparten su duración, sus fechas y sus plazas; la página principal muestra el primer alias en todos los idiomas menos en español. Las mayúsculas, las tildes y los espacios no importan. **Añadir código** añade una fila, **Quitar** la elimina y **Guardar** guarda la lista.
- **Usuarios → Editar → Acceso gratuito**: ninguno, **De por vida** o **Hasta una fecha** (el final de ese día). Cuando termina, la cuenta se trata como una suscripción sin pagar: solo puede renovar, descargar sus datos o borrarse, recibe tres avisos con una semana de diferencia y se borra siete días después del tercero. La lista muestra el acceso gratuito y la suscripción de cada cuenta.

## Cuenta `admin` por defecto
- Cada despliegue nuevo crea una vez la cuenta `admin`, con la contraseña `admin123`, que aparece en la pantalla de acceso hasta que se cambia. **Cámbiala** nada más desplegar; si la borras, no se vuelve a crear.

## Desde la consola
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
