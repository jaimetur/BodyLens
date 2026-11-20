<!-- en: 3debc5cd0805d718 -->
# Cuentas y acceso

Cada persona tiene su propia cuenta de BodyLens, con sus datos separados de los de los demás. Entras con tu nombre de usuario (o tu correo) y tu contraseña.

## Entrar
- **Pantalla de acceso** (`/login`): tu usuario o el correo de tu cuenta, y tu contraseña. Si fallas varias veces seguidas, tendrás que esperar unos minutos.
- **Sesión**: dura 90 días en ese navegador. Para salir, ve a «Tu cuenta» → **Cerrar sesión** (esto también borra los datos guardados en ese navegador).
- **Cuenta inicial de un despliegue nuevo**: mientras la cuenta `admin` conserve su contraseña por defecto (`admin123`), la pantalla de acceso la muestra con un botón **Usar**. Desaparece en cuanto cambias la contraseña.

## Crear una cuenta con una suscripción
- En la pantalla de acceso (web y app de Android), la tarjeta **Crear mi cuenta** abre el registro; en la web, la página de inicio (`/`) muestra qué hace BodyLens y sus precios, y **Empezar gratis** también lo abre (`/alta`).
- **Planes**: 1,49 € al mes o 12 € al año (1 € al mes), los dos con **7 días de prueba gratis**. En la web se paga con tarjeta, Google Pay o Apple Pay (en la página segura de Stripe); en la app de Android, con Google Play.
- **Datos que se piden**: nombre y apellidos, correo, usuario y contraseña, un **código de invitación** si tienes uno, y aceptar las [condiciones](/terms) y la [política de privacidad](/privacy). La cuenta se crea en cuanto la página de pago confirma la suscripción, y entras con ella.
- **Código de invitación**: con un código válido la cuenta es **gratis** y se crea al momento, sin pagar, de por vida salvo que la administración le ponga una fecha de fin. Las mayúsculas, las tildes y los espacios no importan.
- Si una suscripción termina o un pago falla, la app te pide renovarla (`/alta`) y se te avisa por correo tres veces, con una semana de diferencia; siete días después del tercer aviso, la cuenta y sus datos se borran.

## Pedir una cuenta
- Ya no se piden cuentas: se crean con una suscripción o con un código de invitación. Las peticiones hechas antes siguen en Administración → Peticiones de acceso.

## Registrarte con una invitación
- Es un enlace `/registro?c=…` creado por la administración. Sirve para **una** cuenta y caduca a los pocos días.
- Pide los mismos datos que el registro con suscripción, pero la cuenta queda activa al momento.

## Primera entrada con una contraseña temporal
- Si tu cuenta se creó con una contraseña temporal, al entrar se te pide **tu propia contraseña** y puedes cambiar tu usuario y tu nombre. La app no se abre hasta que lo hagas.

## Tu cuenta (`/cuenta`)
Ábrela desde el menú del perfil (arriba a la izquierda) → **Tu cuenta**.
- **Nombre y apellidos** y **correo**: el correo recibe todas las notificaciones.
- **Idioma**: el idioma de toda la app y de los correos que recibes. Antes de entrar, elígelo con el selector 🌐 de la pantalla de acceso. Las cuentas nuevas empiezan en inglés (o en el idioma elegido al pedir la cuenta).
- **Tamaño del texto**: Pequeño, Normal, Grande o Muy grande, para toda la app.
- **Tema**: los colores de la app y de estas páginas. **Automático** sigue a tu dispositivo (claro de día y oscuro de noche si tu dispositivo lo hace); **Diurno** es siempre claro, **Nocturno** siempre oscuro, y además están **Sepia** (claro y cálido), **Océano** (azul profundo), **Bosque** (verde oscuro), **Alto contraste** (blanco y negro, para leer mejor), **Rosa**, **Lavanda** y **Menta** (claros y suaves), **Atardecer** (oscuro y cálido) y **Grafito** (gris oscuro neutro).
- **Bloquear perfiles con PIN tras**: los minutos sin actividad (1, 2, 5, 10, 15 o 30; 1 por defecto) tras los que un perfil con PIN se bloquea solo.
- **Contraseña**: pide la actual; al cambiarla se cierra tu sesión en los demás dispositivos.
- **Pareja** y **Sincronización**: mira [pareja](couples.md) y [sincronización](sync.md). Importar copias está en Tu cuenta → Datos y copias ([importar](import.md)).
- **Administración**: solo para cuentas de administrador; mira [administración](administration.md).
- **Suscripción** (cuentas con suscripción): el plan, hasta cuándo está activa y **Gestionar**: en la web, la página de Stripe para cambiar la tarjeta, descargar facturas o cancelar; en la app, las suscripciones de Google Play. Si se te ha avisado de un pago fallido, indica cuántos avisos llevas, con **Renovar**.
- **Privacidad y condiciones**: enlaces a la [política de privacidad](/privacy), las [condiciones de uso](/terms) y [cómo borrar una cuenta](/delete-account).
- **Borrar mi cuenta**: escribe tu contraseña y confirma. Tu cuenta y todos sus datos se borran al momento y se cancela cualquier suscripción. No se puede deshacer: descarga antes una copia en Datos y copias si quieres conservar tus datos.

## Privacidad
- La [política de privacidad](/privacy) explica con detalle qué se guarda y por qué.
- Solo tú puedes ver tus datos. Los datos del **ciclo** y de intimidad los ve también tu pareja si habéis unido vuestras cuentas.
- Las contraseñas se guardan cifradas (argon2); nadie puede leerlas.
