# Administración

Solo para cuentas administradoras. Está en «Tu cuenta» → **Administración**.

## Usuarios
- Todas las cuentas del servidor. El **interruptor** de cada fila activa o desactiva la cuenta (una desactivada no puede entrar, pero sus datos se conservan). La tuya no se puede desactivar.
- **Editar**: usuario, nombre y apellidos, correo y, si quieres, una contraseña nueva (escrita dos veces; vacía = no se cambia). Al cambiar la contraseña se cierran las sesiones abiertas de esa cuenta.
- **Restablecer contraseña**: pone una provisional, se la envía por correo y le pide cambiarla al entrar.
- **Hacer/Quitar admin** y **Borrar** (borra la cuenta y todos sus datos).

## Peticiones de acceso
- Lista de cuentas pedidas desde la pantalla de entrar, con nombre, usuario, correo, fecha y mensaje.
- **Aprobar**: la cuenta se activa y la persona recibe un correo con el enlace para entrar.
- **Rechazar**: la petición se borra y la persona recibe un correo.
- Cada petición nueva llega por correo a las cuentas administradoras que tengan correo.

## Invitaciones
- **Crear invitación**: genera un enlace de registro de un solo uso (opcional: una nota para saber a quién va). El enlace solo se muestra una vez: cópialo.
- La lista muestra si cada invitación está pendiente, usada (y por quién) o caducada.

## Cuentas y fuentes (fase 1)
- Para cada cuenta: **ID de la hoja de Google** (compartida como lector con la cuenta de servicio del servidor) y **URL del Apps Script** (`https://script.google.com/…/exec`).
- Solo la administración puede cambiarlas, para que nadie pueda leer la hoja de otra persona.

## Correo
- El correo sale del buzón configurado en el servidor (variables `SMTP_*`). **Enviarme un correo de prueba** comprueba que funciona.

## Cuenta `admin` por defecto
- Todo despliegue nuevo crea una vez la cuenta `admin` con la contraseña `admin123`, que aparece en la pantalla de entrar mientras no se cambie. **Cámbiala** nada más desplegar; si la borras, no vuelve a crearse.

## Por consola
```
docker exec -it bodylens python -m app.accounts.cli usuarios
docker exec -it bodylens python -m app.accounts.cli contrasena <usuario>
docker exec -it bodylens python -m app.accounts.cli invitacion [nota]
docker exec -it bodylens python -m app.accounts.cli fuentes <usuario> --hoja <ID> --apps-script <URL>
```
