# Hotel Tumán — Sistema de Gestión Hotelera

Sistema web completo para la gestión de un hotel boutique, desarrollado con Django 4.2, PostgreSQL y Docker.

---

## Tecnologías

- **Backend:** Python 3.11 + Django 4.2.13
- **Base de datos:** PostgreSQL 15
- **ORM:** Django ORM con Service Layer y Soft Delete
- **API REST:** Django REST Framework + drf-spectacular (Swagger)
- **Frontend:** Django Templates + CSS propio (sin Bootstrap)
- **Imágenes:** Cloudinary
- **Consulta DNI:** RENIEC via api.factiliza.com
- **Contenedores:** Docker + Docker Compose

---

## Requisitos

- Docker Desktop
- Git

---

## ⚙️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/fustamantelennart-lgtm/Sitema_Hotel.git
cd Sitema_Hotel
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

### 3. Levantar con Docker
```bash
docker compose up -d
```

### 4. Aplicar migraciones
```bash
docker exec -it hotel_web python manage.py migrate
```

### 5. Crear superusuario
```bash
docker exec -it hotel_web python manage.py createsuperuser
```

### 6. Cargar datos de prueba
```bash
docker exec -it hotel_web python manage.py loaddata fixtures/initial_data.json
```

### 7. Acceder al sistema
- **Portal web:** http://localhost:8000/web/
- **Panel staff:** http://localhost:8000/
- **API Swagger:** http://localhost:8000/api/v1/docs/
- **Django Admin:** http://localhost:8000/admin/

---

## Credenciales de prueba

### Staff
| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| maicol | admin123 | Administrador |
| carlos | recep123 | Recepcionista |
| lennart | hk123456 | Housekeeping |

### Cliente portal web
| Email | Contraseña |
|-------|-----------|
| fustamantelennart@gmail.com | Lefuso123 |

---

## Estructura del proyecto
hotel_v2/
├── apps/
│   ├── usuarios/        # Auth, roles, registro cliente
│   ├── recepcion/       # Dashboard, habitaciones
│   ├── reservas/        # Reservas, checkin, checkout, folio
│   ├── housekeeping/    # Tareas, incidentes
│   ├── gerencia/        # Reportes, dashboard KPIs
│   ├── publica/         # Portal web cliente
│   └── api/             # API REST
├── utils/
│   └── models.py        # ModeloBase con soft delete
├── static/
│   ├── css/
│   └── js/
├── templates/
├── docker-compose.yml
├── requirements.txt
└── .env.example
---

## Arquitectura

El sistema implementa **Service Layer** con separación de responsabilidades:
Request → View → Service → ORM → Base de datos
↓
Exceptions (errores de dominio)
Cada módulo tiene:
- `models.py` — modelos que heredan de `ModeloBase`
- `services.py` — lógica de negocio
- `exceptions.py` — errores específicos del dominio
- `views.py` — solo coordinación, sin lógica de negocio

---

## API REST

Documentación interactiva disponible en `/api/v1/docs/`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/hoteles/` | GET | Lista hoteles |
| `/api/v1/habitaciones/` | GET | Lista habitaciones |
| `/api/v1/habitaciones/disponibles/` | GET | Habitaciones disponibles por fecha |
| `/api/v1/huespedes/` | GET, POST | Gestión huéspedes |
| `/api/v1/reservas/` | GET, POST | Gestión reservas |
| `/api/v1/token/` | POST | Obtener token auth |

---

## Tests

```bash
docker exec -it hotel_web coverage run --source=apps manage.py test apps --verbosity=2
docker exec -it hotel_web coverage report --skip-empty
```

Cobertura actual: **66%** — 39 tests unitarios e integración

---

## Módulos del sistema

### Operación (Recepcionista/Admin)
- **Mapa de habitaciones** — vista visual por piso con estados en colores
- **Gestión habitaciones** — cambiar estados, agregar nuevas
- **Reservas** — panel con tabs (Llegadas/En Casa/Salidas)
- **Check-in** — asignación de habitación con verificación de documento
- **Folio** — cargos, pagos, checkout
- **Huéspedes** — historial de reservas por huésped

### Limpieza (Housekeeping)
- **Panel de tareas** — prioridades visuales, asignación por empleado
- **Historial** — tareas completadas filtradas por fecha
- **Incidentes** — reporte y resolución de incidentes por habitación

### Inteligencia (Admin)
- **Dashboard** — KPIs + gráficos Chart.js (línea, donut, barras)
- **Ocupación** — reporte mensual de noches vendidas e ingresos
- **Reportes** — filtro por período + exportación PDF y Excel
- **Usuarios** — gestión del personal del hotel

### Portal Cliente
- **Búsqueda** — disponibilidad en tiempo real por fechas
- **Reserva** — formulario multi-paso con autocomplete DNI RENIEC
- **Pago** — tarjeta, Yape o transferencia bancaria
- **Perfil** — historial de reservas y cancelación

---

## Variables de entorno

Ver `.env.example` para la lista completa de variables requeridas.
