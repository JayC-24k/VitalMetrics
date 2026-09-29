# VitalMetrics con XAMPP (Apache + MySQL)

La aplicación usa Flask para las rutas de Python. En Windows, Waitress ejecuta Flask en `127.0.0.1:5001` y el Apache de XAMPP publica el sitio en el puerto 80 mediante un proxy inverso. La base de datos se sirve desde el MySQL/MariaDB de XAMPP.

## 1. Crear la base de datos

Inicia **MySQL** desde el panel de control de XAMPP. En phpMyAdmin, ejecuta:

```sql
CREATE DATABASE vitalmetrics
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Las tablas `users` y `evaluations` se crean al iniciar la aplicación. Usa un usuario MySQL con permisos sobre esta base. El usuario `root` sin contraseña es el valor inicial habitual de una instalación local de XAMPP; si tu instalación tiene contraseña, configúrala en `.env`.

## 2. Configurar la aplicación

En PowerShell, desde la carpeta del proyecto, crea `.env` desde el ejemplo solo si aún no tienes uno:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edita `.env` y establece `DB_ENGINE=mysql`, `MYSQL_USER`, `MYSQL_PASSWORD` y `SECRET_KEY`. Si ya tienes `.env`, agrega o ajusta esas variables sin reemplazar el archivo. Conserva las variables de servicios que ya uses. No subas `.env` a Git.

La base SQLite existente (`usuarios.db`) se conserva intacta; activar MySQL empieza a usar las tablas de `vitalmetrics` y no copia registros anteriores automáticamente.

Instala dependencias en el entorno Python del proyecto:

```powershell
python -m pip install -r requirements.txt
```

## 3. Conectar Apache con Flask

En `C:\xampp\apache\conf\httpd.conf`, habilita estos módulos quitando `#` al inicio si están comentados:

```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
```

Incluye el archivo de este proyecto desde `httpd.conf` (ajusta la ruta si guardaste el repositorio en otro lugar):

```apache
Include "C:/Users/linet/OneDrive/Desktop/Vitalmetrics/xampp/vitalmetrics-vhost.conf"
```

El archivo incluido configura Apache para reenviar `/vitalmetrics/` al servidor Flask local, y deja el resto de XAMPP, incluido phpMyAdmin, en sus rutas habituales. `mod_headers` ya está habilitado en esta instalación. No actives `ProxyRequests`; Apache queda configurado como proxy inverso.

## 4. Iniciar servicios

1. Inicia **MySQL** y **Apache** desde el panel de XAMPP.
2. En otra terminal PowerShell, activa el entorno virtual y ejecuta `python run_waitress.py` desde la carpeta del proyecto.
3. Abre `http://localhost/vitalmetrics/`.

Waitress debe permanecer ejecutándose para que Apache pueda servir la aplicación. Para la primera ejecución, Flask creará las tablas y el usuario administrador inicial configurado por `ADMIN_USERNAME`, `ADMIN_PASSWORD` y `ADMIN_EMAIL` (o los valores predeterminados del proyecto).

## Autenticaci?n PHP

El login y el registro usan `login.php`, `validar_login.php`, `registrar.php` y `logout.php` desde Apache, conectados a la misma base MySQL definida en `.env`. Apache excluye esos cuatro archivos del proxy Flask; las dem?s rutas contin?an en Waitress. El primer uso crea ?nicamente la tabla auxiliar `php_login_tickets` para pasar el inicio de sesi?n a Flask. Las tablas `users` y `evaluations` se conservan. Las claves nuevas usan el mismo formato PBKDF2 que Python, por lo que los usuarios existentes pueden seguir iniciando sesi?n.

Si Apache no inicia, revisa `C:\xampp\apache\logs\error.log`; si Waitress no se conecta a MySQL, confirma el servicio, puerto, base de datos y credenciales de `.env`.
