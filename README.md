# Elegance Nails SaaS Platform

Una plataforma multi-tenant moderna para salones de uñas y belleza con directorio de negocios interactivo y sistema de reservas.

## Características Principales

### 🗺️ Directorio de Negocios Interactivo
- Mapa interactivo powered by Mapbox
- Búsqueda y filtrado de salones por ubicación
- Marcadores agrupados (clustering)
- Información detallada de cada negocio
- Geocodificador integrado

### 💼 Sistema Multi-Tenant
- Soporte para múltiples negocios
- Gestión independiente por negocio
- Base de datos compartida con aislamiento de datos

### 📅 Sistema de Reservas
- Calendario de citas interactivo
- Gestión de servicios y empleados
- Notificaciones automáticas
- Sistema de pagos integrado

### 👥 Gestión de Usuarios
- Roles: Admin, Empleado, Cliente
- Autenticación segura con JWT
- Perfiles personalizables

## Tecnologías

- **Backend**: Flask + SQLAlchemy
- **Base de Datos**: MySQL
- **Frontend**: Bootstrap 5 + JavaScript
- **Mapas**: Mapbox GL JS
- **Autenticación**: Flask-Login + JWT

## Instalación

### Requisitos Previos
- Python 3.8+
- MySQL 8.0+
- Node.js (opcional, para assets)

### Configuración

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd nails
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
```
Editar `.env` con tus configuraciones:
- Credenciales de MySQL
- API Key de Mapbox
- Secret keys

5. **Configurar base de datos**
```bash
# Crear la base de datos MySQL
mysql -u root -p -e "CREATE DATABASE elegance_nails_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Ejecutar migraciones
flask db init
flask db migrate
flask db upgrade
```

6. **Ejecutar la aplicación**
```bash
python app.py
```

## Estructura del Proyecto

```
nails/
├── app/                    # Aplicación principal
│   ├── models/            # Modelos de base de datos
│   ├── routes/            # Rutas y endpoints
│   ├── static/            # Archivos estáticos
│   └── templates/         # Plantillas HTML
├── static/                # Assets estáticos globales
├── templates/             # Plantillas principales
├── instance/              # Configuración de instancia
├── .env                   # Variables de entorno
├── app.py                 # Punto de entrada
├── config.py              # Configuración
└── requirements.txt       # Dependencias
```

## API Endpoints

### Autenticación
- `POST /api/auth/login` - Login de usuario

### Directorio de Negocios
- `GET /api/businesses/search` - Buscar negocios
- `GET /api/businesses/<id>` - Detalle de negocio
- `GET /api/businesses/types` - Tipos de negocio
- `GET /api/config/mapbox` - Configuración de Mapbox

### Citas
- `GET /api/appointments` - Obtener citas
- `POST /api/appointments` - Crear cita
- `PUT /api/appointments/<id>/status` - Actualizar estado

### Servicios
- `GET /api/services` - Obtener servicios
- `GET /api/available_slots` - Horarios disponibles

## Rutas Web

- `/` - Página principal
- `/directory` - Directorio de negocios con mapa
- `/login` - Inicio de sesión
- `/register` - Registro de usuario
- `/dashboard` - Panel de control
- `/appointments` - Gestión de citas
- `/services` - Gestión de servicios

## Configuración de Mapbox

1. Obtener API key en [Mapbox](https://www.mapbox.com)
2. Agregar la key en `.env`:
```
MAPBOX_ACCESS_TOKEN=tu_api_key_aqui
```

## Base de Datos

### Tablas Principales
- `users` - Usuarios del sistema
- `businesses` - Negocios registrados
- `appointments` - Citas programadas
- `services` - Servicios ofrecidos
- `payments` - Pagos realizados

### Datos de Ejemplo
El sistema incluye datos de ejemplo para México con varios salones en diferentes ciudades.

## Deployment

### Desarrollo
```bash
export FLASK_ENV=development
python app.py
```

### Producción
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/nueva-caracteristica`)
3. Commit los cambios (`git commit -am 'Agregar nueva característica'`)
4. Push al branch (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.

## Soporte

Para soporte técnico o preguntas, contactar a través de los issues del repositorio.

---

### Versión
v2.0.0 - Plataforma SaaS Multi-Tenant con Mapbox Integration
