# dbReader

**Universal Database Reader** es una aplicación web para explorar bases de datos SQLite desde una interfaz centralizada. Permite descubrir bases de datos disponibles, consultar su estructura, revisar estadísticas y visualizar registros sin necesidad de utilizar directamente herramientas de línea de comandos.

La aplicación está desarrollada con Python, FastAPI y una interfaz web basada en HTML, CSS y JavaScript. Docker Compose permite ejecutarla de forma reproducible y conservar los archivos de bases de datos entre reinicios.

## Características

- **Descubrimiento de bases de datos:** inventario de los archivos SQLite disponibles.
- **Gestión de archivos:** incorporación de bases de datos mediante la interfaz web.
- **Exploración del esquema:** consulta de tablas, vistas, columnas, índices y claves foráneas.
- **Estadísticas:** recuento de tablas, filas, columnas, índices y tamaño de las bases de datos.
- **Visor de registros:** navegación por los registros mediante paginación.
- **Inspector de datos:** consulta de valores extensos y visualización de registros en formato de fila o JSON.
- **API REST:** acceso a las funcionalidades mediante endpoints HTTP.
- **Persistencia:** almacenamiento de las bases de datos en un directorio del sistema anfitrión.
- **Contenedorización:** despliegue mediante Docker y Docker Compose.

## Tecnologías

- Python 3.11
- FastAPI
- Uvicorn
- SQLite
- HTML, CSS y JavaScript
- Docker Engine
- Docker Compose

## Requisitos

Para ejecutar la aplicación mediante Docker se necesita:

- Docker Engine.
- Docker Compose v2 o compatible con el comando `docker compose`.
- Un puerto disponible, por defecto el `8000`.

No es necesario instalar Python ni crear un entorno virtual para ejecutar la aplicación mediante Docker.

## Instalación y ejecución con Docker

### 1. Clonar el repositorio

Sustituye `<URL_DEL_REPOSITORIO>` por la dirección del repositorio Git:

```bash
git clone <URL_DEL_REPOSITORIO>
cd dbReader
```

### 2. Construir e iniciar la aplicación

```bash
sudo docker compose up -d --build
```

Docker construirá la imagen a partir del `Dockerfile`, instalará las dependencias e iniciará el servicio.

### 3. Acceder a la aplicación

Desde el mismo equipo:

- Aplicación web: http://localhost:8000
- Documentación interactiva de la API: http://localhost:8000/docs
- Documentación alternativa de la API: http://localhost:8000/redoc

Por defecto, el puerto se publica en las interfaces de red del equipo. Para utilizar la aplicación desde otros dispositivos de la red local, consulta la sección de acceso LAN.

### 4. Comprobar el servicio

```bash
sudo docker compose ps
sudo docker compose logs -f
```

Para salir de los logs, pulsa `Ctrl + C`. Esto no detiene el contenedor.

## Gestión del servicio

Ejecuta estos comandos desde el directorio que contiene `compose.yaml`.

| Operación | Comando |
|---|---|
| Iniciar el servicio | `sudo docker compose up -d` |
| Reconstruir e iniciar | `sudo docker compose up -d --build` |
| Detener el servicio | `sudo docker compose stop` |
| Volver a iniciarlo | `sudo docker compose start` |
| Consultar el estado | `sudo docker compose ps` |
| Consultar los logs | `sudo docker compose logs -f` |
| Detener y eliminar el contenedor | `sudo docker compose down` |

Los archivos de bases de datos se almacenan fuera del contenedor, por lo que detenerlo, reconstruirlo o eliminarlo mediante `docker compose down` no elimina el contenido de `data/`.

## Almacenamiento de bases de datos

Docker Compose monta el directorio local `./data` en `/app/data` dentro del contenedor.

```text
dbReader/
├── app/
├── data/
│   └── bases de datos SQLite
├── tests/
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

El directorio `data/` se utiliza para almacenar las bases de datos que descubre la aplicación y los archivos que se incorporan mediante la interfaz.

Por defecto, `data/` está excluido del control de versiones para evitar publicar accidentalmente datos privados o bases de datos de prueba.

## Configuración

La aplicación utiliza la variable de entorno `DBREADER_DATABASE_DIRECTORY` para determinar el directorio de almacenamiento.

En Docker Compose se configura así:

```yaml
environment:
  DBREADER_DATABASE_DIRECTORY: /app/data
```

Si se modifica la ruta de almacenamiento, debe ajustarse también el volumen de Docker para que el directorio configurado corresponda con el almacenamiento persistente.

El puerto publicado se configura en `compose.yaml`. Para cambiarlo, modifica el puerto del anfitrión manteniendo el puerto interno `8000`.

## Acceso desde la red local

Para permitir el acceso desde otros dispositivos de la LAN, el servicio puede publicarse en el puerto `8000` del equipo anfitrión.

Desde otro dispositivo conectado a la misma red, accede a:

```text
http://IP_LOCAL_DEL_SERVIDOR:8000
```

La dirección IP debe corresponder al equipo donde se ejecuta Docker.

Si el acceso no funciona, comprueba el firewall del anfitrión y las reglas de red. No es necesario configurar una redirección de puertos en el router para el uso exclusivamente local.

**Seguridad:** la aplicación debe utilizarse únicamente en una red de confianza mientras no disponga de autenticación y autorización. Un dispositivo con acceso al servicio podría consultar o cargar bases de datos. No publiques el puerto directamente en Internet sin implementar y revisar previamente las medidas de seguridad necesarias.

## Desarrollo local

Para desarrollar sin Docker, crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Inicia el servidor de desarrollo:

```bash
python -m uvicorn app.main:app --reload
```

El servidor estará disponible en http://127.0.0.1:8000.

El entorno virtual `.venv/` es local y no debe incorporarse al repositorio.

## Pruebas

Las pruebas automatizadas utilizan pytest.

Instala las dependencias del proyecto y ejecuta:

```bash
python -m pytest -v
```

La suite incluye pruebas de la API, descubrimiento de bases de datos, validación de archivos SQLite, estadísticas y lectura paginada de registros.

## Estructura del proyecto

```text
dbReader/
├── app/
│   ├── adapters/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── static/
│       ├── css/
│       ├── js/
│       └── index.html
├── tests/
├── data/                 # Datos locales, excluidos de Git
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

## Limitaciones actuales

- El motor de base de datos soportado es SQLite.
- La aplicación no debe considerarse un servicio multiusuario seguro mientras no disponga de mecanismos de autenticación y autorización.
- El acceso a los datos depende de los permisos del sistema de archivos y de la configuración del almacenamiento.
- Las vistas SQLite pueden inspeccionarse a nivel de esquema, pero la visualización de sus registros no está soportada actualmente por el endpoint de lectura de tablas.

## Contribuciones

Las contribuciones, propuestas de mejoras y notificaciones de errores son bienvenidas. Antes de enviar cambios, ejecuta la suite de pruebas y evita incluir datos privados, credenciales o bases de datos reales.

## Licencia

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.