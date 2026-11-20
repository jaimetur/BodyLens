<!-- en: 143dddf469bf479f -->
# Administración

Solo para cuentas de administrador. Está en «Tu cuenta» → **Administración**.

## Usuarios
- Todas las cuentas del servidor. El **interruptor** de cada fila activa o desactiva la cuenta (una cuenta desactivada no puede entrar, pero conserva sus datos). No puedes desactivar la tuya.
- Junto a cada nombre, cómo se creó la cuenta: el **código de invitación** que usó (o «Gratis por administración») con el final de su tiempo gratis, o su **suscripción**: en la web (mensual o anual, y cómo se paga: marca y últimas cifras de la tarjeta, Google Pay o Apple Pay) o en Google Play (mensual o anual).
- **Editar**: usuario, nombre y apellidos, correo y, si quieres, una contraseña nueva (escrita dos veces; vacío = sin cambios). Al cambiar la contraseña se cierran las sesiones abiertas de esa cuenta.
- **Restablecer contraseña**: pone una temporal, se la envía por correo a la persona y le pide que la cambie al entrar.
- **Hacer admin / Quitar admin** y **Borrar** (borra la cuenta y todos sus datos).

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
- En la pestaña Invitaciones, **Códigos de invitación**: cada código con su **duración**: 1 mes, 3 meses, 6 meses, 1 año, de por vida o hasta una fecha que elijas. `INVITACION_AMIGOS`, de por vida, por defecto. Quien se registra con uno tiene una cuenta gratis, sin pagar, durante ese tiempo contado desde el día del alta, o hasta esa fecha (hasta el final del último día); después puedes cambiarle la fecha de fin en Usuarios → Editar. Un código puede tener además una **fecha de caducidad** y un **máximo de cuentas** (los dos opcionales; por ejemplo, las 100 primeras para una promoción): se puede usar hasta el final de ese día o hasta que lo hayan usado esas cuentas; después se borra y ya no vale, pero las cuentas que ya se crearon con él conservan su tiempo gratis. Debajo del máximo se ve cuántas plazas quedan. **Anunciar en la web** muestra el código en la página principal como promoción, con su tiempo gratis y un contador de las plazas que quedan. Un código puede tener **alias**, en su campo **Alias**, separados por comas (por ejemplo, `LAUNCH` para `LANZAMIENTO`): otros nombres del mismo código que comparten su duración, sus fechas y sus plazas; la página principal en inglés muestra el primer alias. Las mayúsculas, las tildes y los espacios no importan. **Añadir código** añade una fila, **Quitar** la elimina y **Guardar** guarda la lista.
- **Usuarios → Editar → Acceso gratuito**: ninguno, **De por vida** o **Hasta una fecha** (el final de ese día). Cuando termina, la cuenta se trata como una suscripción sin pagar: solo puede renovar, descargar sus datos o borrarse, recibe tres avisos con una semana de diferencia y se borra siete días después del tercero. La lista muestra el acceso gratuito y la suscripción de cada cuenta.

## Correo
- El correo se envía desde el buzón configurado en el servidor (variables `SMTP_*`). **Enviarme un correo de prueba** comprueba que funciona.

## Datos legales
- El responsable de los datos (tu nombre o tu marca), un correo de contacto para privacidad y, si quieres, una dirección postal. Aparecen al principio de las páginas públicas [política de privacidad](/privacy), [condiciones de uso](/terms) y [borrar una cuenta](/delete-account), que Google Play pide para publicar la app.

## Google Play
- Para las cuentas que pagan con una suscripción en la app de Android. Pega la **clave JSON de una cuenta de servicio** con acceso a la Play Console; el servidor la usa para comprobar cada compra con Google y para cancelar la suscripción de una cuenta que se borra. El paquete (`app.bodylens.android`) y el ID de la suscripción (`bodylens`) vienen rellenados.
- Mientras no esté configurado, la app no ofrece suscribirse.

## Pagos web (Stripe)
- Para las cuentas que pagan en la web (tarjeta, Google Pay, Apple Pay), a 1,50 € al mes o 12 € al año con 7 días de prueba gratis.
- Pega tu **clave secreta** de Stripe: el servidor crea en Stripe el producto de BodyLens y sus dos precios si aún no existen. Después crea un webhook en Stripe (Developers → Webhooks) con la dirección que se muestra aquí y los eventos `checkout.session.completed` y `customer.subscription.*`, y pega su **secreto de firma**.
- Una clave de prueba (`sk_test_…`) permite probarlo todo con las tarjetas de prueba de Stripe; cambia a la clave real para cobrar de verdad.
- Las cuentas que dejan de pagar reciben tres correos, con una semana de diferencia, y se borran siete días después del tercero; las cuentas de administrador nunca se borran así.

## Cuenta `admin` por defecto
- Cada despliegue nuevo crea una vez la cuenta `admin`, con la contraseña `admin123`, que aparece en la pantalla de acceso hasta que se cambia. **Cámbiala** nada más desplegar; si la borras, no se vuelve a crear.

## Desde la consola
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
