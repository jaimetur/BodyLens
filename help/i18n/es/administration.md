<!-- en: 3afc480b4fb92deb -->
# Administración

Solo para cuentas de administrador. Está en «Tu cuenta» → **Administración**.

## Usuarios
- Todas las cuentas del servidor. El **interruptor** de cada fila activa o desactiva la cuenta (una cuenta desactivada no puede entrar, pero conserva sus datos). No puedes desactivar la tuya.
- **Editar**: usuario, nombre y apellidos, correo y, si quieres, una contraseña nueva (escrita dos veces; vacío = sin cambios). Al cambiar la contraseña se cierran las sesiones abiertas de esa cuenta.
- **Restablecer contraseña**: pone una temporal, se la envía por correo a la persona y le pide que la cambie al entrar.
- **Hacer admin / Quitar admin** y **Borrar** (borra la cuenta y todos sus datos).

## Peticiones de acceso
- Lista de las cuentas pedidas desde la pantalla de acceso, con nombre, usuario, correo, fecha y mensaje.
- **Aprobar**: la cuenta se activa y la persona recibe un correo con el enlace para entrar.
- **Rechazar**: la petición se borra y la persona recibe un correo.
- Cada petición nueva se envía por correo a las cuentas de administrador que tengan correo.

## Invitaciones
- **Crear invitación**: genera un enlace de registro de un solo uso (opcional: una nota para recordar a quién va dirigido). El enlace se muestra una sola vez: cópialo.
- La lista indica si cada invitación está pendiente, usada (y por quién) o caducada.

## Cuentas y fuentes (fase 1)
- Para cada cuenta: **ID de la hoja de Google** (compartida como lector con la cuenta de servicio del servidor) y **URL del Apps Script** (`https://script.google.com/…/exec`).
- Solo la administración puede cambiarlas, para que nadie pueda leer la hoja de otra persona.

## Correo
- El correo se envía desde el buzón configurado en el servidor (variables `SMTP_*`). **Enviarme un correo de prueba** comprueba que funciona.

## Cuenta `admin` por defecto
- Cada despliegue nuevo crea una vez la cuenta `admin`, con la contraseña `admin123`, que aparece en la pantalla de acceso hasta que se cambia. **Cámbiala** nada más desplegar; si la borras, no se vuelve a crear.

## Desde la consola
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
