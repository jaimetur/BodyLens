<!-- en: ba545567cd87b696 -->
# Administración

Solo para cuentas de administrador. Está en «Tu cuenta» → **Administración**.

## Usuarios
- Todas las cuentas del servidor. El **interruptor** de cada fila activa o desactiva la cuenta (una cuenta desactivada no puede entrar, pero conserva sus datos). No puedes desactivar la tuya.
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
- En la pestaña Invitaciones, **Códigos de invitación**: uno por línea (`INVITACION_AMIGOS` por defecto). Quien se registra con uno tiene una cuenta gratis de por vida, sin pagar; las mayúsculas, las tildes y los espacios no importan.
- **Usuarios → Editar → Acceso gratuito**: ninguno, **De por vida** o **Hasta una fecha** (el final de ese día). Cuando termina, la cuenta se trata como una suscripción sin pagar: solo puede renovar, descargar sus datos o borrarse, recibe tres avisos con una semana de diferencia y se borra siete días después del tercero. La lista muestra el acceso gratuito y la suscripción de cada cuenta.

## Correo
- El correo se envía desde el buzón configurado en el servidor (variables `SMTP_*`). **Enviarme un correo de prueba** comprueba que funciona.

## Datos legales
- El responsable de los datos (tu nombre o tu marca), un correo de contacto para privacidad y, si quieres, una dirección postal. Aparecen al principio de las páginas públicas [política de privacidad](/privacy), [condiciones de uso](/terms) y [borrar una cuenta](/delete-account), que Google Play pide para publicar la app.

## Google Play
- Para las cuentas que pagan con una suscripción en la app de Android. Pega la **clave JSON de una cuenta de servicio** con acceso a la Play Console; el servidor la usa para comprobar cada compra con Google y para cancelar la suscripción de una cuenta que se borra. El paquete (`app.bodylens.android`) y el ID de la suscripción (`bodylens`) vienen rellenados.
- Mientras no esté configurado, la app no ofrece suscribirse.

## Pagos web (Stripe)
- Para las cuentas que pagan en la web (tarjeta, Google Pay, Apple Pay), a 1,49 € al mes o 12 € al año con 7 días de prueba gratis.
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
